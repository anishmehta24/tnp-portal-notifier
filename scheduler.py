"""Periodic runner. Executes one full cycle immediately, then every
POLL_INTERVAL_MIN minutes. Each run is wrapped so an exception (network blip,
portal hiccup) is logged and the loop keeps going -- crash-isolated.

Run:  python scheduler.py
Stop: Ctrl-C   (on a server, run under systemd / Task Scheduler -- see README)
"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
import heartbeat
import main

log = logging.getLogger("scheduler")


def safe_cycle():
    try:
        main.run_cycle()
        heartbeat.success()
    except Exception:
        log.exception("Cycle raised -- skipping this run, loop continues")
        heartbeat.fail()


def start():
    main.setup_logging()
    log.info("Scheduler starting: every %d min", config.POLL_INTERVAL_MIN)
    sched = BlockingScheduler(timezone="Asia/Kolkata")
    sched.add_job(
        safe_cycle,
        trigger=IntervalTrigger(minutes=config.POLL_INTERVAL_MIN),
        id="tnp_cycle",
        max_instances=1,        # never overlap a slow run with the next tick
        coalesce=True,          # if we fell behind, run once, not N times
        next_run_time=None,     # see manual first-run below
    )
    safe_cycle()                # run once now, before waiting for the first interval
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    start()
