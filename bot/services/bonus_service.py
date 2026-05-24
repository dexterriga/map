"""Points and rewards service."""

from datetime import datetime
from sqlalchemy.orm import Session
from bot.models import User, Transaction, Reward, RewardRedemption, PointsLog
from bot.config import POINTS, REWARDS


def award_points(db: Session, user: User, amount: int, description: str,
                 description_lv: str = "", reference_type: str = None,
                 reference_id: int = None, admin_id: int = None) -> Transaction:
    multiplier = POINTS.get("BIRTHDAY_WEEK_MULTIPLIER", 1.0) if user.is_birthday_week else 1.0
    final_amount = int(amount * multiplier)

    if multiplier > 1.0:
        description += f" (x{multiplier} — день рождения!)"
        description_lv += f" (x{multiplier} — dzimšanas diena!)"

    user.points_balance += final_amount
    user.total_earned += final_amount
    user.last_activity = datetime.utcnow()

    txn = Transaction(
        user_id=user.id,
        type="earn",
        amount=final_amount,
        balance_after=user.points_balance,
        description=description,
        description_lv=description_lv,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(txn)

    if admin_id:
        log = PointsLog(
            user_id=user.id,
            admin_id=admin_id,
            amount=final_amount,
            type="earn",
            reason=description,
        )
        db.add(log)

    db.commit()
    db.refresh(txn)
    return txn


def deduct_points(db: Session, user: User, amount: int, description: str,
                  description_lv: str = "", admin_id: int = None) -> Transaction:
    if user.points_balance < amount:
        raise ValueError("Insufficient points")

    user.points_balance -= amount
    user.total_spent += amount
    user.last_activity = datetime.utcnow()

    txn = Transaction(
        user_id=user.id,
        type="spend",
        amount=amount,
        balance_after=user.points_balance,
        description=description,
        description_lv=description_lv,
    )
    db.add(txn)

    if admin_id:
        log = PointsLog(
            user_id=user.id,
            admin_id=admin_id,
            amount=amount,
            type="spend",
            reason=description,
        )
        db.add(log)

    db.commit()
    db.refresh(txn)
    return txn


def redeem_reward(db: Session, user: User, reward: Reward) -> RewardRedemption:
    if user.points_balance < reward.points_required:
        raise ValueError("Not enough points")

    deduct_points(db, user, reward.points_required,
                  f"Активация: {reward.title_ru}",
                  f"Aktivizācija: {reward.title_lv}")

    redemption = RewardRedemption(
        user_id=user.id,
        reward_id=reward.id,
        points_spent=reward.points_required,
        status="approved",
        completed_at=datetime.utcnow(),
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption


def get_available_rewards(db: Session) -> list[Reward]:
    return db.query(Reward).filter(Reward.is_active == True).all()


def get_user_transactions(db: Session, user: User, limit: int = 20) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_redemptions(db: Session, user: User) -> list[RewardRedemption]:
    return (
        db.query(RewardRedemption)
        .filter(RewardRedemption.user_id == user.id)
        .order_by(RewardRedemption.redeemed_at.desc())
        .all()
    )
