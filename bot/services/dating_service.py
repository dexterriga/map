"""Dating module business logic."""

import logging
import secrets
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, not_

from bot.models import (
    User, DatingProfile, DatingPhoto, DatingPayment, DatingAccessPackage,
    DatingProfileView, DatingComplaint, DatingModerationLog,
    DatingProfileStatus, ModerationStatus
)

logger = logging.getLogger(__name__)

# ---- Config (overridable via admin) ----
DATING_CONFIG = {
    "package_price_stars": 10,
    "package_size": 5,
    "safe_mode": True,
    "max_photos": 3,
    "max_complaints_before_hide": 5,
    "allow_reshow": True,
    "reshow_threshold": 3,
}


def get_dating_config() -> dict:
    return dict(DATING_CONFIG)


def update_dating_config(**kwargs):
    for k, v in kwargs.items():
        if k in DATING_CONFIG:
            DATING_CONFIG[k] = v


# ---- Profile Management ----

def get_or_create_profile(db: Session, user: User) -> DatingProfile:
    profile = db.query(DatingProfile).filter(DatingProfile.user_id == user.id).first()
    if not profile:
        profile = DatingProfile(user_id=user.id, display_name=user.first_name)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def get_profile_by_user(db: Session, user: User) -> DatingProfile | None:
    return db.query(DatingProfile).filter(DatingProfile.user_id == user.id).first()


def get_active_profile_count(db: Session) -> int:
    return db.query(DatingProfile).filter(
        DatingProfile.status == DatingProfileStatus.ACTIVE.value
    ).count()


def create_profile_from_wizard(db: Session, user: User, data: dict) -> DatingProfile:
    profile = get_or_create_profile(db, user)
    profile.display_name = data.get("display_name", user.first_name)
    profile.gender = data.get("gender")
    profile.age = data.get("age")
    profile.bio = data.get("bio", "")
    profile.phone = data.get("phone", "")
    profile.city = data.get("city", "Daugavpils")
    profile.rules_accepted = True
    profile.status = DatingProfileStatus.PENDING_MODERATION.value
    db.commit()
    db.refresh(profile)

    _log_moderation(db, profile, None, "created",
                    "Анкета создана и отправлена на модерацию")

    return profile


def update_profile(db: Session, profile: DatingProfile, data: dict) -> DatingProfile:
    for key, val in data.items():
        if hasattr(profile, key):
            setattr(profile, key, val)
    profile.updated_at = datetime.utcnow()
    db.commit()
    return profile


