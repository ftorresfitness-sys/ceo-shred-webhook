import os
import json
import stripe
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Config (all from environment variables — no hardcoded secrets) ────────────
STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "sk_live_REPLACE_ME")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_REPLACE_ME")
BREVO_API_KEY         = os.environ.get("BREVO_API_KEY", "")

stripe.api_key = STRIPE_SECRET_KEY

# Product → Brevo list ID mapping
# Key = lowercase product identifier found in Stripe metadata or product name
PRODUCT_LIST_MAP = {
    "testosterone": 38,
    "cortisol":     39,
    "insulin":      40,
    "stack":        41,
    "vault":        42,
}

BREVO_HEADERS = {
    "api-key": BREVO_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def add_contact_to_list(email: str, first_name: str, list_id: int) -> dict:
    """
    Upsert contact in Brevo and add to the specified list.
    Returns a dict with success/error info.
    """
    # 1. Upsert contact
    upsert_url = "https://api.brevo.com/v3/contacts"
    payload = {
        "email": email,
        "updateEnabled": True,
        "attributes": {"FIRSTNAME": first_name} if first_name else {},
        "listIds": [list_id],
    }
    r = requests.post(upsert_url, headers=BREVO_HEADERS, json=payload, timeout=10)
    if r.status_code in (200, 201, 204):
        return {"success": True, "list_id": list_id, "email": email}
    # If contact already exists (409), add to list explicitly
    if r.status_code == 400 and "Contact already exist" in r.text:
        add_url = f"https://api.brevo.com/v3/contacts/lists/{list_id}/contacts/add"
        r2 = requests.post(add_url, headers=BREVO_HEADERS,
                           json={"emails": [email]}, timeout=10)
        if r2.status_code in (200, 201, 204):
            return {"success": True, "list_id": list_id, "email": email, "note": "existing contact added to list"}
        return {"success": False, "error": r2.text, "status": r2.status_code}
    return {"success": False, "error": r.text, "status": r.status_code}


def resolve_list_id(session: dict) -> int | None:
    """
    Determine which Brevo list to add the buyer to.
    Checks (in order):
      1. session.metadata.product
      2. session.metadata.protocol
      3. line_items product name / metadata
    Returns list_id or None if unknown.
    """
    meta = session.get("metadata") or {}

    # Direct metadata keys
    for key in ("product", "protocol", "item", "type"):
        val = (meta.get(key) or "").lower()
        for keyword, lid in PRODUCT_LIST_MAP.items():
            if keyword in val:
                return lid

    # Fall back to line item product name / metadata via Stripe API
    try:
        line_items = stripe.checkout.Session.list_line_items(
            session["id"], limit=5
        )
        for item in line_items.auto_paging_iter():
            price = item.get("price") or {}
            product_id = price.get("product")
            if product_id:
                product = stripe.Product.retrieve(product_id)
                name = (product.get("name") or "").lower()
                pmeta = product.get("metadata") or {}
                # Check product name
                for keyword, lid in PRODUCT_LIST_MAP.items():
                    if keyword in name:
                        return lid
                # Check product metadata
                for key in ("product", "protocol", "item", "type"):
                    val = (pmeta.get(key) or "").lower()
                    for keyword, lid in PRODUCT_LIST_MAP.items():
                        if keyword in val:
                            return lid
    except Exception as e:
        app.logger.warning(f"Could not retrieve line items: {e}")

    return None


@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload   = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        app.logger.error(f"Webhook signature verification failed: {e}")
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        app.logger.error(f"Webhook parse error: {e}")
        return jsonify({"error": str(e)}), 400

    # Only handle completed checkouts
    if event["type"] != "checkout.session.completed":
        return jsonify({"status": "ignored", "type": event["type"]}), 200

    session = event["data"]["object"]
    email      = (session.get("customer_details") or {}).get("email") or session.get("customer_email", "")
    first_name = ((session.get("customer_details") or {}).get("name") or "").split()[0]

    if not email:
        app.logger.warning("checkout.session.completed received with no email")
        return jsonify({"status": "no_email"}), 200

    list_id = resolve_list_id(session)
    if list_id is None:
        app.logger.warning(f"Could not resolve list for session {session['id']} — metadata: {session.get('metadata')}")
        return jsonify({"status": "unknown_product", "session_id": session["id"]}), 200

    result = add_contact_to_list(email, first_name, list_id)
    app.logger.info(f"Brevo add result: {result}")

    return jsonify({"status": "ok", "result": result}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "CEO Shred Stripe Webhook"}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "CEO Shred Stripe Webhook Handler",
        "version": "1.0.0",
        "endpoints": {
            "POST /webhook/stripe": "Stripe webhook receiver",
            "GET /health": "Health check"
        }
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
