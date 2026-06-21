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

### Option A — GitHub Actions (free, no server, no card) ✅ in use
`.github/workflows/poll.yml` runs one cycle every 15 min on free public-repo
Actions. The dedup DB is persisted between runs via `actions/cache`. A fresh DB
(first run, or after a cache eviction) is seeded silently so history isn't blasted.

Set these repo secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|-------|
| `TNP_PASSWORD` | your portal password |
| `NTFY_TOPIC`   | your ntfy topic (e.g. `tnp`) |
| `TNP_IDENTITY` | roll number (optional; defaults in the workflow) |
| `HEARTBEAT_URL`| healthchecks.io ping URL (optional) |

Trigger manually from the Actions tab ("Run workflow") or wait for the schedule.
Note: GitHub auto-disables scheduled workflows after 60 days of repo inactivity —
it emails you to re-enable with one click.

### Option B — Long-running process (VPS / Pi / your PC)
`python scheduler.py` runs one cycle immediately, then every `POLL_INTERVAL_MIN`
minutes. Each run is crash-isolated — a failed poll is logged and the loop continues.

### On a Linux VM (Oracle Cloud Always Free, or any VPS)
Create an Ubuntu VM (on Oracle pick an **Always Free** shape: `VM.Standard.E2.1.Micro`
or `VM.Standard.A1.Flex`). Only outbound HTTPS is needed — no inbound ports beyond SSH.

```bash
ssh ubuntu@<PUBLIC_IP>
git clone https://github.com/anishmehta24/tnp-portal-notifier.git
cd tnp-portal-notifier
bash deploy/setup.sh          # 1st run: creates .env, then stops
nano .env                     # fill TNP creds, NTFY_TOPIC, HEARTBEAT_URL
bash deploy/setup.sh          # 2nd run: installs + starts the service
journalctl -u tnp-notifier -f # watch it
```
`setup.sh` builds the venv, rewrites the unit's user/paths, and enables the service.
`Restart=always` + `enable` brings it back after crashes and reboots.

**Update later:** `git pull && sudo systemctl restart tnp-notifier`

### Heartbeat (know if the VM dies)
Create a free check at [healthchecks.io](https://healthchecks.io) (period 20m, grace
10m), put its ping URL in `.env` as `HEARTBEAT_URL`, and add its **ntfy** integration
on topic `tnp`. Each healthy cycle pings it; if pings stop, you get alerted.

### On Windows (Task Scheduler)
Create a task → trigger "At log on" → action: `python.exe scheduler.py` in the
project dir. Or just run `python scheduler.py` in a terminal.

## Status
- [x] Phase 1 — login, scraping, change detection, dedup, persistence
- [x] Phase 2 — notification channels (ntfy, Discord, console; pluggable)
- [x] Phase 3 — scheduler (every 15 min, crash-isolated) + systemd unit

## Notes
`.env`, `*.db`, `*.cookies`, and logs are gitignored. Never commit real credentials.
