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

## Notifications
Channel-agnostic `notifiers/` package; pick channels with `NOTIFY_CHANNELS` in `.env`
(comma-separated). An item is marked delivered only when a channel succeeds, so a
failed send is retried next cycle.

| Channel | Setup |
|---------|-------|
| `ntfy`    | No account. Set `NTFY_TOPIC` to a long random string; subscribe in the ntfy app. |
| `discord` | Set `DISCORD_WEBHOOK_URL` to a channel webhook. |
| `console` | Default fallback; prints alerts. |

## Running continuously
`python scheduler.py` runs one cycle immediately, then every `POLL_INTERVAL_MIN`
minutes. Each run is crash-isolated — a failed poll is logged and the loop continues.

### On a Linux VPS (systemd)
```bash
cd ~ && git clone https://github.com/anishmehta24/tnp-portal-notifier.git
cd tnp-portal-notifier
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env          # fill creds + NTFY_TOPIC
sudo cp deploy/tnp-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tnp-notifier
journalctl -u tnp-notifier -f             # watch logs
```
Edit `User`/paths in the unit file to match your box. `Restart=always` brings it
back after crashes or reboots.

### On Windows (Task Scheduler)
Create a task → trigger "At log on" → action: `python.exe scheduler.py` in the
project dir. Or just run `python scheduler.py` in a terminal.

## Status
- [x] Phase 1 — login, scraping, change detection, dedup, persistence
- [x] Phase 2 — notification channels (ntfy, Discord, console; pluggable)
- [x] Phase 3 — scheduler (every 15 min, crash-isolated) + systemd unit

## Notes
`.env`, `*.db`, `*.cookies`, and logs are gitignored. Never commit real credentials.
