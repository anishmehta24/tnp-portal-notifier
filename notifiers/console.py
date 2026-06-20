"""Console notifier — always-available fallback, used for local testing and as a
safety net so 'no channel configured' still surfaces alerts in the log."""
import logging

from .base import Notifier

log = logging.getLogger("notifiers.console")


class ConsoleNotifier(Notifier):
    name = "console"

    def send(self, title: str, body: str, url: str = "") -> bool:
        print(f"\n----- ALERT -----\n{body}\n-----------------")
        return True
