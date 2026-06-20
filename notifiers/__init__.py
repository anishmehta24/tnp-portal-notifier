"""Notifier factory. NOTIFY_CHANNELS (comma-separated) decides which channels are
active, e.g. NOTIFY_CHANNELS=ntfy,discord. Falls back to console if none load."""
import logging

import config
from .console import ConsoleNotifier

log = logging.getLogger("notifiers")

_REGISTRY = {"console": ConsoleNotifier}

# Import optional channels lazily so a missing config for one doesn't break others.
try:
    from .ntfy import NtfyNotifier
    _REGISTRY["ntfy"] = NtfyNotifier
except Exception:  # pragma: no cover
    pass
try:
    from .discord import DiscordNotifier
    _REGISTRY["discord"] = DiscordNotifier
except Exception:  # pragma: no cover
    pass


def get_notifiers() -> list:
    wanted = [c.strip() for c in config.NOTIFY_CHANNELS.split(",") if c.strip()]
    active = []
    for name in wanted:
        cls = _REGISTRY.get(name)
        if not cls:
            log.warning("Unknown notify channel %r (skipped)", name)
            continue
        try:
            active.append(cls())
            log.info("Notifier enabled: %s", name)
        except Exception as e:
            log.error("Notifier %r disabled (config error): %s", name, e)
    if not active:
        log.warning("No notifier configured -- using console fallback")
        active.append(ConsoleNotifier())
    return active
