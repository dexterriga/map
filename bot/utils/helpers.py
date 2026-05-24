"""Helper utilities."""

import re
from datetime import datetime
from bot.config import ROLES, POINTS, BOT_USERNAME


def get_role_level(role: str) -> int:
    return ROLES.get(role, 0)


def has_permission(user_role: str, required_role: str) -> bool:
    return get_role_level(user_role) >= get_role_level(required_role)


def generate_referral_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME.lstrip('@')}?start=ref_{user_id}"


def parse_referral(start_param: str) -> int | None:
    match = re.match(r"ref_(\d+)", start_param or "")
    return int(match.group(1)) if match else None


def format_date(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y")


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def format_price(price: float | None) -> str:
    if price is None or price == 0:
        return "Бесплатно / Free"
    return f"{price:.2f} EUR"


def truncate(text: str, max_len: int = 100) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^\+?[\d\s\-()]{7,20}$", phone))


def validate_name(name: str) -> bool:
    return bool(re.match(r"^[а-яА-ЯёЁa-zA-Z\s\-]{2,100}$", name))
