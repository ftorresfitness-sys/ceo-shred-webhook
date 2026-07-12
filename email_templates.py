"""
CEO Shred — Scorecard Follow-Up Email Templates
Emails A, B, C for contacts added to Brevo list 44.
Email R (Result) is the instant transactional email sent on scorecard submission.
All tokens are replaced before sending; no Brevo template IDs needed.
"""

APPLY_LINK = "https://theceoshred.com/apply"
STACK_LINK = "https://protocols.theceoshred.com/stack"

# Protocol links mapped by weakest corner.
# Keys cover both storage formats:
#   "Cortisol & Stress" — set by the Render /webhook/scorecard path
#   "Cortisol"          — set by the Supabase scorecard-submit edge function
PROTOCOL_MAP = {
    "Testosterone": {
        "name": "The Testosterone Protocol",
        "link": "https://protocols.theceoshred.com/testosterone"
    },
    "Cortisol & Stress": {
        "name": "The Cortisol Reset Protocol",
        "link": "https://protocols.theceoshred.com/cortisol"
    },
    "Cortisol": {
        "name": "The Cortisol Reset Protocol",
        "link": "https://protocols.theceoshred.com/cortisol"
    },
    "Insulin": {
        "name": "The Insulin Resistance Protocol",
        "link": "https://protocols.theceoshred.com/insulin"
    }
}

# Brief links mapped by weakest corner (using the old live brief until new ones are hosted)
# Old live brief link: https://drive.google.com/file/d/1nRrMTF0RlusvmgHmsqPbUPdK6BK95J8x/view
# "Cortisol" key added to match Supabase scorecard-submit storage format.
BRIEF_MAP = {
    "Testosterone": "https://drive.google.com/file/d/1nRrMTF0RlusvmgHmsqPbUPdK6BK95J8x/view",
    "Cortisol & Stress": "https://drive.google.com/file/d/1nRrMTF0RlusvmgHmsqPbUPdK6BK95J8x/view",
    "Cortisol": "https://drive.google.com/file/d/1GsBdt6tkzGiycSZGJf71_KMMzdoE_64z/view",
    "Insulin": "https://drive.google.com/file/d/1nRrMTF0RlusvmgHmsqPbUPdK6BK95J8x/view"
}

def get_utm(utm_content: str) -> str:
    return f"?utm_source=scorecard&utm_medium=email&utm_campaign=repoint&utm_content={utm_content}"

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

# ── Email R — Instant result (Email 0) ─────────────────────────────────────────

def email_r_subject(total: int) -> str:
    return f"Your score: {total} — here's what it means"

def email_r_html(firstname: str, total: int, weakest: str, band: str) -> str:
    protocol_info = PROTOCOL_MAP.get(weakest, PROTOCOL_MAP["Testosterone"])
    protocol_name = protocol_info["name"]
    protocol_link = protocol_info["link"] + get_utm("email0")
    stack_link = STACK_LINK + get_utm("email0")
    brief_link = BRIEF_MAP.get(weakest, BRIEF_MAP["Testosterone"])
    
    body = f"""
      <p>{firstname},</p>

      <p>Your Hormone Scorecard results are in.</p>

      <p>Score: {total}. Weakest corner: {weakest}.</p>

      <p>That weak corner matters more than the total. {weakest} is the system currently costing you the most — energy, waistline, recovery, drive. The other two can't compensate for it. That's how the hormone triangle works.</p>

      <p>I've put together a short brief that explains your result and what's happening underneath it:</p>

      <p><a href="{brief_link}">Download Your {weakest} Brief &rarr;</a></p>

      <p>The brief covers the what. If you want the exact daily execution — the full protocol I use with private clients — that's the {protocol_name}: the complete system for your weak corner.</p>

      <p><a href="{protocol_link}">Get the {protocol_name} — $47 &rarr;</a></p>

      <p>One note: most men who score weak in one corner have a second corner quietly failing. The Executive Endocrine Stack covers all three protocols — $141 of material for $97, lifetime access.</p>

      <p><a href="{stack_link}">Get the Full Stack — $97 &rarr;</a></p>

      <p class="sig">Francisco<br>The CEO Shred<br>theceoshred.com</p>

      <p><em>P.S. Start with the brief. It's free and it will tell you if I know what I'm talking about.</em></p>
    """
    
    if band == "Red Zone":
        body += f"""
      <hr style="border: 0; border-top: 1px solid #eee; margin: 32px 0;">
      <p>One more thing. Your score puts you in the range where a self-guided protocol may not be enough. If you want me to look at your specific situation directly, book an Executive Diagnostic — 30 minutes, $150, credited toward coaching if we work together. Application-only.</p>
      
      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Book Your Executive Diagnostic &rarr;</a>
      </div>
        """
        
    return _wrap(body)

