"""Fetch + parse the two server-rendered tables. All HTML knowledge lives here,
so a portal redesign only touches this file.

  /index.html  -> table#job-listings   (companies: name, deadline, posted, link)
  /newsevents  -> table#newsevents      (notifications: title, category, date, link)
"""
import logging
import re
import time

import requests
from bs4 import BeautifulSoup

import config
from models import Company, Notification

log = logging.getLogger(__name__)

_HASH_RE = re.compile(r"/(?:notice|info)/([0-9a-fA-F]+)")


def _extract_hash(href: str | None) -> str | None:
    if not href:
        return None
    m = _HASH_RE.search(href)
    return m.group(1) if m else None


def _abs_url(href: str | None) -> str:
    if not href:
        return config.INDEX_URL
    return href if href.startswith("http") else f"{config.BASE_URL}/{href.lstrip('/')}"


def fetch(session: requests.Session, url: str) -> str:
    """GET with simple exponential-backoff retry."""
    last = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=config.REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last = e
            wait = config.RETRY_BACKOFF ** attempt
            log.warning("fetch %s failed (try %d/%d): %s -- retry in %ds",
                        url, attempt, config.MAX_RETRIES, e, wait)
            time.sleep(wait)
    raise last


def parse_companies(html: str) -> list[Company]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tr in soup.select("#job-listings tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        name = tds[0].get_text(strip=True)
        deadline = tds[1].get("data-order") or tds[1].get_text(strip=True)
        posted = tds[2].get("data-order") or tds[2].get_text(strip=True)
        link = tr.find("a", href=_HASH_RE)
        uid = _extract_hash(link["href"]) if link else None
        url = _abs_url(link["href"]) if link else config.INDEX_URL
        if name:
            out.append(Company.build(uid, name, deadline, posted, url))
    log.info("Parsed %d companies", len(out))
    return out


def parse_notifications(html: str) -> list[Notification]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tr in soup.select("#newsevents tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        a = tr.find("h6")
        a = a.find("a") if a else None
        if not a:
            continue
        title = a.get_text(strip=True)
        uid = _extract_hash(a.get("href"))
        url = _abs_url(a.get("href"))
        desc_el = tds[0].find("p")
        cat_el = tds[0].find("b")
        description = desc_el.get_text(strip=True) if desc_el else ""
        category = cat_el.get_text(strip=True) if cat_el else ""
        posted_at = tds[-1].get("data-order") or tds[-1].get_text(strip=True)
        out.append(Notification.build(uid, title, category, description, posted_at, url))
    log.info("Parsed %d notifications", len(out))
    return out


def normalize_name(name: str) -> str:
    """Loose key for matching a company across the listing and the eligible modal."""
    return re.sub(r"\s+", " ", (name or "").strip()).casefold().rstrip(".")


def parse_eligible(html: str) -> set[str]:
    """The 'Eligible: N' button opens #eligibleModal, whose body lists the
    companies the logged-in student is eligible for, one per <li>."""
    soup = BeautifulSoup(html, "html.parser")
    modal = soup.find(id="eligibleModal")
    if not modal:
        log.warning("eligibleModal not found -- eligibility filter unavailable")
        return set()
    names = {normalize_name(li.get_text(strip=True))
             for li in modal.select(".modal-body li") if li.get_text(strip=True)}
    log.info("Eligible companies (%d): %s", len(names), ", ".join(sorted(names)))
    return names


def scrape_companies(session) -> list[Company]:
    return parse_companies(fetch(session, config.INDEX_URL))


def scrape_notifications(session) -> list[Notification]:
    return parse_notifications(fetch(session, config.NEWSEVENTS_URL))
