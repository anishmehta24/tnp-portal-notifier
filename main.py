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
import scraper


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


def deliver(table: str):
    """Phase-1 stub: 'send' every pending row by logging it, then mark notified.
    Replace the print with a real notifier.send() and only mark on success."""
    pending = database.pending_notifications(table)
    if not pending:
        return
    log.info("Delivering %d pending %s", len(pending), table)
    delivered = []
    for row in pending:
        title = row.get("title") or row.get("name")
        print(f"  [{table}] NEW -> {title}  ({row.get('posted_at') or row.get('posted_on')})")
        delivered.append(row["uid"])
    database.mark_notified(table, delivered)


def run_cycle():
    log.info("=== cycle start ===")
    database.init_db()
    session = auth.get_session()
    session = auth.ensure_logged_in(session)

    companies = scraper.scrape_companies(session)
    notifications = scraper.scrape_notifications(session)

    new_companies = detector.find_new("companies", companies)
    new_notifs = detector.find_new("notifications", notifications)
    log.info("New: %d companies, %d notifications",
             len(new_companies), len(new_notifs))

    database.insert("companies", [c.as_row() for c in new_companies])
    database.insert("notifications", [n.as_row() for n in new_notifs])

    deliver("companies")
    deliver("notifications")
    log.info("=== cycle done ===")


if __name__ == "__main__":
    setup_logging()
    try:
        run_cycle()
    except Exception:
        log.exception("Cycle failed")
        raise
