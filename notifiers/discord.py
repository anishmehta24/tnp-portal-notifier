"""Discord webhook notifier. Create a webhook in a channel
(Channel Settings -> Integrations -> Webhooks) and put its URL in DISCORD_WEBHOOK_URL.
Friends in that channel get the alerts."""
import logging

import requests

import config
from .base import Notifier

log = logging.getLogger("notifiers.discord")


class DiscordNotifier(Notifier):
    name = "discord"

    def __init__(self):
        self.url = config.DISCORD_WEBHOOK_URL
        if not self.url:
            raise RuntimeError("DISCORD_WEBHOOK_URL not set")

    def send(self, title: str, body: str, url: str = "") -> bool:
        # Discord renders markdown; body already contains the formatted alert.
        content = body if len(body) <= 1900 else body[:1900] + "..."
        r = requests.post(
            self.url,
            json={"content": content, "flags": 4},  # 4 = suppress link embeds
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return True
