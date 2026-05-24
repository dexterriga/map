"""Booking request service."""

from datetime import datetime
from sqlalchemy.orm import Session
from bot.models import BookingRequest, Specialist


def create_booking(db: Session, user_id: int, specialist_id: int | None,
                   client_name: str, event_date: datetime, phone: str = None,
                   telegram_username: str = None, event_type: str = None,
                   venue: str = None, comment: str = None,
                   budget: float = None, specialist_type: str = None) -> BookingRequest:
    booking = BookingRequest(
        user_id=user_id,
        specialist_id=specialist_id,
        specialist_type=specialist_type,
        client_name=client_name,
        phone=phone,
        telegram_username=telegram_username,
        event_date=event_date,
        event_type=event_type,
        venue=venue,
        comment=comment,
        budget=budget,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_user_bookings(db: Session, user_id: int) -> list[BookingRequest]:
    return (
        db.query(BookingRequest)
        .filter(BookingRequest.user_id == user_id)
        .order_by(BookingRequest.created_at.desc())
        .all()
    )


def get_all_bookings(db: Session, status: str = None, limit: int = 50) -> list[BookingRequest]:
    query = db.query(BookingRequest)
    if status:
        query = query.filter(BookingRequest.status == status)
    return query.order_by(BookingRequest.created_at.desc()).limit(limit).all()


def update_booking_status(db: Session, booking_id: int, status: str,
                          admin_note: str = None) -> BookingRequest | None:
    booking = db.query(BookingRequest).filter(BookingRequest.id == booking_id).first()
    if booking:
        booking.status = status
        if admin_note:
            booking.admin_note = admin_note
        booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)
    return booking


def get_specialists_for_category(db: Session, category: str) -> list[Specialist]:
    return (
        db.query(Specialist)
        .filter(Specialist.category.ilike(f"%{category}%"),
                Specialist.is_active == True)
        .all()
    )


def get_specialist_by_id(db: Session, spec_id: int) -> Specialist | None:
    return db.query(Specialist).filter(Specialist.id == spec_id).first()
