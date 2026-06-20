"""Central configuration. Secrets come from environment / .env (never hardcoded)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv is optional; env vars still work without it
    pass

BASE_DIR = Path(__file__).resolve().parent

# --- Portal ---
BASE_URL = "https://tp.bitmesra.co.in"
LOGIN_PAGE = f"{BASE_URL}/login"
LOGIN_ACTION = f"{BASE_URL}/auth/login.html"
INDEX_URL = f"{BASE_URL}/index.html"
NEWSEVENTS_URL = f"{BASE_URL}/newsevents"

# --- Credentials (from environment) ---
TNP_IDENTITY = os.getenv("TNP_IDENTITY", "")
TNP_PASSWORD = os.getenv("TNP_PASSWORD", "")
TNP_CENTRE = os.getenv("TNP_CENTRE", "")  # txtcentrenm; empty works for this account

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# --- Storage ---
DB_PATH = BASE_DIR / "tnp.db"
COOKIE_PATH = BASE_DIR / "session.cookies"

# --- Behaviour ---
POLL_INTERVAL_MIN = int(os.getenv("POLL_INTERVAL_MIN", "15"))

# Only alert for companies you are eligible for (from the portal's Eligible list).
ELIGIBLE_ONLY = os.getenv("ELIGIBLE_ONLY", "true").lower() in ("1", "true", "yes")
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, exponential

LOG_PATH = BASE_DIR / "tnp_notifier.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Notifications ---
# Comma-separated active channels, e.g. "ntfy", "discord", "ntfy,discord".
NOTIFY_CHANNELS = os.getenv("NOTIFY_CHANNELS", "console")

# ntfy.sh (no account needed; pick a long, hard-to-guess topic)
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
NTFY_TOKEN = os.getenv("NTFY_TOKEN", "")  # only for protected/self-hosted topics

# Discord webhook URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
