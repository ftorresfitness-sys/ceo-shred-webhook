# CEO Shred — Stripe Webhook Handler + Scorecard Follow-Up Scheduler

Two functions in one service:

1. **Stripe Webhook Handler** — receives `checkout.session.completed` events and adds buyers to the correct Brevo delivery list.
2. **Scorecard Follow-Up Scheduler** — sends a 3-email sequence to contacts added to Brevo list 44 (Scorecard – Hormone Leads) at +1d / +3d / +6d.

---

## Stripe Webhook: Product → Brevo List Mapping

| Product | Brevo List ID |
|---------|--------------|
| Testosterone Protocol | 38 |
| Cortisol Reset Protocol | 39 |
| Insulin Resistance Protocol | 40 |
| Executive Endocrine Stack | 41 |
| Complete EOS Vault | 42 |

---

## Scorecard Follow-Up Sequence (List 44)

| Email | Subject | Sends at |
|-------|---------|----------|
| A | It was never about willpower | +1 day after list-44 add |
| B | 530 to 800, no TRT | +3 days after list-44 add |
| C | In or out, {FIRSTNAME}? | +6 days after list-44 add |

**Sender:** Francisco Torres `<francisco@theceoshred.com>`
**CTA:** All buttons link to `https://theceoshred.com/apply`
**Tokens used:** `FIRSTNAME`, `SCORECARD_WEAKEST`, `SCORECARD_TOTAL` (from Brevo contact attributes)
**Dedup:** Each contact gets a `FOLLOWUP_SENT` attribute (e.g. `A,B`) — already-sent emails are never re-sent.

### How the scheduler works

- Runs as a background thread inside the same Render web service.
- Polls list 44 every hour (configurable via `FOLLOWUP_POLL_HOURS`).
- For each contact, calculates days elapsed since `createdAt` (accurate for new scorecard leads — they are created and added to list 44 in the same operation).
- Sends whichever emails are due and not yet sent.
- Marks sent emails on the contact via `FOLLOWUP_SENT` attribute.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_...`) | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) | — |
| `BREVO_API_KEY` | Brevo API key | — |
| `FOLLOWUP_ENABLED` | Set `"true"` to activate the scheduler | `"false"` |
| `SCORECARD_LIST_ID` | Brevo list to monitor | `44` |
| `FOLLOWUP_POLL_HOURS` | Poll interval in hours | `1` |
| `FOLLOWUP_FROM_EMAIL` | Sender email | `francisco@theceoshred.com` |
| `FOLLOWUP_FROM_NAME` | Sender name | `Francisco Torres` |
| `ADMIN_KEY` | Optional secret for `/followup/run-now` | — |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook/stripe` | Stripe webhook receiver |
| `GET` | `/health` | Health check |
| `GET` | `/followup/status` | Scheduler config and current settings |
| `POST` | `/followup/test` | Test follow-up for a specific email address |
| `POST` | `/followup/run-now` | Trigger a full cycle immediately (admin) |

---

## Testing

### Step 1 — Verify the scheduler is configured

```
GET https://YOUR_RENDER_URL/followup/status
```

Expected response:
```json
{
  "followup_scheduler": "disabled",
  "scorecard_list_id": 44,
  "poll_interval_hours": 1.0,
  "from_email": "francisco@theceoshred.com",
  "schedule": {"email_a_days": 1, "email_b_days": 3, "email_c_days": 6}
}
```

### Step 2 — Add a test contact to list 44

In Brevo, manually add a test contact (your own email) to list 44 with these attributes:
- `FIRSTNAME` = your first name
- `SCORECARD_WEAKEST` = `Testosterone`
- `SCORECARD_TOTAL` = `28`

### Step 3 — Force-process the test contact immediately

```
POST https://YOUR_RENDER_URL/followup/test
Content-Type: application/json

{ "email": "your-test@email.com" }
```

Because the contact was just added (0 days elapsed), no emails will send yet — this confirms the contact is found and attributes are read correctly.

### Step 4 — Trigger Email A manually

The simplest way to test actual delivery:

1. Submit the real scorecard form with your own email.
2. Wait 24 hours, then call:

```
POST https://YOUR_RENDER_URL/followup/run-now
X-Admin-Key: YOUR_ADMIN_KEY
```

3. Check your inbox for Email A.
4. Confirm `FOLLOWUP_SENT=A` appears on the contact in Brevo.

Repeat at +3d for Email B and +6d for Email C.

### Step 5 — Go live

Set `FOLLOWUP_ENABLED=true` in Render environment variables. The scheduler activates on next deploy/restart.

---

## Stripe Setup (existing)

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://YOUR_RENDER_URL/webhook/stripe`
3. Select event: `checkout.session.completed`
4. Copy the signing secret (`whsec_...`) and add to Render env vars

**Recommendation:** Set `metadata: { product: "testosterone" }` on each Stripe Payment Link or Price.
