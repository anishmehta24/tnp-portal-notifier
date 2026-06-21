"""Authenticated session management for the TNP portal.

Verified login flow:
  1. GET  /login              -> sets the session cookie (cookie name is "/")
  2. POST /auth/login.html    -> {identity, txtcentrenm, password, submit:"Login"}
  3. session cookie is now authenticated

Cookies are pickled to disk so we don't re-login every cycle; we re-login only
when a fetch shows we've been bounced back to the login page.
"""
import logging
import pickle
import time

import requests

import config

log = logging.getLogger(__name__)


def _new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT})
    return s


def _save_cookies(session: requests.Session):
    with open(config.COOKIE_PATH, "wb") as f:
        pickle.dump(session.cookies, f)


def _load_cookies(session: requests.Session) -> bool:
    if not config.COOKIE_PATH.exists():
        return False
    try:
        with open(config.COOKIE_PATH, "rb") as f:
            session.cookies.update(pickle.load(f))
        return True
    except Exception as e:  # corrupt cookie file -> just re-login
        log.warning("Could not load cookies: %s", e)
        return False


def is_authenticated(session: requests.Session) -> bool:
    """An authenticated index page contains the job-listings table; the
    unauthenticated root redirects to login and returns an empty body."""
    try:
        r = session.get(config.INDEX_URL, timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException as e:
        log.warning("Auth check request failed: %s", e)
        return False
    return r.status_code == 200 and "job-listings" in r.text


def login(session: requests.Session) -> bool:
    if not config.TNP_IDENTITY or not config.TNP_PASSWORD:
        raise RuntimeError("TNP_IDENTITY / TNP_PASSWORD not set (check your .env)")
    log.info("Logging in as %s", config.TNP_IDENTITY)
    payload = {
        "identity": config.TNP_IDENTITY,
        "txtcentrenm": config.TNP_CENTRE,
        "password": config.TNP_PASSWORD,
        "submit": "Login",
    }
    session.headers["Referer"] = config.LOGIN_PAGE
    # The portal occasionally rejects/throttles a login transiently (esp. from
    # cloud IPs), so retry with backoff before declaring a credential failure.
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            session.get(config.LOGIN_PAGE, timeout=config.REQUEST_TIMEOUT)  # fresh token/cookie
            session.post(config.LOGIN_ACTION, data=payload,
                         timeout=config.REQUEST_TIMEOUT)
            if is_authenticated(session):
                _save_cookies(session)
                log.info("Login successful")
                return True
        except requests.RequestException as e:
            log.warning("Login attempt %d/%d errored: %s",
                        attempt, config.MAX_RETRIES, e)
        if attempt < config.MAX_RETRIES:
            wait = config.RETRY_BACKOFF ** attempt
            log.warning("Login attempt %d/%d unsuccessful -- retry in %ds",
                        attempt, config.MAX_RETRIES, wait)
            time.sleep(wait)
    log.error("Login failed after %d attempts -- transient portal issue or bad "
              "credentials", config.MAX_RETRIES)
    return False


def get_session() -> requests.Session:
    """Return a ready-to-use authenticated session, reusing saved cookies."""
    s = _new_session()
    if _load_cookies(s) and is_authenticated(s):
        log.debug("Reused saved session")
        return s
    if not login(s):
        raise RuntimeError("Unable to authenticate to TNP portal")
    return s


def ensure_logged_in(session: requests.Session) -> requests.Session:
    """Call before each scrape; re-logs in if the session has expired."""
    if is_authenticated(session):
        return session
    log.info("Session expired -- re-authenticating")
    login(session)
    return session
