import anthropic
import sendgrid
import base64
import os
import urllib.parse
from datetime import datetime, timedelta
from sendgrid.helpers.mail import Mail, To

# --- Config ---
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
SENDGRID_KEY  = os.environ["SENDGRID_API_KEY"]
SENDER_EMAIL  = os.environ["SENDER_EMAIL"]
RECIPIENTS    = [r.strip() for r in open("recipients.txt") if r.strip()]

SYSTEM_PROMPT = """
You are a mental health research journalist producing a weekly digest email.
Your output must be a single, complete, valid HTML document — nothing else.
No markdown, no preamble, no explanation outside the HTML.

COVERAGE SCOPE (past 7 days only):
- Developments in treatments: new drugs, therapies, studies
- Announcements from institutions, researchers, or health organizations
- Root cause research (biological, environmental, social)
- New or notable treatment centers worldwide
- Alternative treatments — plant medicine, psychedelics, breathwork, somatic therapies, etc.
- Indigenous healing practices and plant knowledge (do NOT exclude based on local legality)
- How indigenous cultures throughout history have treated mental health
  (this is a historical/cultural segment — include everything factual, even dark history
   such as institutionalization, persecution, or ritual-based interventions)

MEDICATION PRIORITY — always include news about these if found:
- Methylphenidate
- Vraylar (cariprazine)
- Venlafaxine (Effexor)

SOURCE STANDARDS:
- Prioritize: peer-reviewed journals, medical institutions, research publications
- Also include: independent researchers, healers, smaller publications
  IF their claims are backed by factual data or cited studies
- Unverified/emerging headlines should be included in a clearly marked
  "Unverified / Worth Watching" section

EMAIL FORMAT REQUIREMENTS:
- Clean, readable HTML with inline CSS (dark background preferred: #0f0f0f or similar)
- Each story must have an embedded hyperlink to the source
- Sections:
  1. This Week's Highlights (3-5 top vetted stories)
  2. Medication Watch (Methylphenidate / Vraylar / Venlafaxine)
  3. Alternative & Plant Medicine
  4. Indigenous Healing — History & Practice
  5. Global Treatment Centers & Announcements
  6. Unverified / Worth Watching
  7. Open in Claude button (placeholder — will be injected by script)
- Use a professional but warm editorial tone
- Include the date range covered at the top
"""

def build_user_prompt():
    today = datetime.today()
    week_ago = today - timedelta(days=7)
    return (
        f"Today is {today.strftime('%A, %B %d, %Y')}. "
        f"Research and write the weekly mental health digest covering "
        f"{week_ago.strftime('%B %d')} through {today.strftime('%B %d, %Y')}. "
        f"Use web search to find real, current stories. Output only the HTML email."
    )

def generate_email_html():
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt()}]
    )
    # Extract the final text block (HTML)
    for block in reversed(response.content):
        if block.type == "text":
            return block.text
    raise ValueError("No text output from Claude")

def inject_open_in_claude_button(html: str, subject: str) -> str:
    # Encode the email content as a Claude.ai deep link
    prompt = f"I just received this mental health weekly digest. Let's discuss it:\n\n{subject}"
    encoded = urllib.parse.quote(prompt)
    claude_url = f"https://claude.ai/new?q={encoded}"
    button_html = f"""
    <div style="text-align:center;margin:40px 0;">
      <a href="{claude_url}"
         style="background:#6c47ff;color:#fff;padding:14px 28px;
                border-radius:8px;text-decoration:none;font-size:15px;
                font-family:sans-serif;font-weight:600;">
        💬 Open in Claude
      </a>
      <p style="color:#888;font-size:12px;margin-top:10px;font-family:sans-serif;">
        Opens a new Claude conversation with this digest as context
      </p>
    </div>
    """
    # Inject before closing body tag
    return html.replace("</body>", button_html + "</body>")

def send_emails(html: str, subject: str):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_KEY)
    for recipient in RECIPIENTS:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject=subject,
            html_content=html
        )
        response = sg.send(message)
        print(f"Sent to {recipient}: {response.status_code}")

if __name__ == "__main__":
    print("Generating newsletter...")
    today_str = datetime.today().strftime("%B %d, %Y")
    subject = f"Mental Health Weekly — {today_str}"

    html = generate_email_html()
    html = inject_open_in_claude_button(html, subject)

    print("Sending emails...")
    send_emails(html, subject)
    print("Done.")
