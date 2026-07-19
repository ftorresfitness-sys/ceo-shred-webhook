"""
CEO Shred — Performance Kitchen backup delivery
Added 2026-07-19.

Purpose:
  The kitchen.theceoshred.com thank-you pages already deliver the Drive links
  in-browser (DO NOT TOUCH). This module adds a BACKUP delivery path:
  when any Kitchen payment link completes checkout, we
    1. send the buyer a transactional email with their matching Drive folder link
    2. upsert the buyer to Brevo with attribute KITCHEN_BUYER = single | full | vault

Detection:
  Primary:  checkout session payment_link ID -> plan
  Fallback: line-item product name keywords -> plan
  Non-kitchen purchases return None and are ignored by this module.

No thank-you pages, Stripe confirmation URLs, or Drive links are modified.
"""

import logging

import requests
import stripe

logger = logging.getLogger("kitchen_delivery")

BREVO_BASE = "https://api.brevo.com/v3"

# ── Plan definitions (Drive links verified live 2026-07-19 — do not change) ──

KITCHEN_PLANS = {
    "single": {
        "label": "The CEO Shred — Single Collection (Breakfast)",
        "drive_url": "https://drive.google.com/drive/folders/1gMevu6zfpYrbuEKRSLeERdssNQYgIrM3",
    },
    "full": {
        "label": "The CEO Shred — Full Performance Kitchen",
        "drive_url": "https://drive.google.com/drive/folders/1cQRraQ6LJ3kFFZj-uWHuDW03ylae4xN4",
    },
    "vault": {
        "label": "The CEO Shred — The Complete Nutrition Vault",
        "drive_url": "https://drive.google.com/drive/folders/17T4miYIxDpSWQgtOW7GkA1FmvTJ5XAPf",
    },
}

# Payment link ID -> plan (all active Kitchen payment links as of 2026-07-19)
PAYMENT_LINK_PLAN_MAP = {
    "plink_1TkxqxD9RVPNgBXLif3YuOm5": "single",  # $27 (Jun 22, older)
    "plink_1Tkxv9D9RVPNgBXL8qqrH1lb": "single",  # $27 (Jun 22, current)
    "plink_1Tkxz8D9RVPNgBXLF2uTQKE2": "full",    # $67 (Jun 22)
    "plink_1ToLpBD9RVPNgBXLdR6XYjQU": "full",    # $47 (Jul 1, current price)
    "plink_1Tky1kD9RVPNgBXLvuQrIoCd": "vault",   # $97 (Jun 22)
}

# Product-name keyword fallback (checked in order — vault first so
# "nutrition vault" never falls through to "kitchen")
NAME_KEYWORD_PLAN = [
    ("nutrition vault", "vault"),
    ("single collection", "single"),
    ("full performance kitchen", "full"),
]


def resolve_kitchen_plan(session: dict) -> str | None:
    """Return 'single' | 'full' | 'vault' for Kitchen purchases, else None."""
    # 1. Payment link ID (deterministic)
    plink = session.get("payment_link")
    if plink:
        plan = PAYMENT_LINK_PLAN_MAP.get(plink)
        if plan:
            return plan

    # 2. Fallback: line-item product names
    try:
        line_items = stripe.checkout.Session.list_line_items(session["id"], limit=5)
        for item in line_items.auto_paging_iter():
            desc = (item.get("description") or "").lower()
            for keyword, plan in NAME_KEYWORD_PLAN:
                if keyword in desc:
                    return plan
            price = item.get("price") or {}
            product_id = price.get("product")
            if product_id:
                product = stripe.Product.retrieve(product_id)
                name = (product.get("name") or "").lower()
                for keyword, plan in NAME_KEYWORD_PLAN:
                    if keyword in name:
                        return plan
    except Exception as e:
        logger.warning(f"Kitchen plan fallback lookup failed: {e}")

    return None


# ── Brevo logging ─────────────────────────────────────────────────────────────

