import anthropic
import json
import os
import smtplib
import urllib.parse
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Config ---
ANTHROPIC_KEY      = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS      = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENTS         = [r.strip() for r in open("recipients.txt") if r.strip()]

SYSTEM_PROMPT = """
You are a mental health research journalist producing a weekly digest.
Return ONLY a valid JSON object — no preamble, no markdown fences, no explanation.

JSON schema (use exactly these keys):
{
  "date_range": "May 9 – May 16, 2026",
  "highlights": [
    {"headline": "...", "url": "...", "summary": "2-3 sentences."}
  ],
  "medication_watch": [
    {"drug": "Methylphenidate", "headline": "...", "url": "...", "summary": "..."}
  ],
  "alternative_medicine": [
    {"headline": "...", "url": "...", "summary": "..."}
  ],
  "indigenous_healing": [
    {"headline": "...", "url": "...", "summary": "..."}
  ],
  "global_centers": [
    {"headline": "...", "url": "...", "summary": "..."}
  ],
  "unverified": [
    {"headline": "...", "url": "...", "summary": "..."}
  ]
}

COVERAGE SCOPE (past 7 days only):
- Developments in treatments: new drugs, therapies, studies
- Announcements from institutions, researchers, or health organizations
- Root cause research (biological, environmental, social)
- New or notable treatment centers worldwide
- Alternative treatments — plant medicine, psychedelics, breathwork, somatic therapies, etc.
- Indigenous healing practices and plant knowledge (do NOT exclude based on local legality)
- How indigenous cultures throughout history have treated mental health
  (include everything factual, including dark history: institutionalization, persecution,
   ritual-based interventions)

MEDICATION PRIORITY — always include news about these if found:
- Methylphenidate
- Vraylar (cariprazine)
- Venlafaxine (Effexor)

SOURCE STANDARDS:
- Prioritize: peer-reviewed journals, medical institutions, research publications
- Also include: independent researchers, healers, smaller publications
  IF their claims are backed by factual data or cited studies
- Unverified/emerging claims go in "unverified" only

Include 3-5 highlights. Fill every section where news exists (omit empty arrays).
Every story needs a real, working source URL.
"""

def build_user_prompt():
    today    = datetime.today()
    week_ago = today - timedelta(days=7)
    return (
        f"Today is {today.strftime('%A, %B %d, %Y')}. "
        f"Research and write the weekly mental health digest covering "
        f"{week_ago.strftime('%B %d')} through {today.strftime('%B %d, %Y')}. "
        f"Use web search. Return only the JSON object — nothing else."
    )

def generate_digest() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt()}]
    )
    for block in reversed(response.content):
        if block.type == "text":
            text = block.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
    raise ValueError("No JSON output from Claude")

# --- HTML template helpers ---

S = "style"  # shorthand

def story_html(story: dict) -> str:
    headline = story.get("headline", "")
    url      = story.get("url", "#")
    summary  = story.get("summary", "")
    drug     = story.get("drug", "")

    drug_tag = (
        f'<span style="display:inline-block;background:#eef6fb;color:#2980b9;'
        f'font-size:11px;font-weight:700;padding:2px 8px;border-radius:3px;'
        f'margin-bottom:8px;">{drug}</span><br>'
    ) if drug else ""

    return f"""
      <div style="margin-bottom:22px;padding-bottom:22px;border-bottom:1px solid #ececec;">
        {drug_tag}
        <a href="{url}"
           style="color:#1a1a1a;font-size:15px;font-weight:600;text-decoration:none;line-height:1.4;
                  display:block;margin-bottom:6px;">{headline}</a>
        <p style="margin:0;color:#555;font-size:14px;line-height:1.65;">{summary}</p>
      </div>"""

def section_html(title: str, stories: list) -> str:
    if not stories:
        return ""
    items = "".join(story_html(s) for s in stories)
    return f"""
    <div style="margin-bottom:36px;">
      <h2 style="margin:0 0 16px;padding-bottom:10px;border-bottom:2px solid #1a1a1a;
                 font-size:11px;font-weight:700;letter-spacing:0.09em;
                 text-transform:uppercase;color:#888;">
        {title}
      </h2>
      {items}
    </div>"""

def build_html(digest: dict, subject: str) -> str:
    date_range = digest.get("date_range", "")
    display_date = subject.replace("Mental Health Weekly — ", "")

    prompt  = f"I just received this mental health weekly digest. Let's discuss it:\n\n{subject}"
    encoded = urllib.parse.quote(prompt)
    claude_url = f"https://claude.ai/new?q={encoded}"

    sections = (
        section_html("This Week's Highlights",              digest.get("highlights", []))
        + section_html("Medication Watch",                  digest.get("medication_watch", []))
        + section_html("Alternative &amp; Plant Medicine",  digest.get("alternative_medicine", []))
        + section_html("Indigenous Healing — History &amp; Practice", digest.get("indigenous_healing", []))
        + section_html("Global Treatment Centers &amp; Announcements", digest.get("global_centers", []))
        + section_html("Unverified / Worth Watching",       digest.get("unverified", []))
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f0f0f0;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">

  <div style="max-width:600px;margin:32px auto;padding:0 16px 48px;">

    <!-- Header -->
    <div style="background:#1a1a1a;padding:28px 32px;border-radius:8px 8px 0 0;">
      <p style="margin:0 0 6px;color:#777;font-size:11px;font-weight:700;
                letter-spacing:0.1em;text-transform:uppercase;">Mental Health Weekly</p>
      <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;line-height:1.25;">
        {display_date}
      </h1>
      <p style="margin:8px 0 0;color:#aaa;font-size:13px;">{date_range}</p>
    </div>

    <!-- Body -->
    <div style="background:#ffffff;padding:32px 32px 24px;
                border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;">

      {sections}

      <!-- Open in Claude -->
      <div style="text-align:center;margin:8px 0 28px;">
        <a href="{claude_url}"
           style="display:inline-block;background:#5436da;color:#ffffff;
                  padding:13px 28px;border-radius:8px;text-decoration:none;
                  font-size:14px;font-weight:600;letter-spacing:0.01em;">
          Open in Claude
        </a>
        <p style="margin:10px 0 0;color:#bbb;font-size:12px;">
          Opens a new conversation with this digest as context
        </p>
      </div>

      <!-- Footer -->
      <p style="margin:0;color:#ccc;font-size:11px;text-align:center;line-height:1.7;">
        Curated for informational purposes only.<br>
        Always consult a healthcare provider before making medical decisions.
      </p>

    </div>
  </div>

</body>
</html>"""

def send_emails(html: str, subject: str):
    for recipient in RECIPIENTS:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = recipient
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [recipient], msg.as_string())

        print(f"Sent to {recipient}")

if __name__ == "__main__":
    print("Generating digest...")
    today_str = datetime.today().strftime("%B %d, %Y")
    subject   = f"Mental Health Weekly — {today_str}"

    digest = generate_digest()
    html   = build_html(digest, subject)

    print("Sending...")
    send_emails(html, subject)
    print("Done.")
