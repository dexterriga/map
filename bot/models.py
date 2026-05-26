"""Database models for Party Map Daugavpils Bot."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum, BigInteger
)
from sqlalchemy.orm import relationship
from bot.database import Base
import enum


# ---------- Enums ----------
class UserRole(str, enum.Enum):
    USER = "user"
    DJ_PERFORMER = "dj_performer"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TransactionType(str, enum.Enum):
    EARN = "earn"
    SPEND = "spend"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    HIDDEN = "hidden"


class RssCategory(str, enum.Enum):
    NEWS = "news"
    AFISHA = "afisha"
    CONCERTS = "concerts"
    FESTIVALS = "festivals"
    CITY_EVENTS = "city_events"


# ---------- User ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(20), default=UserRole.USER.value)
    city = Column(String(100), default="Daugavpils")
    language = Column(String(5), default="ru")
    points_balance = Column(Integer, default=0)
    total_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    is_birthday_week = Column(Boolean, default=False)
    birthday = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    dating_photo = Column(String(500), nullable=True)
    dating_bio = Column(Text, nullable=True)
    dating_gender = Column(String(10), nullable=True)
    dating_age = Column(Integer, nullable=True)
    dating_interests = Column(String(500), nullable=True)
    dating_is_active = Column(Boolean, default=False)

    transactions = relationship("Transaction", back_populates="user", lazy="dynamic")
    referrals_given = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer", lazy="dynamic")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred", lazy="dynamic")
    bookings = relationship("BookingRequest", back_populates="user", lazy="dynamic")
    saved_events = relationship("SavedEvent", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    admin_actions = relationship("AdminAction", back_populates="admin", lazy="dynamic")
    points_log = relationship("PointsLog", back_populates="user", lazy="dynamic")
    mix_listens = relationship("MixListen", back_populates="user", lazy="dynamic")
    redemptions = relationship("RewardRedemption", back_populates="user", lazy="dynamic")
    tickets = relationship("SoldTicket", back_populates="user", lazy="dynamic")


# ---------- Events ----------
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    title_lv = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    description_lv = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    venue = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    price = Column(Float, default=0)
    price_lv = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
    ticket_url = Column(String(1000), nullable=True)
    ticket_price_points = Column(Integer, default=0)
    category = Column(String(100), default="party")
    tags = Column(String(500), nullable=True)
    promo_code = Column(String(50), nullable=True)
    points_bonus = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    moderation_status = Column(String(20), default=ModerationStatus.APPROVED.value)
    source_rss_id = Column(Integer, ForeignKey("rss_sources.id"), nullable=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rss_source = relationship("RssSource", back_populates="events")
    bonuses = relationship("EventBonus", back_populates="event", lazy="dynamic")


class EventBonus(Base):
    __tablename__ = "event_bonuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    bonus_type = Column(String(50))
    bonus_description = Column(String(500))
    bonus_value = Column(String(100))

    event = relationship("Event", back_populates="bonuses")


# ---------- Transactions (Points) ----------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(10), default=TransactionType.EARN.value)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    description_lv = Column(String(500), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


# ---------- Rewards ----------
class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    title_ru = Column(String(255), nullable=False)
    title_lv = Column(String(255), nullable=False)
    description_ru = Column(Text, nullable=True)
    description_lv = Column(Text, nullable=True)
    points_required = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    status = Column(String(20), default=RequestStatus.PENDING.value)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="redemptions")
    reward = relationship("Reward")


# ---------- Referrals ----------
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bonus_given = Column(Boolean, default=False)
    bonus_amount = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_given")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")


# ---------- Specialists ----------
class Specialist(Base):
    __tablename__ = "specialists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    stage_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)
    city = Column(String(100), default="Daugavpils")
    description = Column(Text, nullable=True)
    description_lv = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    specialization = Column(String(500), nullable=True)
    price_from = Column(Float, nullable=True)
    currency = Column(String(10), default="EUR")
    contacts = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    instagram = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    moderation_status = Column(String(20), default=ModerationStatus.PENDING.value)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("BookingRequest", back_populates="specialist", lazy="dynamic")


# ---------- Booking Requests ----------
class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specialist_id = Column(Integer, ForeignKey("specialists.id"), nullable=True)
    specialist_type = Column(String(100), nullable=True)
    client_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    telegram_username = Column(String(255), nullable=True)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String(255), nullable=True)
    venue = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(String(20), default=RequestStatus.PENDING.value)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    specialist = relationship("Specialist", back_populates="bookings")


# ---------- DJ Mixes ----------
class DjMix(Base):
    __tablename__ = "dj_mixes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    artist_name = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    description_lv = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    audio_file_path = Column(String(500), nullable=True)
    external_link = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    plays_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    moderation_status = Column(String(20), default=ModerationStatus.PENDING.value)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listens = relationship("MixListen", back_populates="mix", lazy="dynamic")


class MixListen(Base):
    __tablename__ = "mix_listens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mix_id = Column(Integer, ForeignKey("dj_mixes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    listened_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50), nullable=True)

    mix = relationship("DjMix", back_populates="listens")
    user = relationship("User", back_populates="mix_listens")


# ---------- RSS ----------
class RssSource(Base):
    __tablename__ = "rss_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1000), nullable=False, unique=True)
    title = Column(String(500), nullable=True)
    category = Column(String(50), default=RssCategory.NEWS.value)
    auto_publish = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime, nullable=True)
    fetch_interval_minutes = Column(Integer, default=30)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="rss_source", lazy="dynamic")
    entries = relationship("RssEntry", back_populates="source", lazy="dynamic")


class RssEntry(Base):
    __tablename__ = "rss_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("rss_sources.id"), nullable=False)
    guid = Column(String(1000), unique=True, nullable=False)
    title = Column(String(1000), nullable=False)
    link = Column(String(2000), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published = Column(DateTime, nullable=True)
    imported_as_event_id = Column(Integer, nullable=True)
    moderation_status = Column(String(20), default=ModerationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("RssSource", back_populates="entries")


# ---------- Saved Events ----------
class SavedEvent(Base):
    __tablename__ = "saved_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    event_data = Column(JSON, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_events")


# ---------- Notifications ----------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), default="info")
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


# ---------- Points Log (for admin auditing) ----------
class PointsLog(Base):
    __tablename__ = "points_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    admin_id = Column(BigInteger, nullable=True)
    amount = Column(Integer, nullable=False)
    type = Column(String(10), default="earn")
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="points_log")


# ---------- Audit Log ----------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(BigInteger, nullable=True, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- Admin Actions ----------
class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(100), nullable=False)
    target_user_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User", back_populates="admin_actions")


# ---------- Sold Tickets ----------
class SoldTicket(Base):
    __tablename__ = "sold_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    unique_code = Column(String(30), unique=True, nullable=False, index=True)
    points_spent = Column(Integer, default=0)
    price_paid = Column(Float, default=0)
    is_used = Column(Boolean, default=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tickets")
    event = relationship("Event")


# ---------- Points QR ----------
class PointsQR(Base):
    __tablename__ = "points_qr"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # "use" or "earn"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bar_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    bar_admin = relationship("User", foreign_keys=[bar_admin_id])


# ---------- Feed / News ----------
class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_type = Column(String(50), nullable=False)  # event / mix / specialist / admin_post
    reference_id = Column(Integer, nullable=True)
    title = Column(String(500), nullable=False)
    text_content = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- Dating ----------
class DatingLike(Base):
    __tablename__ = "dating_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_like = Column(Boolean, default=True)
    is_match = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatingMessage(Base):
    __tablename__ = "dating_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- New Dating Module Entities ----------

class DatingProfileStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_MODERATION = "pending_moderation"
    ACTIVE = "active"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    DELETED = "deleted"


class DatingProfile(Base):
    __tablename__ = "dating_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    city = Column(String(100), default="Daugavpils")
    status = Column(String(20), default=DatingProfileStatus.DRAFT.value)
    rules_accepted = Column(Boolean, default=False)
    complaint_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="dating_profile", uselist=False)
    photos = relationship("DatingPhoto", back_populates="profile", lazy="dynamic",
                          cascade="all, delete-orphan",
                          order_by="DatingPhoto.sort_order")
    payments = relationship("DatingPayment", back_populates="profile", lazy="dynamic")
    packages = relationship("DatingAccessPackage", back_populates="profile", lazy="dynamic")
    profile_views = relationship("DatingProfileView",
                                  foreign_keys="DatingProfileView.target_profile_id",
                                  back_populates="target_profile", lazy="dynamic")
    complaints_received = relationship("DatingComplaint",
                                        foreign_keys="DatingComplaint.target_profile_id",
                                        back_populates="target_profile", lazy="dynamic")
    moderation_logs = relationship("DatingModerationLog",
                                    back_populates="profile", lazy="dynamic")


class DatingPhoto(Base):
    __tablename__ = "dating_photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False, index=True)
    telegram_file_id = Column(String(500), nullable=False)
    moderation_status = Column(String(20), default=ModerationStatus.APPROVED.value)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("DatingProfile", back_populates="photos")


class DatingPayment(Base):
    __tablename__ = "dating_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False, index=True)
    telegram_user_id = Column(BigInteger, nullable=False)
    amount_stars = Column(Integer, nullable=False)
    package_size = Column(Integer, default=5)
    status = Column(String(20), default="pending")
    invoice_payload = Column(String(255), unique=True, nullable=True, index=True)
    telegram_payment_charge_id = Column(String(255), nullable=True)
    provider_charge_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("DatingProfile", back_populates="payments")
    package = relationship("DatingAccessPackage", uselist=False, back_populates="payment")


class DatingAccessPackage(Base):
    __tablename__ = "dating_access_packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("dating_payments.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False, index=True)
    total_views = Column(Integer, default=5)
    used_views = Column(Integer, default=0)
    status = Column(String(20), default="active")
    activated_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)

    payment = relationship("DatingPayment", back_populates="package")
    profile = relationship("DatingProfile", back_populates="packages")
    views = relationship("DatingProfileView", back_populates="package", lazy="dynamic")


class DatingProfileView(Base):
    __tablename__ = "dating_profile_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey("dating_access_packages.id"), nullable=False)
    viewer_profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False)
    target_profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False)
    shown_at = Column(DateTime, default=datetime.utcnow)

    package = relationship("DatingAccessPackage", back_populates="views")
    viewer_profile = relationship("DatingProfile", foreign_keys=[viewer_profile_id])
    target_profile = relationship("DatingProfile", foreign_keys=[target_profile_id],
                                   back_populates="profile_views")


class DatingComplaint(Base):
    __tablename__ = "dating_complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False, index=True)
    reporter_telegram_user_id = Column(BigInteger, nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    target_profile = relationship("DatingProfile", foreign_keys=[target_profile_id],
                                   back_populates="complaints_received")


class DatingModerationLog(Base):
    __tablename__ = "dating_moderation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("dating_profiles.id"), nullable=False)
    moderator_id = Column(BigInteger, nullable=True)
    action = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("DatingProfile", back_populates="moderation_logs")