def log_kitchen_buyer(email: str, first_name: str, plan: str, brevo_headers: dict) -> dict:
    """Upsert contact in Brevo with KITCHEN_BUYER attribute."""
    attributes = {"KITCHEN_BUYER": plan}
    if first_name:
        attributes["FIRSTNAME"] = first_name

    r = requests.post(
        f"{BREVO_BASE}/contacts",
        headers=brevo_headers,
        json={"email": email, "updateEnabled": True, "attributes": attributes},
        timeout=10,
    )
    if r.status_code in (200, 201, 204):
        return {"success": True, "email": email, "kitchen_buyer": plan}

    # Contact exists but updateEnabled didn't apply — force attribute update
    if r.status_code == 400:
        r2 = requests.put(
            f"{BREVO_BASE}/contacts/{requests.utils.quote(email, safe='')}",
            headers=brevo_headers,
            json={"attributes": attributes},
            timeout=10,
        )
        if r2.status_code in (200, 201, 204):
            return {"success": True, "email": email, "kitchen_buyer": plan, "note": "existing contact updated"}
        return {"success": False, "error": r2.text[:200], "status": r2.status_code}

    return {"success": False, "error": r.text[:200], "status": r.status_code}


# ── Backup delivery email ─────────────────────────────────────────────────────

def kitchen_email_subject(plan: str) -> str:
    return f"Your access link — {KITCHEN_PLANS[plan]['label']}"


def kitchen_email_html(first_name: str, plan: str) -> str:
    p = KITCHEN_PLANS[plan]
    name = first_name or "there"
    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background-color:#f5f5f4;font-family:Georgia,'Times New Roman',serif;color:#1c1917;">
  <div style="max-width:560px;margin:0 auto;padding:40px 24px;">
    <div style="background:#ffffff;border:1px solid #e7e5e4;padding:40px 36px;">
      <p style="font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#a8a29e;margin:0 0 24px;">The CEO Shred</p>
      <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">{name},</p>
      <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">Your order is confirmed. Here is your permanent access link to <strong>{p['label']}</strong>:</p>
      <p style="margin:28px 0;">
        <a href="{p['drive_url']}" style="display:inline-block;background:#1c1917;color:#ffffff;text-decoration:none;padding:14px 28px;font-size:15px;letter-spacing:0.5px;">Open your files</a>
      </p>
      <p style="font-size:14px;line-height:1.6;color:#57534e;margin:0 0 16px;">Bookmark this email. The link does not expire and always points to the latest version of your files.</p>
      <p style="font-size:14px;line-height:1.6;color:#57534e;margin:0 0 16px;">If the button doesn't work, copy this address into your browser:<br>
      <a href="{p['drive_url']}" style="color:#1c1917;">{p['drive_url']}</a></p>
      <p style="font-size:16px;line-height:1.6;margin:24px 0 0;">Francisco<br><span style="font-size:13px;color:#a8a29e;">The CEO Shred</span></p>
    </div>
    <p style="font-size:12px;color:#a8a29e;text-align:center;margin:20px 0 0;">You're receiving this because you purchased {p['label']}.</p>
  </div>
</body>
</html>"""


def kitchen_email_text(first_name: str, plan: str) -> str:
    p = KITCHEN_PLANS[plan]
    name = first_name or "there"
    return (
        f"{name},\n\n"
        f"Your order is confirmed. Here is your permanent access link to {p['label']}:\n\n"
        f"{p['drive_url']}\n\n"
        "Bookmark this email. The link does not expire and always points to the latest version of your files.\n\n"
        "Francisco\nThe CEO Shred\n"
    )


def deliver_kitchen_purchase(
    email: str,
    first_name: str,
    plan: str,
    brevo_headers: dict,
    send_email_fn,
) -> dict:
    """
    Full backup delivery: log KITCHEN_BUYER to Brevo + send the Drive-link email.
    `send_email_fn` = followup_scheduler.send_transactional_email
    """
    result = {"plan": plan}

    try:
        result["brevo"] = log_kitchen_buyer(email, first_name, plan, brevo_headers)
    except Exception as e:
        logger.exception(f"KITCHEN_BUYER logging failed for {email}: {e}")
        result["brevo"] = {"success": False, "error": str(e)}

    try:
        ok = send_email_fn(
            to_email=email,
            to_name=first_name or email,
            subject=kitchen_email_subject(plan),
            html_content=kitchen_email_html(first_name, plan),
            text_content=kitchen_email_text(first_name, plan),
        )
        result["email_sent"] = bool(ok)
    except Exception as e:
        logger.exception(f"Kitchen delivery email failed for {email}: {e}")
        result["email_sent"] = False
        result["email_error"] = str(e)

    logger.info(f"Kitchen backup delivery for {email}: {result}")
    return result
