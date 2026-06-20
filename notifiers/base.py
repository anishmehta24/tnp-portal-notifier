"""Notifier interface. A channel just needs send(title, body, url) -> bool.
Returning True means 'delivered'; main only marks an item notified when at least
one channel returns True, so a transient failure is retried next cycle."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

log = logging.getLogger("notifiers")


class Notifier(ABC):
    name = "base"

    @abstractmethod
    def send(self, title: str, body: str, url: str = "") -> bool:
        ...

    def send_item(self, item) -> bool:
        """item is a Notification or Company (has .format_alert / fields)."""
        title = getattr(item, "title", None) or getattr(item, "name", "TNP update")
        body = item.format_alert() if hasattr(item, "format_alert") else str(item)
        url = getattr(item, "url", "")
        try:
            ok = self.send(title, body, url)
            if not ok:
                log.warning("%s: send returned False for %r", self.name, title)
            return ok
        except Exception as e:
            log.warning("%s: send failed for %r: %s", self.name, title, e)
            return False
