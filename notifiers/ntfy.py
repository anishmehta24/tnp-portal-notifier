"""ntfy.sh push notifier. No account needed: pick a hard-to-guess topic, the
script POSTs to it, you + friends subscribe in the ntfy app (or the web) to that
topic. Self-hostable too by pointing NTFY_SERVER at your own instance."""
import logging

import requests

import config
from .base import Notifier

log = logging.getLogger("notifiers.ntfy")


class NtfyNotifier(Notifier):
    name = "ntfy"

    def __init__(self):
        self.server = config.NTFY_SERVER.rstrip("/")
        self.topic = config.NTFY_TOPIC
        self.token = config.NTFY_TOKEN  # optional, for protected/self-hosted topics
        if not self.topic:
            raise RuntimeError("NTFY_TOPIC not set")

    def send(self, title: str, body: str, url: str = "") -> bool:
        headers = {"Title": title.encode("utf-8")}
        if url:
            # tapping the notification opens the portal item
            headers["Click"] = url
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        r = requests.post(
            f"{self.server}/{self.topic}",
            data=body.encode("utf-8"),
            headers=headers,
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return True
