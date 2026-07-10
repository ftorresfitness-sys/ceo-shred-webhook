"""
CEO Shred — Scorecard Follow-Up Scheduler
Runs as a background thread inside the Flask/Render service.

Logic:
  Every hour, fetch all contacts in Brevo list 44.
  For each contact, check how many days have elapsed since they were added to the list.
  Send Email A at +1d, Email B at +3d, Email C at +6d.
  Track sent state via the contact's FOLLOWUP_SENT attribute (comma-separated: "A", "A,B", etc.)
  to prevent duplicate sends across poll cycles.

Environment variables consumed:
  BREVO_API_KEY         — Brevo API key (same as the rest of the service)
  FOLLOWUP_ENABLED      — set to "true" to activate (default: "false" — safe off by default)
  FOLLOWUP_POLL_HOURS   — poll interval in hours (default: 1)
  FOLLOWUP_FROM_EMAIL   — sender email (default: francisco@theceoshred.com)
  FOLLOWUP_FROM_NAME    — sender name  (default: Francisco Torres)
  SCORECARD_LIST_ID     — Brevo list ID to monitor (default: 44)
"""

import os
import time
import logging
import threading
from datetime import datetime, timezone

import requests

from email_templates import (
    EMAIL_A_SUBJECT, email_a_html, email_a_text,
    EMAIL_B_SUBJECT, email_b_html, email_b_text,
    email_c_subject, email_c_html, email_c_text,
)

logger = logging.getLogger("followup_scheduler")

# ── Config ────────────────────────────────────────────────────────────────────

BREVO_API_KEY      = os.environ.get("BREVO_API_KEY", "")
FOLLOWUP_ENABLED   = os.environ.get("FOLLOWUP_ENABLED", "false").lower() == "true"
POLL_HOURS         = float(os.environ.get("FOLLOWUP_POLL_HOURS", "1"))
FROM_EMAIL         = os.environ.get("FOLLOWUP_FROM_EMAIL", "francisco@theceoshred.com")
FROM_NAME          = os.environ.get("FOLLOWUP_FROM_NAME", "Francisco Torres")
SCORECARD_LIST_ID  = int(os.environ.get("SCORECARD_LIST_ID", "44"))

BREVO_BASE         = "https://api.brevo.com/v3"

# Days after list-add to send each email
SCHEDULE = {
    "A": 1,
    "B": 3,
    "C": 6,
}


