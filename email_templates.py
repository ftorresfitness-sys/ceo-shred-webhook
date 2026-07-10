"""
CEO Shred — Scorecard Follow-Up Email Templates
Emails A, B, C for contacts added to Brevo list 44.
Email R (Result) is the instant transactional email sent on scorecard submission.
All tokens are replaced before sending; no Brevo template IDs needed.
"""

APPLY_LINK = "https://calendly.com/franciscofitness/executive-diagnostic"
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
    .score-box {{
      background: #0d0d0d;
      color: #ffffff;
      padding: 24px 28px;
      margin: 24px 0;
      border-radius: 2px;
    }}
    .score-box .score-label {{
      font-family: Arial, sans-serif;
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #999;
      margin: 0 0 4px 0;
    }}
    .score-box .score-value {{
      font-size: 28px;
      font-weight: bold;
      color: #ffffff;
      margin: 0 0 12px 0;
    }}
    .score-box .score-detail {{
      font-family: Arial, sans-serif;
      font-size: 13px;
      color: #ccc;
      margin: 4px 0;
    }}
    .guide-box {{
      background: #f9f5ec;
      border-left: 3px solid #B68B3B;
      padding: 18px 22px;
      margin: 24px 0;
    }}
    .guide-box p {{
      margin: 0 0 10px 0;
      font-size: 15px;
    }}
    .guide-box a {{
      color: #B68B3B;
      font-weight: bold;
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


# ── Email R — Instant result (sent immediately on scorecard submission) ────────

EMAIL_R_SUBJECT = "Your Executive Hormone Score — {archetype}"

def email_r_subject(archetype: str) -> str:
    return f"Your Executive Hormone Score — {archetype}"

def email_r_html(firstname: str, archetype: str, tier: str,
                 t_score: int, i_score: int, c_score: int,
                 composite: int, weakest: str) -> str:
    tier_label = tier.upper() if tier else "FUNCTIONAL"
    body = f"""
      <p>Hi {firstname},</p>

      <p>Your results are in. Here&rsquo;s what the diagnostic found.</p>

      <div class="score-box">
        <p class="score-label">Overall Score</p>
        <p class="score-value">{composite} / 100 &mdash; {tier_label}</p>
        <p class="score-detail">Testosterone &nbsp;&middot;&nbsp; {t_score}/100</p>
        <p class="score-detail">Insulin &nbsp;&middot;&nbsp; {i_score}/100</p>
        <p class="score-detail">Cortisol &nbsp;&middot;&nbsp; {c_score}/100</p>
        <p class="score-detail" style="margin-top:12px; color:#f0c060;">
          Weakest corner: <strong>{weakest}</strong>
        </p>
      </div>

      <p>Your archetype is <strong>{archetype}</strong>. This is the pattern that best
      describes where your endocrine system is right now &mdash; and where the leverage is.</p>

      <p>Most men at your level have the discipline. What they&rsquo;re missing is the
      correct target. Your weakest corner (<strong>{weakest}</strong>) is the upstream
      signal that&rsquo;s been running the wrong program. Fix that first and everything
      else responds.</p>

      <div class="guide-box">
        <p><strong>Your Testosterone Rebuild Guide</strong></p>
        <p>A practical framework for the first 30 days. Read it before you do anything else.</p>
        <p><a href="{GUIDE_LINK}">Download the guide &rarr;</a></p>
      </div>

      <p>If you want a custom protocol built around your specific numbers, the Executive
      Diagnostic is the next step. 30 minutes. I&rsquo;ll tell you exactly what to fix
      and in what order. The $150 is credited in full if you move into coaching.</p>

      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Book Your Executive Diagnostic &mdash; $150 &rarr;</a>
      </div>

      <p class="sig">&mdash; Francisco &middot; The CEO Shred</p>
    """
    return _wrap(body)

def email_r_text(firstname: str, archetype: str, tier: str,
                 t_score: int, i_score: int, c_score: int,
                 composite: int, weakest: str) -> str:
    tier_label = tier.upper() if tier else "FUNCTIONAL"
    return f"""Hi {firstname},

Your results are in.

OVERALL SCORE: {composite}/100 — {tier_label}
Testosterone: {t_score}/100
Insulin: {i_score}/100
Cortisol: {c_score}/100
Weakest corner: {weakest}

Your archetype is {archetype}. This is the pattern that best describes where your endocrine system is right now — and where the leverage is.

Most men at your level have the discipline. What they're missing is the correct target. Your weakest corner ({weakest}) is the upstream signal that's been running the wrong program. Fix that first and everything else responds.

YOUR TESTOSTERONE REBUILD GUIDE
A practical framework for the first 30 days. Read it before you do anything else.
{GUIDE_LINK}

If you want a custom protocol built around your specific numbers, the Executive Diagnostic is the next step. 30 minutes. I'll tell you exactly what to fix and in what order. The $150 is credited in full if you move into coaching.

Book Your Executive Diagnostic — $150:
{APPLY_LINK}

— Francisco · The CEO Shred
"""


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

      <div class="guide-box">
        <p><strong>In case you missed it</strong></p>
        <p>Your Testosterone Rebuild Guide is still waiting. If you haven&rsquo;t read it yet,
        start there &mdash; it covers the first 30 days.</p>
        <p><a href="{GUIDE_LINK}">Read the guide &rarr;</a></p>
      </div>

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

IN CASE YOU MISSED IT
Your Testosterone Rebuild Guide is still waiting. If you haven't read it yet, start there — it covers the first 30 days.
{GUIDE_LINK}

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

      <div class="guide-box">
        <p><strong>Your Testosterone Rebuild Guide</strong></p>
        <p><a href="{GUIDE_LINK}">Read it here &rarr;</a></p>
      </div>

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

Your Testosterone Rebuild Guide: {GUIDE_LINK}

Book Your Executive Diagnostic — $150:
{APPLY_LINK}

— Francisco · The CEO Shred
"""
