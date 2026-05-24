"""Referral system service."""

from sqlalchemy.orm import Session
from bot.models import User, Referral
from bot.config import POINTS
from bot.services.bonus_service import award_points


def create_referral(db: Session, referrer_id: int, referred_id: int) -> Referral:
    referral = Referral(
        referrer_id=referrer_id,
        referred_id=referred_id,
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


def process_referral_bonus(db: Session, referrer: User, referred: User) -> None:
    referral = (
        db.query(Referral)
        .filter(Referral.referred_id == referred.id, Referral.referrer_id == referrer.id)
        .first()
    )
    if referral and not referral.bonus_given:
        award_points(
            db, referrer, POINTS["REFERRAL"],
            "Бонус за приглашение друга",
            "Bonuss par drauga uzaicināšanu",
            reference_type="referral",
            reference_id=referral.id,
        )
        referral.bonus_given = True
        referral.bonus_amount = POINTS["REFERRAL"]
        db.commit()


def get_referrals(db: Session, user: User) -> list[Referral]:
    return (
        db.query(Referral)
        .filter(Referral.referrer_id == user.id)
        .order_by(Referral.created_at.desc())
        .all()
    )


def count_referrals(db: Session, user: User) -> int:
    return db.query(Referral).filter(Referral.referrer_id == user.id).count()


def get_referral_by_code(db: Session, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).first()
