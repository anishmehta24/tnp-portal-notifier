# TNP Portal Notifier

Monitors the BIT Mesra Training & Placement portal (`tp.bitmesra.co.in`) for new
companies and notifications, and (Phase 2) pushes alerts to a chat channel.

Server-rendered portal, session-cookie auth, no public API — so it logs in with
`requests` and parses HTML with BeautifulSoup. Seen items are stored in SQLite and
deduped by the portal's own per-item hash, so an item is never alerted twice.

## Modules
| File | Role |
|------|------|
| `config.py`   | URLs, secrets (from `.env`), tunables |
| `models.py`   | `Notification` / `Company` dataclasses + stable IDs |
| `auth.py`     | Login (`GET /login` → `POST /auth/login.html`), cookie reuse, re-login |
| `scraper.py`  | Parse `#job-listings` (companies) and `#newsevents` (notifications) |
| `database.py` | SQLite store, `INSERT OR IGNORE`, `notified` flag |
| `detector.py` | Pure new-item diff |
| `main.py`     | One full cycle: login → scrape → detect → store → deliver |

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in TNP_IDENTITY / TNP_PASSWORD
python main.py
```

## Status
- [x] Phase 1 — login, scraping, change detection, dedup, persistence
- [ ] Phase 2 — notification channel (Telegram / WhatsApp / etc.)
- [ ] Phase 3 — scheduler (every 15 min)

## Notes
`.env`, `*.db`, `*.cookies`, and logs are gitignored. Never commit real credentials.
