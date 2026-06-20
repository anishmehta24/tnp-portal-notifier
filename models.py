"""Typed records for scraped items. The portal already gives each item a stable
hash in its URL (job/notice/<hash> or job/info/<hash>); we use that as the unique
id and fall back to a content hash only if a row has no link."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict


def _content_hash(*parts: str) -> str:
    raw = "|".join(p.strip() for p in parts if p)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class Notification:
    uid: str          # portal hash or content hash
    title: str
    category: str     # e.g. "Job Update"
    description: str
    posted_at: str    # ISO-ish "2026/06/19 07:29:28"
    url: str

    @classmethod
    def build(cls, uid, title, category, description, posted_at, url):
        uid = uid or _content_hash(title, posted_at)
        return cls(uid, title, category, description, posted_at, url)

    def as_row(self) -> dict:
        return asdict(self)

    def format_alert(self) -> str:
        return (
            f"\U0001F4E2 *{self.title}*\n"
            f"{self.description}\n"
            f"_{self.category} • {self.posted_at}_\n"
            f"{self.url}"
        )


@dataclass(frozen=True)
class Company:
    uid: str
    name: str
    deadline: str     # ISO "2026/02/04"
    posted_on: str
    url: str

    @classmethod
    def build(cls, uid, name, deadline, posted_on, url):
        uid = uid or _content_hash(name, posted_on)
        return cls(uid, name, deadline, posted_on, url)

    def as_row(self) -> dict:
        return asdict(self)

    def format_alert(self) -> str:
        return (
            f"\U0001F3E2 *New company: {self.name}*\n"
            f"Apply by: {self.deadline}\n"
            f"Posted: {self.posted_on}\n"
            f"{self.url}"
        )
