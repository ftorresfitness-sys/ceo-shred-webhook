import os
import json
import threading
import stripe
import requests
import logging
from flask import Flask, request, jsonify

from followup_scheduler import start_scheduler, run_cycle, process_contact, get_contact_detail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# ── Follow-up scheduler endpoints ─────────────────────────────────────────────

@app.route("/followup/status", methods=["GET"])
def followup_status():
    """
    Returns the current scheduler configuration.
    Use this to confirm the scheduler is running and check its settings.
    """
    enabled = os.environ.get("FOLLOWUP_ENABLED", "false").lower() == "true"
    return jsonify({
        "followup_scheduler": "enabled" if enabled else "disabled",
        "scorecard_list_id": int(os.environ.get("SCORECARD_LIST_ID", "44")),
        "poll_interval_hours": float(os.environ.get("FOLLOWUP_POLL_HOURS", "1")),
        "from_email": os.environ.get("FOLLOWUP_FROM_EMAIL", "francisco@theceoshred.com"),
        "schedule": {"email_a_days": 1, "email_b_days": 3, "email_c_days": 6},
        "note": "Set FOLLOWUP_ENABLED=true in Render env vars to activate.",
    }), 200


@app.route("/followup/test", methods=["POST"])
def followup_test():
    """
    Manually trigger the follow-up logic for a specific email address.
    Used for testing before going live.

    POST body (JSON):
      { "email": "test@example.com", "force_email": "A" }

    If force_email is set to "A", "B", or "C", that email is sent immediately
    regardless of how long ago the contact was added to list 44.
    Without force_email, normal day-elapsed logic applies.

    The contact must already exist in Brevo with list 44 membership.
    """
    from followup_scheduler import (
        get_contact_detail, send_transactional_email, mark_sent, get_sent_flags,
        SCORECARD_LIST_ID
    )
    from email_templates import (
        email_a_subject, email_a_html, email_a_text,
        email_b_subject, email_b_html, email_b_text,
        email_c_subject, email_c_html, email_c_text,
    )

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    force_email = (data.get("force_email") or "").strip().upper()

    if not email:
        return jsonify({"error": "email is required"}), 400

    detail = get_contact_detail(email)
    if not detail:
        return jsonify({"error": f"Contact {email} not found in Brevo"}), 404

    attrs = detail.get("attributes") or {}
    firstname = attrs.get("FIRSTNAME") or "there"
    weakest   = attrs.get("SCORECARD_WEAKEST") or "hormonal health"
    total     = attrs.get("SCORECARD_TOTAL") or "unknown"
    sent_flags = get_sent_flags(detail)

    if force_email in ("A", "B", "C"):
        # Force-send the specified email regardless of timing
        try:
            if force_email == "A":
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=email_a_subject(firstname),
                    html_content=email_a_html(firstname, weakest),
                    text_content=email_a_text(firstname, weakest),
                )
            elif force_email == "B":
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=email_b_subject(firstname),
                    html_content=email_b_html(firstname, weakest),
                    text_content=email_b_text(firstname, weakest),
                )
            else:  # C
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=email_c_subject(firstname),
                    html_content=email_c_html(firstname, total),
                    text_content=email_c_text(firstname, total),
                )
            if ok:
                mark_sent(email, force_email, sent_flags)
                return jsonify({
                    "status": "sent",
                    "email": email,
                    "email_type": force_email,
                    "tokens": {"FIRSTNAME": firstname, "SCORECARD_WEAKEST": weakest, "SCORECARD_TOTAL": total},
                    "note": "Check your inbox. FOLLOWUP_SENT attribute updated in Brevo."
                }), 200
            else:
                return jsonify({"error": "Brevo API returned failure — check server logs"}), 500
        except Exception as e:
            logger.exception(f"Force-send Email {force_email} failed for {email}: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        # Normal day-elapsed logic
        try:
            process_contact({"email": email})
            return jsonify({"status": "processed", "email": email,
                            "note": "Check your inbox. Emails are only sent for due windows based on list-add date."}), 200
        except Exception as e:
            logger.exception(f"Test processing failed for {email}: {e}")
            return jsonify({"error": str(e)}), 500


@app.route("/followup/run-now", methods=["POST"])
def followup_run_now():
    """
    Manually trigger a full scheduler cycle across all list-44 contacts.
    Runs in a background thread so the request returns immediately
    (avoids 30s timeout on Render free plan with large contact lists).
    Protected by a simple shared secret via X-Admin-Key header.
    """
    admin_key = os.environ.get("ADMIN_KEY", "")
    if admin_key and request.headers.get("X-Admin-Key", "") != admin_key:
        return jsonify({"error": "Unauthorized"}), 401

    def _run():
        try:
            run_cycle()
        except Exception as e:
            logger.exception(f"Background run-now failed: {e}")

    t = threading.Thread(target=_run, name="manual-run-now", daemon=True)
    t.start()
    return jsonify({"status": "cycle started in background — check logs for results"}), 202


# ── Standard endpoints ─────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "CEO Shred Stripe Webhook + Followup Scheduler"}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "CEO Shred Webhook Handler + Scorecard Follow-Up Scheduler",
        "version": "2.0.0",
        "endpoints": {
            "POST /webhook/stripe":   "Stripe webhook receiver",
            "GET  /health":           "Health check",
            "GET  /followup/status":  "Scheduler config and status",
            "POST /followup/test":    "Test follow-up for a specific email",
            "POST /followup/run-now": "Trigger a full scheduler cycle (admin)",
        }
    }), 200


# ── Startup ────────────────────────────────────────────────────────────────────

# Start the background follow-up scheduler when the app boots.
# It only activates if FOLLOWUP_ENABLED=true is set in the environment.
start_scheduler()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
