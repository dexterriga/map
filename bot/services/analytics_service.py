"""Analytics service for admin dashboard."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from bot.models import User, Event, Transaction, Referral, DjMix, BookingRequest, RewardRedemption


def get_total_users(db: Session) -> int:
    return db.query(User).count()


def get_active_users(db: Session, days: int = 30) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return db.query(User).filter(User.last_activity >= cutoff).count()


def get_blocked_users(db: Session) -> int:
    return db.query(User).filter(User.is_blocked == True).count()


def get_total_points_earned(db: Session) -> int:
    result = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "earn").scalar()
    return result or 0


def get_total_points_spent(db: Session) -> int:
    result = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "spend").scalar()
    return result or 0


def get_total_referrals(db: Session) -> int:
    return db.query(Referral).count()


def get_upcoming_events_count(db: Session) -> int:
    return db.query(Event).filter(Event.date >= datetime.utcnow()).count()


def get_total_bookings(db: Session) -> int:
    return db.query(BookingRequest).count()


def get_pending_bookings(db: Session) -> int:
    return db.query(BookingRequest).filter(BookingRequest.status == "pending").count()


def get_top_mixes(db: Session, limit: int = 5) -> list[DjMix]:
    return db.query(DjMix).order_by(desc(DjMix.plays_count)).limit(limit).all()


def get_top_rewards(db: Session, limit: int = 5) -> list:
    result = (
        db.query(
            RewardRedemption.reward_id,
            func.count(RewardRedemption.id).label("count")
        )
        .group_by(RewardRedemption.reward_id)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return result


def get_registration_stats(db: Session, days: int = 30) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = (
        db.query(
            func.date(User.registered_at).label("date"),
            func.count(User.id).label("count")
        )
        .filter(User.registered_at >= cutoff)
        .group_by(func.date(User.registered_at))
        .order_by("date")
        .all()
    )
    return [{"date": r.date, "count": r.count} for r in results]
