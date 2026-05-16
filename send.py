import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_ADDRESS      = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENTS         = [r.strip() for r in os.environ["RECIPIENTS"].split(",") if r.strip()]

def find_latest_digest() -> Path:
    digests = sorted(Path(".").glob("digest_*.html"), reverse=True)
    if not digests:
        raise FileNotFoundError("No digest_*.html found in current directory.")
    return digests[0]

def send(html_path: Path):
    html = html_path.read_text()
    date_str = html_path.stem.replace("digest_", "")
    try:
        subject = f"Mental Health Weekly — {datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"
    except ValueError:
        subject = f"Mental Health Weekly — {date_str}"

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

        print(f"Sent to {recipient}: {subject}")

if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else find_latest_digest()
    print(f"Sending {path}...")
    send(path)
    print("Done.")
