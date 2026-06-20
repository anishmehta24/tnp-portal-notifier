"""Pure change detection: given freshly scraped items and the set of uids we've
already stored, return only the genuinely new ones. No side effects -> easy to test."""
import database


def find_new(table: str, items: list) -> list:
    """items: list of Notification/Company. Returns those whose uid is unseen."""
    seen = database.known_uids(table)
    fresh = [it for it in items if it.uid not in seen]
    # de-dupe within this batch too (portal occasionally repeats a row)
    out, batch_seen = [], set()
    for it in fresh:
        if it.uid not in batch_seen:
            batch_seen.add(it.uid)
            out.append(it)
    return out