def _headers() -> dict:
    return {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ── Brevo helpers ─────────────────────────────────────────────────────────────

def get_list_contacts(list_id: int) -> list[dict]:
    """
    Fetch all contacts in a Brevo list, paging through results.
    Returns list of contact dicts with email + attributes.
    """
    contacts = []
    offset = 0
    limit = 500

    while True:
        url = f"{BREVO_BASE}/contacts"
        params = {
            "listId": list_id,
            "limit": limit,
            "offset": offset,
            "sort": "asc",
        }
        r = requests.get(url, headers=_headers(), params=params, timeout=15)
        if r.status_code != 200:
            logger.error(f"Failed to fetch list {list_id} contacts: {r.status_code} {r.text[:200]}")
            break

        data = r.json()
        batch = data.get("contacts", [])
        contacts.extend(batch)

        if len(batch) < limit:
            break
        offset += limit

    return contacts


def get_contact_detail(email: str) -> dict | None:
    """Fetch a single contact's full attribute set including list membership dates."""
    url = f"{BREVO_BASE}/contacts/{requests.utils.quote(email, safe='')}"
    r = requests.get(url, headers=_headers(), timeout=10)
    if r.status_code == 200:
        return r.json()
    logger.warning(f"Could not fetch contact detail for {email}: {r.status_code}")
    return None


def get_list_added_date(contact_detail: dict, list_id: int) -> datetime | None:
    """
    Extract the date a contact was added to a specific list.
    Brevo returns listIds as a list of ints; the add-date lives in
    contact_detail['listUnsubscribedDate'] or we fall back to 'createdAt'.
    The most reliable field is contact_detail['createdAt'] when the contact
    was created by the scorecard submission, but for contacts that pre-existed
    we use the modifiedAt as a conservative proxy.
    
    Brevo does not expose per-list add timestamps in the contacts API directly.
    We use the contact's 'createdAt' as the list-44 add time when list 44 is
    in their listIds, which is accurate for new scorecard leads (they are created
    and added to list 44 simultaneously). For existing contacts re-added to list 44,
    we use 'modifiedAt'.
    """
    lists = contact_detail.get("listIds", [])
    if list_id not in lists:
        return None

    # Prefer createdAt (accurate for new scorecard leads)
    raw = contact_detail.get("createdAt") or contact_detail.get("modifiedAt")
    if not raw:
        return None

    try:
        # Brevo returns ISO 8601 with Z suffix
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def days_since(dt: datetime) -> float:
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() / 86400


def get_sent_flags(contact_detail: dict) -> set[str]:
    """Return set of email keys already sent, e.g. {'A', 'B'}."""
    raw = (contact_detail.get("attributes") or {}).get("FOLLOWUP_SENT", "") or ""
    return set(x.strip() for x in raw.split(",") if x.strip())


def mark_sent(email: str, key: str, current_flags: set[str]) -> bool:
    """Update FOLLOWUP_SENT attribute on the contact."""
    new_flags = current_flags | {key}
    value = ",".join(sorted(new_flags))
    url = f"{BREVO_BASE}/contacts/{requests.utils.quote(email, safe='')}"
    payload = {"attributes": {"FOLLOWUP_SENT": value}}
    r = requests.put(url, headers=_headers(), json=payload, timeout=10)
    if r.status_code in (200, 201, 204):
        return True
    logger.error(f"Failed to mark FOLLOWUP_SENT={value} for {email}: {r.status_code} {r.text[:200]}")
    return False


def send_transactional_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """Send a transactional email via Brevo POST /v3/smtp/email."""
    url = f"{BREVO_BASE}/smtp/email"
    payload = {
        "sender": {"name": FROM_NAME, "email": FROM_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
        "replyTo": {"email": FROM_EMAIL, "name": FROM_NAME},
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=15)
    if r.status_code in (200, 201):
        logger.info(f"Sent email '{subject}' to {to_email}")
        return True
    logger.error(f"Failed to send '{subject}' to {to_email}: {r.status_code} {r.text[:300]}")
    return False


# ── Core processing ───────────────────────────────────────────────────────────

def process_contact(contact: dict) -> None:
    """
    Evaluate a single contact and send any due follow-up emails.
    """
    email = contact.get("email", "")
    if not email:
        return

    detail = get_contact_detail(email)
    if not detail:
        return

    attrs = detail.get("attributes") or {}
    firstname = attrs.get("FIRSTNAME") or email.split("@")[0].capitalize()
    weakest   = attrs.get("SCORECARD_WEAKEST") or "your hormone profile"
    total_raw = attrs.get("SCORECARD_TOTAL")
    total     = str(total_raw) if total_raw is not None else "your score"

    added_dt = get_list_added_date(detail, SCORECARD_LIST_ID)
    if not added_dt:
        logger.debug(f"No list-add date for {email}, skipping.")
        return

    elapsed_days = days_since(added_dt)
    sent_flags   = get_sent_flags(detail)

    logger.debug(
        f"{email}: elapsed={elapsed_days:.2f}d, sent={sent_flags}, "
        f"weakest={weakest}, total={total}"
    )

    # Email A — +1 day
    if "A" not in sent_flags and elapsed_days >= SCHEDULE["A"]:
        ok = send_transactional_email(
            to_email=email,
            to_name=firstname,
            subject=EMAIL_A_SUBJECT,
            html_content=email_a_html(firstname, weakest),
            text_content=email_a_text(firstname, weakest),
        )
        if ok:
            mark_sent(email, "A", sent_flags)
            sent_flags.add("A")

    # Email B — +3 days
    if "B" not in sent_flags and elapsed_days >= SCHEDULE["B"]:
        ok = send_transactional_email(
            to_email=email,
            to_name=firstname,
            subject=EMAIL_B_SUBJECT,
            html_content=email_b_html(firstname, weakest),
            text_content=email_b_text(firstname, weakest),
        )
        if ok:
            mark_sent(email, "B", sent_flags)
            sent_flags.add("B")

    # Email C — +6 days
    if "C" not in sent_flags and elapsed_days >= SCHEDULE["C"]:
        ok = send_transactional_email(
            to_email=email,
            to_name=firstname,
            subject=email_c_subject(firstname),
            html_content=email_c_html(firstname, total),
            text_content=email_c_text(firstname, total),
        )
        if ok:
            mark_sent(email, "C", sent_flags)
            sent_flags.add("C")


def run_cycle() -> None:
    """Single poll cycle: fetch list 44 contacts and process each one."""
    logger.info(f"Followup scheduler cycle starting — list {SCORECARD_LIST_ID}")
    try:
        contacts = get_list_contacts(SCORECARD_LIST_ID)
        logger.info(f"Found {len(contacts)} contacts in list {SCORECARD_LIST_ID}")
        for contact in contacts:
            try:
                process_contact(contact)
            except Exception as e:
                logger.exception(f"Error processing contact {contact.get('email')}: {e}")
    except Exception as e:
        logger.exception(f"Followup scheduler cycle failed: {e}")
    logger.info("Followup scheduler cycle complete.")


def _scheduler_loop() -> None:
    interval_seconds = POLL_HOURS * 3600
    # Small initial delay so the web server starts cleanly first
    time.sleep(30)
    while True:
        run_cycle()
        time.sleep(interval_seconds)


def start_scheduler() -> None:
    """Start the background scheduler thread. Call once at app startup."""
    if not FOLLOWUP_ENABLED:
        logger.info("Followup scheduler is DISABLED (set FOLLOWUP_ENABLED=true to activate).")
        return
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not set — followup scheduler will not start.")
        return

    t = threading.Thread(target=_scheduler_loop, name="followup-scheduler", daemon=True)
    t.start()
    logger.info(
        f"Followup scheduler started — polling list {SCORECARD_LIST_ID} "
        f"every {POLL_HOURS}h."
    )
