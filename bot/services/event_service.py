"""Event management service."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from bot.models import Event, SavedEvent


def get_upcoming_events(db: Session, limit: int = 20, offset: int = 0) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.is_active == True, Event.date >= datetime.utcnow())
        .order_by(Event.date.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_event_by_id(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()


def get_featured_events(db: Session, limit: int = 5) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.is_active == True, Event.is_featured == True, Event.date >= datetime.utcnow())
        .order_by(Event.date.asc())
        .limit(limit)
        .all()
    )


def save_event_for_user(db: Session, user_id: int, event_id: int) -> SavedEvent:
    existing = (
        db.query(SavedEvent)
        .filter(SavedEvent.user_id == user_id, SavedEvent.event_id == event_id)
        .first()
    )
    if existing:
        return existing
    saved = SavedEvent(user_id=user_id, event_id=event_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def get_saved_events(db: Session, user_id: int) -> list[SavedEvent]:
    return (
        db.query(SavedEvent)
        .filter(SavedEvent.user_id == user_id)
        .order_by(SavedEvent.saved_at.desc())
        .all()
    )


def unsave_event(db: Session, user_id: int, event_id: int) -> bool:
    saved = (
        db.query(SavedEvent)
        .filter(SavedEvent.user_id == user_id, SavedEvent.event_id == event_id)
        .first()
    )
    if saved:
        db.delete(saved)
        db.commit()
        return True
    return False


def cleanup_past_events(db: Session) -> int:
    """Deactivate events whose date has passed (yesterday or earlier)."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=1)
    expired = (
        db.query(Event)
        .filter(Event.is_active == True, Event.date <= cutoff)
        .all()
    )
    count = 0
    for event in expired:
        event.is_active = False
        count += 1
    if count > 0:
        db.commit()
    return count
