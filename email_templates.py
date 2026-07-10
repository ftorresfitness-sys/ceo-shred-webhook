"""
CEO Shred — Scorecard Follow-Up Email Templates
Emails A, B, C for contacts added to Brevo list 44.
All tokens are replaced before sending; no Brevo template IDs needed.
"""

APPLY_LINK = "https://theceoshred.com/apply"
GUIDE_LINK = "https://drive.google.com/file/d/1nRrMTF0RlusvmgHmsqPbUPdK6BK95J8x/view"

# ── Shared HTML wrapper ────────────────────────────────────────────────────────

def _wrap(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The CEO Shred</title>
  <style>
    body {{
      margin: 0; padding: 0;
      background: #f5f5f5;
      font-family: Georgia, 'Times New Roman', serif;
      color: #1a1a1a;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 32px auto;
      background: #ffffff;
      border-radius: 4px;
      overflow: hidden;
    }}
    .header {{
      background: #0d0d0d;
      padding: 24px 32px;
    }}
    .header span {{
      color: #ffffff;
      font-size: 13px;
      letter-spacing: 2px;
      text-transform: uppercase;
      font-family: Arial, sans-serif;
    }}
    .body {{
      padding: 36px 32px;
      line-height: 1.7;
      font-size: 16px;
    }}
    .body p {{
      margin: 0 0 18px 0;
    }}
    .cta-wrap {{
      text-align: center;
      margin: 32px 0;
    }}
    .cta {{
      display: inline-block;
      background: #0d0d0d;
      color: #ffffff !important;
      text-decoration: none;
      padding: 14px 32px;
      font-family: Arial, sans-serif;
      font-size: 14px;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 2px;
    }}
    .sig {{
      margin-top: 28px;
      font-size: 14px;
      color: #555;
    }}
    .footer {{
      background: #f5f5f5;
      padding: 16px 32px;
      font-size: 12px;
      color: #999;
      font-family: Arial, sans-serif;
      text-align: center;
    }}
    @media (max-width: 600px) {{
      .body {{ padding: 24px 20px; }}
      .header {{ padding: 20px; }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <span>The CEO Shred</span>
    </div>
    <div class="body">
      {body_html}
    </div>
    <div class="footer">
      &copy; The CEO Shred &nbsp;|&nbsp; theceoshred.com<br />
      You received this because you completed the Hormone Scorecard.
    </div>
  </div>
</body>
</html>"""


# ── Email A — +1 day ──────────────────────────────────────────────────────────

EMAIL_A_SUBJECT = "It was never about willpower"

def email_a_html(firstname: str, weakest: str) -> str:
    body = f"""
      <p>Hi {firstname},</p>

      <p>Your scorecard flagged <strong>{weakest}</strong> as your weakest area.
      That&rsquo;s not a small detail &mdash; it&rsquo;s the bottleneck dragging down
      everything downstream: energy, fat storage, drive, recovery.</p>

      <p>Here&rsquo;s the part most men get wrong: this isn&rsquo;t a discipline problem.
      You already have discipline &mdash; you run a company. If effort alone fixed it,
      you&rsquo;d already be lean and sharp. The issue is upstream of effort. Your
      endocrine system is sending the wrong signals, and no amount of willpower
      out-argues a hormone.</p>

      <p>Change the signal and the body follows. Your <strong>{weakest}</strong> score
      is exactly where to start.</p>

      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Book Your Executive Diagnostic &mdash; $150 &rarr;</a>
      </div>

      <p>One 30-minute conversation. We pinpoint what&rsquo;s suppressing your
      {weakest} and map your 90-day fix. The $150 is credited if you move into
      coaching.</p>

      <p class="sig">&mdash; Francisco &middot; The CEO Shred</p>
    """
    return _wrap(body)

def email_a_text(firstname: str, weakest: str) -> str:
    return f"""Hi {firstname},

Your scorecard flagged {weakest} as your weakest area. That's not a small detail — it's the bottleneck dragging down everything downstream: energy, fat storage, drive, recovery.

Here's the part most men get wrong: this isn't a discipline problem. You already have discipline — you run a company. If effort alone fixed it, you'd already be lean and sharp. The issue is upstream of effort. Your endocrine system is sending the wrong signals, and no amount of willpower out-argues a hormone.

Change the signal and the body follows. Your {weakest} score is exactly where to start.

Book Your Executive Diagnostic — $150:
{APPLY_LINK}

One 30-minute conversation. We pinpoint what's suppressing your {weakest} and map your 90-day fix. The $150 is credited if you move into coaching.

— Francisco · The CEO Shred
"""


# ── Email B — +3 days ─────────────────────────────────────────────────────────

EMAIL_B_SUBJECT = "530 to 800, no TRT"

def email_b_html(firstname: str, weakest: str) -> str:
    body = f"""
      <p>{firstname},</p>

      <p>A few of the men who&rsquo;ve run this:</p>

      <p>
        <strong>Nassif, 44</strong> &mdash; tripled his testosterone naturally in six months.
        Blood-work verified, no TRT.<br />
        <strong>Gary, 45</strong> &mdash; down 27 lbs in five months, and the food noise gone.<br />
        <strong>Ibrahim, 37</strong> &mdash; 10.3 kg in 90 days, abs back, sleep fixed,
        through two weeks of travel.
      </p>

      <p>None had more time or discipline than you. They had a system built around their
      actual numbers instead of guesses.</p>

      <p>That&rsquo;s what the Executive Diagnostic is: 30 minutes to review your situation,
      pinpoint what&rsquo;s suppressing your <strong>{weakest}</strong>, and map your protocol.
      $150, credited in full if you move forward. No pitch &mdash; I&rsquo;ll tell you straight
      if it&rsquo;s a fit.</p>

      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Book Your Executive Diagnostic &mdash; $150 &rarr;</a>
      </div>

      <p class="sig">&mdash; Francisco &middot; The CEO Shred</p>
    """
    return _wrap(body)

def email_b_text(firstname: str, weakest: str) -> str:
    return f"""{firstname},

A few of the men who've run this:

Nassif, 44 — tripled his testosterone naturally in six months. Blood-work verified, no TRT.
Gary, 45 — down 27 lbs in five months, and the food noise gone.
Ibrahim, 37 — 10.3 kg in 90 days, abs back, sleep fixed, through two weeks of travel.

None had more time or discipline than you. They had a system built around their actual numbers instead of guesses.

That's what the Executive Diagnostic is: 30 minutes to review your situation, pinpoint what's suppressing your {weakest}, and map your protocol. $150, credited in full if you move forward. No pitch — I'll tell you straight if it's a fit.

Book Your Executive Diagnostic — $150:
{APPLY_LINK}

— Francisco · The CEO Shred
"""


# ── Email C — +6 days ─────────────────────────────────────────────────────────

EMAIL_C_SUBJECT = "In or out, {firstname}?"  # subject uses firstname — formatted at send time

def email_c_subject(firstname: str) -> str:
    return f"In or out, {firstname}?"

def email_c_html(firstname: str, total: str) -> str:
    body = f"""
      <p>{firstname},</p>

      <p>You took the scorecard for a reason. Your score (<strong>{total}</strong>) and your
      weak corner didn&rsquo;t happen by accident, and they won&rsquo;t fix themselves.</p>

      <p>I keep a small number of diagnostic slots each week. If you want yours, take it now.
      If the timing&rsquo;s wrong, no problem &mdash; the guide is yours to keep either way.</p>

      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Book Your Executive Diagnostic &mdash; $150 &rarr;</a>
      </div>

      <p class="sig">&mdash; Francisco &middot; The CEO Shred</p>
    """
    return _wrap(body)

def email_c_text(firstname: str, total: str) -> str:
    return f"""{firstname},

You took the scorecard for a reason. Your score ({total}) and your weak corner didn't happen by accident, and they won't fix themselves.

I keep a small number of diagnostic slots each week. If you want yours, take it now. If the timing's wrong, no problem — the guide is yours to keep either way.

Book Your Executive Diagnostic — $150:
{APPLY_LINK}

— Francisco · The CEO Shred
"""
