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
    name_parts = ((session.get("customer_details") or {}).get("name") or "").split()
    first_name = name_parts[0] if name_parts else ""

    if not email:
        app.logger.warning("checkout.session.completed received with no email")
        return jsonify({"status": "no_email"}), 200

    # ── Performance Kitchen backup delivery (added 2026-07-19) ──────────────
    # Detect Kitchen purchases by payment link / product name, send the buyer
    # their Drive link by email, and log KITCHEN_BUYER to Brevo.
    # Non-kitchen purchases fall through to the protocol list logic unchanged.
    from kitchen_delivery import resolve_kitchen_plan, deliver_kitchen_purchase
    from followup_scheduler import send_transactional_email

    kitchen_plan = resolve_kitchen_plan(session)
    if kitchen_plan:
        kitchen_result = deliver_kitchen_purchase(
            email=email,
            first_name=first_name,
            plan=kitchen_plan,
            brevo_headers=BREVO_HEADERS,
            send_email_fn=send_transactional_email,
        )
        return jsonify({"status": "ok", "kitchen": kitchen_result}), 200

    list_id = resolve_list_id(session)
    if list_id is None:
        app.logger.warning(f"Could not resolve list for session {session['id']} — metadata: {session.get('metadata')}")
        return jsonify({"status": "unknown_product", "session_id": session["id"]}), 200

    result = add_contact_to_list(email, first_name, list_id)
    app.logger.info(f"Brevo add result: {result}")

    return jsonify({"status": "ok", "result": result}), 200


@app.route("/kitchen/test", methods=["POST"])
def kitchen_test():
    """
    Admin-protected test of the Kitchen backup delivery path.
    Sends the real delivery email and sets KITCHEN_BUYER in Brevo
    for the given address, without a Stripe purchase.

    POST body: { "email": "...", "first_name": "...", "plan": "single|full|vault" }
    Header:    X-Admin-Key: <ADMIN_KEY>
    """
    admin_key = os.environ.get("ADMIN_KEY", "")
    if admin_key and request.headers.get("X-Admin-Key", "") != admin_key:
        return jsonify({"error": "Unauthorized"}), 401

    from kitchen_delivery import KITCHEN_PLANS, deliver_kitchen_purchase
    from followup_scheduler import send_transactional_email

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    first_name = (data.get("first_name") or "").strip()
    plan = (data.get("plan") or "").strip().lower()

    if not email or plan not in KITCHEN_PLANS:
        return jsonify({"error": "email and plan (single|full|vault) are required"}), 400

    result = deliver_kitchen_purchase(
        email=email,
        first_name=first_name,
        plan=plan,
        brevo_headers=BREVO_HEADERS,
        send_email_fn=send_transactional_email,
    )
    return jsonify({"status": "ok", "kitchen": result}), 200


# ── Scorecard webhook — instant result email ─────────────────────────────────

