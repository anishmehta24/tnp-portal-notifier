"""One full cycle: login -> scrape -> detect new -> store -> deliver.

Phase 1 'delivers' by printing/logging. The notifier is intentionally a stub so
the channel (Telegram / WhatsApp / etc.) can be plugged in later without touching
this orchestration. Order is store-first, then notify pending rows, so a delivery
failure is retried next cycle and an alert is never lost (never-miss-an-alert)."""
import logging
import logging.handlers
import sys

import auth
import config
import database
import detector
import notifiers
import scraper
from models import Company, Notification


def setup_logging():
    # Portal text contains non-cp1252 chars (e.g. U+202F); force UTF-8 output so
    # printing/logging never crashes on the Windows console.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fmt = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            config.LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        ),
    ]
    logging.basicConfig(level=config.LOG_LEVEL, format=fmt, handlers=handlers)


log = logging.getLogger("main")


_MODEL = {"notifications": Notification, "companies": Company}


def _row_to_item(table: str, row: dict):
    cls = _MODEL[table]
    fields = cls.__dataclass_fields__
    return cls(**{k: row[k] for k in fields})


def deliver(table: str, channels: list):
    """Send every pending row through all channels. Mark an item notified only
    when at least one channel accepted it, so failures retry next cycle."""
    pending = database.pending_notifications(table)
    if not pending:
        return
    log.info("Delivering %d pending %s via %s",
             len(pending), table, ", ".join(c.name for c in channels))
    delivered = []
    for row in pending:
        item = _row_to_item(table, row)
        if any(c.send_item(item) for c in channels):
            delivered.append(row["uid"])
    database.mark_notified(table, delivered)
    if len(delivered) < len(pending):
        log.warning("%d/%d %s not delivered -- will retry next cycle",
                    len(pending) - len(delivered), len(pending), table)


def run_cycle():
    log.info("=== cycle start ===")
    database.init_db()
    # On a brand-new DB (first run, or after cache loss on CI), record everything
    # currently on the portal as 'seen' without alerting, so we don't blast the
    # entire history. Genuinely new items from then on are alerted normally.
    fresh_db = config.SEED_ON_FIRST_RUN and not (
        database.known_uids("companies") or database.known_uids("notifications"))
    session = auth.get_session()
    session = auth.ensure_logged_in(session)

    index_html = scraper.fetch(session, config.INDEX_URL)
    companies = scraper.parse_companies(index_html)
    eligible = scraper.parse_eligible(index_html)
    notifications = scraper.scrape_notifications(session)

    new_companies = detector.find_new("companies", companies)
    new_notifs = detector.find_new("notifications", notifications)

    if config.ELIGIBLE_ONLY:
        before = len(new_companies)
        new_companies = [c for c in new_companies
                         if scraper.normalize_name(c.name) in eligible]
        if before != len(new_companies):
            log.info("Eligibility filter: %d -> %d new companies",
                     before, len(new_companies))

    log.info("New: %d companies, %d notifications",
             len(new_companies), len(new_notifs))

    database.insert("companies", [c.as_row() for c in new_companies])
    database.insert("notifications", [n.as_row() for n in new_notifs])

    if fresh_db:
        database.mark_notified("companies", [c.uid for c in new_companies])
        database.mark_notified("notifications", [n.uid for n in new_notifs])
        log.info("First run: recorded %d companies + %d notifications as seen "
                 "(no alerts sent)", len(new_companies), len(new_notifs))
    else:
        channels = notifiers.get_notifiers()
        deliver("companies", channels)
        deliver("notifications", channels)
    log.info("=== cycle done ===")


if __name__ == "__main__":
    setup_logging()
    import heartbeat
    try:
        run_cycle()
        heartbeat.success()
    except Exception:
        log.exception("Cycle failed")
        heartbeat.fail()
        raise