def email_r_text(firstname: str, total: int, weakest: str, band: str) -> str:
    protocol_info = PROTOCOL_MAP.get(weakest, PROTOCOL_MAP["Testosterone"])
    protocol_name = protocol_info["name"]
    protocol_link = protocol_info["link"] + get_utm("email0")
    stack_link = STACK_LINK + get_utm("email0")
    brief_link = BRIEF_MAP.get(weakest, BRIEF_MAP["Testosterone"])
    
    text = f"""{firstname},

Your Hormone Scorecard results are in.

Score: {total}. Weakest corner: {weakest}.

That weak corner matters more than the total. {weakest} is the system currently costing you the most — energy, waistline, recovery, drive. The other two can't compensate for it. That's how the hormone triangle works.

I've put together a short brief that explains your result and what's happening underneath it:

Download Your {weakest} Brief → {brief_link}

The brief covers the what. If you want the exact daily execution — the full protocol I use with private clients — that's the {protocol_name}: the complete system for your weak corner.

Get the {protocol_name} — $47 → {protocol_link}

One note: most men who score weak in one corner have a second corner quietly failing. The Executive Endocrine Stack covers all three protocols — $141 of material for $97, lifetime access.

Get the Full Stack — $97 → {stack_link}

Francisco
The CEO Shred
theceoshred.com

P.S. Start with the brief. It's free and it will tell you if I know what I'm talking about.
"""
    if band == "Red Zone":
        text += f"""
---
One more thing. Your score puts you in the range where a self-guided protocol may not be enough. If you want me to look at your specific situation directly, book an Executive Diagnostic — 30 minutes, $150, credited toward coaching if we work together. Application-only.

Book Your Executive Diagnostic → {APPLY_LINK}
"""
    return text


# ── Email A — +1 day ──────────────────────────────────────────────────────────

EMAIL_A_SUBJECT = "The corner you didn't score"

def email_a_html(firstname: str, weakest: str) -> str:
    protocol_info = PROTOCOL_MAP.get(weakest, PROTOCOL_MAP["Testosterone"])
    protocol_name = protocol_info["name"]
    protocol_link = protocol_info["link"] + get_utm("emailA")
    stack_link = STACK_LINK + get_utm("emailA")
    
    body = f"""
      <p>{firstname},</p>

      <p>Yesterday you found your weakest corner: {weakest}.</p>

      <p>Here's what the scorecard can't show you: the three systems don't fail independently. Cortisol drives insulin resistance. Insulin resistance suppresses testosterone. Low testosterone raises stress reactivity — which raises cortisol.</p>

      <p>It's a triangle. Fix one corner while the others leak, and you're bailing water with a hole in the boat.</p>

      <p>That's why I don't sell the protocols as a "pick one" solution. The Executive Endocrine Stack is all three — Testosterone Protocol, Cortisol Reset Protocol, Insulin Resistance Protocol. 200+ pages. The complete operating system for male hormones after 40.</p>

      <p>$141 separately. $97 as the Stack. Lifetime access, including future updates.</p>

      <div class="cta-wrap">
        <a class="cta" href="{stack_link}">Get the Stack — $97 &rarr;</a>
      </div>

      <p>If budget is the constraint, start with your weak corner alone: <a href="{protocol_link}">{protocol_name} — $47</a></p>

      <p class="sig">Francisco<br>The CEO Shred</p>

      <p><em>P.S. Every man I've coached who fixed only one corner came back within 90 days for the other two. Save yourself the round trip.</em></p>
    """
    return _wrap(body)

