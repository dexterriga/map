"""Input validators for forms."""

import re
from datetime import datetime


def validate_phone(phone: str) -> tuple[bool, str]:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if re.match(r"^\+?\d{7,15}$", cleaned):
        return True, cleaned
    return False, "Неверный номер телефона / Nekorekts tālruņa numurs"


def validate_name(name: str) -> tuple[bool, str]:
    if 2 <= len(name.strip()) <= 100:
        return True, name.strip()
    return False, "Имя должно быть от 2 до 100 символов / Vārdam jābūt 2–100 simboliem"


def validate_date(date_str: str) -> tuple[bool, datetime | None]:
    formats = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return True, dt
        except ValueError:
            continue
    return False, None


def validate_budget(budget_str: str) -> tuple[bool, float | None]:
    try:
        budget = float(budget_str.replace(",", ".").strip())
        if budget >= 0:
            return True, budget
    except ValueError:
        pass
    return False, None
