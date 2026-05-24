"""RSS feed fetching and parsing service."""

import feedparser
from datetime import datetime
from sqlalchemy.orm import Session
from bot.models import RssSource, RssEntry, Event
from bot.config import RSS_FETCH_INTERVAL_MINUTES


def fetch_rss_feed(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entries.append({
            "guid": entry.get("id", entry.get("link", "")),
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "content": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
            "published": _parse_date(entry.get("published_parsed")),
        })
    return entries


def _parse_date(struct_time) -> datetime | None:
    if struct_time:
        try:
            from time import mktime
            return datetime.fromtimestamp(mktime(struct_time))
        except Exception:
            pass
    return None


def import_rss_entries(db: Session, source: RssSource) -> int:
    try:
        entries_data = fetch_rss_feed(source.url)
    except Exception as e:
        print(f"RSS fetch error for {source.url}: {e}")
        return 0

    imported = 0
    for data in entries_data:
        existing = db.query(RssEntry).filter(RssEntry.guid == data["guid"]).first()
        if existing:
            continue

        entry = RssEntry(
            source_id=source.id,
            guid=data["guid"],
            title=data["title"],
            link=data["link"],
            summary=data["summary"],
            content=data["content"],
            published=data["published"],
            moderation_status="approved" if source.auto_publish else "pending",
        )
        db.add(entry)

        if source.auto_publish:
            _create_event_from_rss(db, entry, source)
            entry.imported_as_event_id = 1  # placeholder, will be updated

        imported += 1

    if imported:
        source.last_fetched = datetime.utcnow()
        db.commit()

    return imported


def _create_event_from_rss(db: Session, entry: RssEntry, source: RssSource) -> Event | None:
    if not entry.title:
        return None
    event = Event(
        title=entry.title,
        description=entry.summary or entry.content,
        date=entry.published or datetime.utcnow(),
        category=source.category,
        source_rss_id=source.id,
        moderation_status="approved" if source.auto_publish else "pending",
    )
    db.add(event)
    db.flush()
    entry.imported_as_event_id = event.id
    return event


def get_active_sources(db: Session) -> list[RssSource]:
    return db.query(RssSource).filter(RssSource.is_active == True).all()


def add_rss_source(db: Session, url: str, category: str = "news",
                   auto_publish: bool = False, created_by: int = None) -> RssSource:
    source = RssSource(
        url=url,
        category=category,
        auto_publish=auto_publish,
        created_by=created_by,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