def email_a_text(firstname: str, weakest: str) -> str:
    protocol_info = PROTOCOL_MAP.get(weakest, PROTOCOL_MAP["Testosterone"])
    protocol_name = protocol_info["name"]
    protocol_link = protocol_info["link"] + get_utm("emailA")
    stack_link = STACK_LINK + get_utm("emailA")
    
    return f"""{firstname},

Yesterday you found your weakest corner: {weakest}.

Here's what the scorecard can't show you: the three systems don't fail independently. Cortisol drives insulin resistance. Insulin resistance suppresses testosterone. Low testosterone raises stress reactivity — which raises cortisol.

It's a triangle. Fix one corner while the others leak, and you're bailing water with a hole in the boat.

That's why I don't sell the protocols as a "pick one" solution. The Executive Endocrine Stack is all three — Testosterone Protocol, Cortisol Reset Protocol, Insulin Resistance Protocol. 200+ pages. The complete operating system for male hormones after 40.

$141 separately. $97 as the Stack. Lifetime access, including future updates.

Get the Stack — $97 → {stack_link}

If budget is the constraint, start with your weak corner alone: {protocol_name} — $47 → {protocol_link}

Francisco
The CEO Shred

P.S. Every man I've coached who fixed only one corner came back within 90 days for the other two. Save yourself the round trip.
"""


# ── Email B — +3 days ─────────────────────────────────────────────────────────

EMAIL_B_SUBJECT = "Self-guided or done-with-you"

def email_b_html(firstname: str) -> str:
    stack_link = STACK_LINK + get_utm("emailB")
    
    body = f"""
      <p>{firstname},</p>

      <p>Two kinds of men take the scorecard.</p>

      <p>The first kind takes the result, gets the system, and executes alone. Disciplined, self-directed, doesn't need a coach — needs a map. If that's you, the Executive Endocrine Stack is your map. All three protocols, $97, done.</p>

      <p><a href="{stack_link}">Get the Stack — $97 &rarr;</a></p>

      <p>The second kind has read enough. He doesn't want another PDF — he wants someone to look at his numbers, his schedule, his bloodwork, and tell him exactly what to do. That's the Executive Diagnostic: 30 minutes with me, application-only, $150 — credited in full if we end up working together.</p>

      <div class="cta-wrap">
        <a class="cta" href="{APPLY_LINK}">Apply for the Executive Diagnostic &rarr;</a>
      </div>

      <p>Both roads fix the triangle. One is self-guided, one is guided. The only wrong move is the third option: knowing your weak corner and doing nothing about it.</p>

      <p class="sig">Francisco<br>The CEO Shred</p>
    """
    return _wrap(body)

def email_b_text(firstname: str) -> str:
    stack_link = STACK_LINK + get_utm("emailB")
    
    return f"""{firstname},

Two kinds of men take the scorecard.

The first kind takes the result, gets the system, and executes alone. Disciplined, self-directed, doesn't need a coach — needs a map. If that's you, the Executive Endocrine Stack is your map. All three protocols, $97, done.

Get the Stack — $97 → {stack_link}

The second kind has read enough. He doesn't want another PDF — he wants someone to look at his numbers, his schedule, his bloodwork, and tell him exactly what to do. That's the Executive Diagnostic: 30 minutes with me, application-only, $150 — credited in full if we end up working together.

Apply for the Executive Diagnostic → {APPLY_LINK}

Both roads fix the triangle. One is self-guided, one is guided. The only wrong move is the third option: knowing your weak corner and doing nothing about it.

Francisco
The CEO Shred
"""


# ── Email C — +6 days ─────────────────────────────────────────────────────────

def email_c_subject(firstname: str, band: str) -> str:
    if band == "Red Zone":
        return "Your score, one week later"
    return f"Closing the loop, {firstname}"

