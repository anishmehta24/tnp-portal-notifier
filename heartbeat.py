"""Dead-man's-switch ping. After each successful cycle we GET HEARTBEAT_URL; if
the whole service (or VM) dies, the pings stop and the monitor alerts you.

Designed for healthchecks.io (free): create a check with period 20m + grace, set
HEARTBEAT_URL to its ping URL (https://hc-ping.com/<uuid>). Appending /fail signals
a failed cycle. Works with any URL-ping monitor, or a self-hosted instance."""
import logging

import requests

import config

log = logging.getLogger("heartbeat")


def _ping(suffix: str = ""):
    if not config.HEARTBEAT_URL:
        return
    url = config.HEARTBEAT_URL.rstrip("/") + suffix
    try:
        requests.get(url, timeout=10)
        log.debug("heartbeat %s ok", suffix or "(success)")
    except requests.RequestException as e:
        log.warning("heartbeat ping failed: %s", e)


def success():
    _ping()


def fail():
    _ping("/fail")
