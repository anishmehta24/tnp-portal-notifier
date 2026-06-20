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
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, exponential

LOG_PATH = BASE_DIR / "tnp_notifier.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