def email_c_html(firstname: str, weakest: str, total: str, band: str) -> str:
    stack_link = STACK_LINK + get_utm("emailC")
    
    if band == "Red Zone":
        # Variant 2 (Diagnostic-led close)
        body = f"""
          <p>{firstname},</p>

          <p>A week ago you scored {total} — with {weakest} as your weakest corner, in the range I'd flag if you were a private client.</p>

          <p>I'll be direct: at that level, I don't recommend starting self-guided. Not because the protocols don't work — because your situation likely has more than one corner failing, and sequencing matters. Get the order wrong and you'll spend three months fixing the wrong thing first.</p>

          <p>The right move is 30 minutes with me looking at your actual situation. That's the Executive Diagnostic. Application-only, $150, credited in full toward coaching if we work together. You leave the call knowing exactly what to fix first — whether we work together or not.</p>

          <div class="cta-wrap">
            <a class="cta" href="{APPLY_LINK}">Apply for the Executive Diagnostic &rarr;</a>
          </div>

          <p>If you'd rather go alone anyway, the full Stack is here: <a href="{stack_link}">Get the Stack — $97</a> — all three protocols.</p>

          <p>Either way, decide. A score like yours doesn't improve by being aware of it.</p>

          <p class="sig">Francisco<br>The CEO Shred</p>
        """
    else:
        # Variant 1 (Stack-led close)
        body = f"""
          <p>{firstname},</p>

          <p>Six days ago you found out {weakest} is your weak corner.</p>

          <p>Question: what's changed since?</p>

          <p>If the answer is "nothing," that's normal — and it's also the whole problem. Information doesn't change a body. Execution does. And execution needs a system, because willpower is exactly the resource a compromised {weakest} drains first.</p>

          <p>The system is built. The Executive Endocrine Stack — all three protocols, 200+ pages, $97, lifetime access.</p>

          <div class="cta-wrap">
            <a class="cta" href="{stack_link}">Get the Stack — $97 &rarr;</a>
          </div>

          <p>This is the last email in this series. No countdown timers, no fake deadline — the price doesn't change. But your biology doesn't wait either. Every month in the current state is a month of compounding in the wrong direction.</p>

          <p>Your call.</p>

          <p class="sig">Francisco<br>The CEO Shred</p>

          <p><em>P.S. If you'd rather have this handled with direct guidance, the Executive Diagnostic is here: <a href="{APPLY_LINK}">Apply for the Diagnostic</a> — 30 minutes, $150, credited toward coaching.</em></p>
        """
    return _wrap(body)

def email_c_text(firstname: str, weakest: str, total: str, band: str) -> str:
    stack_link = STACK_LINK + get_utm("emailC")
    
    if band == "Red Zone":
        # Variant 2
        return f"""{firstname},

A week ago you scored {total} — with {weakest} as your weakest corner, in the range I'd flag if you were a private client.

I'll be direct: at that level, I don't recommend starting self-guided. Not because the protocols don't work — because your situation likely has more than one corner failing, and sequencing matters. Get the order wrong and you'll spend three months fixing the wrong thing first.

The right move is 30 minutes with me looking at your actual situation. That's the Executive Diagnostic. Application-only, $150, credited in full toward coaching if we work together. You leave the call knowing exactly what to fix first — whether we work together or not.

Apply for the Executive Diagnostic → {APPLY_LINK}

If you'd rather go alone anyway, the full Stack is here: {stack_link} — $97, all three protocols.

Either way, decide. A score like yours doesn't improve by being aware of it.

Francisco
The CEO Shred
"""
    else:
        # Variant 1
        return f"""{firstname},

Six days ago you found out {weakest} is your weak corner.

Question: what's changed since?

If the answer is "nothing," that's normal — and it's also the whole problem. Information doesn't change a body. Execution does. And execution needs a system, because willpower is exactly the resource a compromised {weakest} drains first.

The system is built. The Executive Endocrine Stack — all three protocols, 200+ pages, $97, lifetime access.

Get the Stack — $97 → {stack_link}

This is the last email in this series. No countdown timers, no fake deadline — the price doesn't change. But your biology doesn't wait either. Every month in the current state is a month of compounding in the wrong direction.

Your call.

Francisco
The CEO Shred

P.S. If you'd rather have this handled with direct guidance, the Executive Diagnostic is here: {APPLY_LINK} — 30 minutes, $150, credited toward coaching.
"""