def add_photo(db: Session, profile: DatingProfile, telegram_file_id: str) -> DatingPhoto | None:
    count = profile.photos.count()
    if count >= DATING_CONFIG["max_photos"]:
        return None
    photo = DatingPhoto(
        profile_id=profile.id,
        telegram_file_id=telegram_file_id,
        sort_order=count,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def remove_photo(db: Session, photo_id: int) -> bool:
    photo = db.query(DatingPhoto).filter(DatingPhoto.id == photo_id).first()
    if photo:
        db.delete(photo)
        db.commit()
        return True
    return False


def get_photos(db: Session, profile: DatingProfile) -> list[DatingPhoto]:
    return profile.photos.order_by(DatingPhoto.sort_order).all()


# ---- Moderation ----

def moderate_profile(db: Session, profile: DatingProfile,
                     moderator_id: int, new_status: str,
                     comment: str = "") -> DatingProfile:
    old_status = profile.status
    profile.status = new_status
    db.commit()

    _log_moderation(db, profile, moderator_id, f"{old_status}->{new_status}", comment)
    return profile


def _log_moderation(db: Session, profile: DatingProfile,
                    moderator_id: int | None, action: str, comment: str = ""):
    log = DatingModerationLog(
        profile_id=profile.id,
        moderator_id=moderator_id,
        action=action,
        comment=comment,
    )
    db.add(log)
    db.commit()


# ---- Payments ----

def create_payment_record(db: Session, profile: DatingProfile,
                          telegram_user_id: int, amount_stars: int,
                          package_size: int, invoice_payload: str) -> DatingPayment:
    payment = DatingPayment(
        profile_id=profile.id,
        telegram_user_id=telegram_user_id,
        amount_stars=amount_stars,
        package_size=package_size,
        status="pending",
        invoice_payload=invoice_payload,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_payment(db: Session, invoice_payload: str,
                    telegram_payment_charge_id: str,
                    provider_charge_id: str) -> DatingAccessPackage | None:
    payment = db.query(DatingPayment).filter(
        DatingPayment.invoice_payload == invoice_payload,
        DatingPayment.status == "pending",
    ).first()
    if not payment:
        logger.warning(f"Payment {invoice_payload} not found or already processed")
        existing = db.query(DatingPayment).filter(
            DatingPayment.invoice_payload == invoice_payload
        ).first()
        if existing and existing.status == "completed":
            existing_pkg = db.query(DatingAccessPackage).filter(
                DatingAccessPackage.payment_id == existing.id
            ).first()
            return existing_pkg
        return None

    payment.status = "completed"
    payment.telegram_payment_charge_id = telegram_payment_charge_id
    payment.provider_charge_id = provider_charge_id
    db.commit()

    pkg = DatingAccessPackage(
        payment_id=payment.id,
        profile_id=payment.profile_id,
        total_views=payment.package_size,
        used_views=0,
        status="active",
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)

    logger.info(f"Package {pkg.id} activated for profile {payment.profile_id}")
    return pkg


def get_active_package(db: Session, profile: DatingProfile) -> DatingAccessPackage | None:
    return db.query(DatingAccessPackage).filter(
        DatingAccessPackage.profile_id == profile.id,
        DatingAccessPackage.status == "active",
        DatingAccessPackage.used_views < DatingAccessPackage.total_views,
    ).first()


def get_payment_history(db: Session, profile: DatingProfile) -> list[DatingPayment]:
    return profile.payments.order_by(desc(DatingPayment.created_at)).all()


def get_package_history(db: Session, profile: DatingProfile) -> list[DatingAccessPackage]:
    return profile.packages.order_by(desc(DatingAccessPackage.activated_at)).all()


# ---- Profile Viewing ----

def get_profiles_for_viewer(db: Session, viewer_profile: DatingProfile) -> list[DatingProfile]:
    config = get_dating_config()
    pkg = get_active_package(db, viewer_profile)
    if not pkg:
        return []

    target_gender = "female" if viewer_profile.gender == "male" else "male"

    already_viewed_ids = db.query(DatingProfileView.target_profile_id).filter(
        DatingProfileView.viewer_profile_id == viewer_profile.id
    ).subquery()

    candidates = db.query(DatingProfile).filter(
        DatingProfile.id != viewer_profile.id,
        DatingProfile.status == DatingProfileStatus.ACTIVE.value,
        DatingProfile.gender == target_gender,
        not_(DatingProfile.id.in_(already_viewed_ids)),
    ).order_by(DatingProfile.created_at.desc()).limit(pkg.total_views - pkg.used_views).all()

    remaining = (pkg.total_views - pkg.used_views) - len(candidates)
    if remaining > 0 and config.get("allow_reshow", True):
        reshows = db.query(DatingProfile).filter(
            DatingProfile.id != viewer_profile.id,
            DatingProfile.status == DatingProfileStatus.ACTIVE.value,
            DatingProfile.gender == target_gender,
        ).order_by(DatingProfile.created_at.desc()).limit(remaining).all()
        candidates.extend(reshows)

    for target in candidates:
        view = DatingProfileView(
            package_id=pkg.id,
            viewer_profile_id=viewer_profile.id,
            target_profile_id=target.id,
        )
        db.add(view)
        pkg.used_views += 1
        db.commit()

    if pkg.used_views >= pkg.total_views:
        pkg.status = "exhausted"
        db.commit()

    return candidates


def get_view_history(db: Session, profile: DatingProfile) -> list[DatingProfileView]:
    return profile.profile_views.order_by(desc(DatingProfileView.shown_at)).all()


# ---- Complaints ----

def file_complaint(db: Session, target_profile: DatingProfile,
                   reporter_telegram_id: int, reason: str) -> DatingComplaint:
    complaint = DatingComplaint(
        target_profile_id=target_profile.id,
        reporter_telegram_user_id=reporter_telegram_id,
        reason=reason,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    target_profile.complaint_count = db.query(DatingComplaint).filter(
        DatingComplaint.target_profile_id == target_profile.id
    ).count()

    if target_profile.complaint_count >= DATING_CONFIG["max_complaints_before_hide"]:
        target_profile.status = DatingProfileStatus.BLOCKED.value
        _log_moderation(db, target_profile, None, "auto_blocked",
                        f"Авто-блокировка: {target_profile.complaint_count} жалоб")
    db.commit()

    return complaint


# ---- Admin ----

def get_all_profiles(db: Session, status_filter: str = None,
                     gender_filter: str = None,
                     offset: int = 0, limit: int = 20) -> list[DatingProfile]:
    q = db.query(DatingProfile)
    if status_filter:
        q = q.filter(DatingProfile.status == status_filter)
    if gender_filter:
        q = q.filter(DatingProfile.gender == gender_filter)
    return q.order_by(desc(DatingProfile.created_at)).offset(offset).limit(limit).all()


def get_all_complaints(db: Session) -> list[DatingComplaint]:
    return db.query(DatingComplaint).order_by(desc(DatingComplaint.created_at)).all()


def get_moderation_logs(db: Session, profile_id: int = None) -> list[DatingModerationLog]:
    q = db.query(DatingModerationLog)
    if profile_id:
        q = q.filter(DatingModerationLog.profile_id == profile_id)
    return q.order_by(desc(DatingModerationLog.created_at)).limit(50).all()
