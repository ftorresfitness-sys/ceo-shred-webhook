# CEO Shred — Stripe Webhook Handler

Receives `checkout.session.completed` events from Stripe and adds the buyer to the correct Brevo delivery list, which triggers the automated protocol email.

## Product → Brevo List Mapping

| Product | Brevo List ID |
|---------|--------------|
| Testosterone Protocol | 38 |
| Cortisol Reset Protocol | 39 |
| Insulin Resistance Protocol | 40 |
| Executive Endocrine Stack | 41 |
| Complete EOS Vault | 42 |

## How Product Resolution Works

The webhook resolves which list to add the buyer to by checking (in order):
1. `session.metadata.product` — e.g. `"testosterone"`
2. `session.metadata.protocol` — e.g. `"cortisol"`
3. Stripe line item product name — e.g. `"Testosterone Protocol"`
4. Stripe product metadata fields

**Recommendation:** Set `metadata: { product: "testosterone" }` on each Stripe Payment Link or Price.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) |
| `BREVO_API_KEY` | Brevo API key |

## Endpoints

- `POST /webhook/stripe` — Stripe webhook receiver
- `GET /health` — Health check
- `GET /` — Service info

## Stripe Setup

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://YOUR_RENDER_URL/webhook/stripe`
3. Select event: `checkout.session.completed`
4. Copy the signing secret (`whsec_...`) and add to Render env vars