@app.route("/webhook/scorecard", methods=["POST", "OPTIONS"])
def scorecard_webhook():
    """
    Receives scorecard submission from the Lovable frontend.
    1. Upserts contact into Brevo list 44 with scorecard attributes.
    2. Sends an instant transactional result email with score + guide link.

    Expected JSON body:
      first_name, email, phone (optional),
      T_score, I_score, C_score, composite_score,
      archetype, tier, archetype_tag, score_tag,
      submitted_at, source
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return resp

    from email_templates import (
        email_r_subject, email_r_html, email_r_text,
    )
    from followup_scheduler import send_transactional_email

    data = request.get_json(silent=True) or {}

    email      = (data.get("email") or "").strip().lower()
    first_name = (data.get("first_name") or "").strip()
    phone      = (data.get("phone") or None)
    t_score    = int(data.get("T_score") or 0)
    i_score    = int(data.get("I_score") or 0)
    c_score    = int(data.get("C_score") or 0)
    composite  = int(data.get("composite_score") or 0)
    archetype  = (data.get("archetype") or "Unknown").strip()
    tier       = (data.get("tier") or "functional").strip()
    submitted  = data.get("submitted_at") or ""

    if not email:
        return jsonify({"error": "email is required"}), 400

    # Determine weakest corner from scores
    scores = {"Testosterone": t_score, "Insulin": i_score, "Cortisol & Stress": c_score}
    weakest = min(scores, key=scores.get)

    SCORECARD_LIST_ID = int(os.environ.get("SCORECARD_LIST_ID", "44"))

    # 1. Upsert contact into Brevo list 44 with scorecard attributes
    upsert_url = "https://api.brevo.com/v3/contacts"
    contact_payload = {
        "email": email,
        "updateEnabled": True,
        "attributes": {
            "FIRSTNAME": first_name,
            "SCORECARD_TOTAL": composite,
            "SCORECARD_WEAKEST": weakest,
            "SCORECARD_ARCHETYPE": archetype,
            "SCORECARD_TIER": tier,
            "SCORECARD_T": t_score,
            "SCORECARD_I": i_score,
            "SCORECARD_C": c_score,
        },
        "listIds": [SCORECARD_LIST_ID],
    }
    if phone:
        contact_payload["attributes"]["SMS"] = phone

    try:
        r = requests.post(upsert_url, headers=BREVO_HEADERS, json=contact_payload, timeout=10)
        if r.status_code == 400 and "Contact already exist" in r.text:
            # Update attributes and add to list
            update_url = f"https://api.brevo.com/v3/contacts/{email}"
            requests.put(update_url, headers=BREVO_HEADERS,
                         json={"attributes": contact_payload["attributes"],
                               "listIds": [SCORECARD_LIST_ID]}, timeout=10)
        app.logger.info(f"Scorecard contact upserted: {email} (list {SCORECARD_LIST_ID})")
    except Exception as e:
        app.logger.error(f"Brevo upsert failed for {email}: {e}")
        # Don't block — still try to send the email

    # 2. Send instant result email
    try:
        # band = tier string from Lovable frontend; worst tier displays as "Red Zone"
        band = tier
        
        subject = email_r_subject(composite)
        html    = email_r_html(first_name or "there", composite, weakest, band)
        text    = email_r_text(first_name or "there", composite, weakest, band)
        ok = send_transactional_email(
            to_email=email,
            to_name=first_name or email,
            subject=subject,
            html_content=html,
            text_content=text,
        )
        if ok:
            app.logger.info(f"Instant result email sent to {email}")
        else:
            app.logger.error(f"Instant result email FAILED for {email}")
    except Exception as e:
        app.logger.error(f"Instant result email exception for {email}: {e}")
        ok = False

    resp = jsonify({
        "status": "ok",
        "email_sent": ok,
        "contact_list": SCORECARD_LIST_ID,
        "archetype": archetype,
        "weakest": weakest,
    })
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200


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
        EMAIL_A_SUBJECT, email_a_html, email_a_text,
        EMAIL_B_SUBJECT, email_b_html, email_b_text,
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

    band = attrs.get("SCORECARD_TIER") or "functional"

    if force_email in ("A", "B", "C"):
        # Force-send the specified email regardless of timing
        try:
            if force_email == "A":
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=EMAIL_A_SUBJECT,
                    html_content=email_a_html(firstname, weakest),
                    text_content=email_a_text(firstname, weakest),
                )
            elif force_email == "B":
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=EMAIL_B_SUBJECT,
                    html_content=email_b_html(firstname),
                    text_content=email_b_text(firstname),
                )
            else:  # C
                ok = send_transactional_email(
                    to_email=email, to_name=firstname,
                    subject=email_c_subject(firstname, band),
                    html_content=email_c_html(firstname, weakest, total, band),
                    text_content=email_c_text(firstname, weakest, total, band),
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
        "version": "2.1.0",
        "endpoints": {
            "POST /webhook/scorecard": "Scorecard submission — upserts contact + sends instant result email",
            "POST /webhook/stripe":   "Stripe webhook receiver (protocols → lists; Kitchen → backup Drive-link email + KITCHEN_BUYER)",
            "POST /kitchen/test":     "Test Kitchen backup delivery for an email+plan (admin)",
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
