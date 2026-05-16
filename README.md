# mental-health-weekly

Weekly mental health research digest. A scheduled GitHub Actions job runs `send_newsletter.py`, which asks Claude (with `web_search`) to research the past 7 days, generates a self-contained HTML email, injects an "Open in Claude" deep-link button, and sends via SendGrid to the addresses in `recipients.txt`.

## Run

- **Schedule:** Saturday 8am Eastern (`.github/workflows/send_newsletter.yaml`).
- **Manual trigger:** Actions tab on GitHub → "Send Mental Health Weekly" → Run workflow.
- **Secrets required (GitHub Actions):** `ANTHROPIC_API_KEY`, `SENDGRID_API_KEY`, `SENDER_EMAIL`.

## Notes & ideas

Project decisions, deliverability brainstorming, content ideas, and the status log live in the vault:
`Projects/mental-health-weekly/CLAUDE.md` (Obsidian Second Brain).
