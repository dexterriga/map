"""Configuration for Party Map Daugavpils Bot."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Database
_db_dir = BASE_DIR / "data"
_db_dir.mkdir(parents=True, exist_ok=True)
_db_path = (_db_dir / "party_map.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")

# File storage
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# RSS
RSS_FETCH_INTERVAL_MINUTES = int(os.getenv("RSS_FETCH_INTERVAL_MINUTES", "30"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "data" / "bot.log"))

# Points
POINTS = {
    "REGISTRATION": 50,
    "DJ_REGISTRATION": 100,
    "DJ_UPLOAD_MIX": 50,
    "VISIT_PARTY": 30,
    "TICKET_PURCHASE": 50,
    "BAR_ORDER_20": 20,
    "REFERRAL": 40,
    "BIRTHDAY_WEEK_MULTIPLIER": 2.0,
    "BAR_EARN_PER_EUR": 2,  # points earned per 1 EUR spent at bar
}

# Rewards
REWARDS = {
    "free_entry": {"points": 100, "title_ru": "Бесплатный вход", "title_lv": "Bezmaksas ieeja"},
    "cocktail_discount": {"points": 150, "title_ru": "Коктейль со скидкой", "title_lv": "Kokteilis ar atlaidi"},
    "two_free_shots": {"points": 250, "title_ru": "2 Free Shots", "title_lv": "2 bezmaksas šoti"},
    "concert_ticket": {"points": 400, "title_ru": "Билет на концерт", "title_lv": "Biļete uz koncertu"},
    "vip_bonus": {"points": 600, "title_ru": "VIP-бонус / депозит", "title_lv": "VIP bonuss / depozīts"},
}

# Roles
ROLES = {
    "user": 0,
    "dj_performer": 1,
    "specialist": 1,
    "bar_admin": 2,
    "moderator": 2,
    "admin": 3,
    "super_admin": 4,
}

ROLE_NAMES_RU = {
    "user": "Пользователь",
    "dj_performer": "DJ / Исполнитель",
    "specialist": "Специалист",
    "bar_admin": "Bar Admin",
    "moderator": "Модератор",
    "admin": "Администратор",
    "super_admin": "Super Admin",
}

ROLE_NAMES_LV = {
    "user": "Lietotājs",
    "dj_performer": "DJ / Izpildītājs",
    "specialist": "Speciālists",
    "bar_admin": "Bar Admin",
    "moderator": "Moderators",
    "admin": "Administrators",
    "super_admin": "Super Admin",
}

# Bot username
BOT_USERNAME = "@mapdaugavpilsbot"

# Languages
LANGUAGES = {"ru": "Русский", "lv": "Latviešu"}
