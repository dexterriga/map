"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from bot.config import DATABASE_URL

_is_postgres = DATABASE_URL.startswith("postgresql")

if _is_postgres:
    url = DATABASE_URL
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url += f"{sep}sslmode=require"
    engine = create_engine(url, echo=False, pool_pre_ping=True)
else:
    engine = create_engine(
        DATABASE_URL, echo=False,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from bot.models import (  # noqa: F401 – register all models
        User, Event, Specialist, BookingRequest,
        DjMix, MixListen, Transaction, Reward, RewardRedemption,
        Referral, RssSource, RssEntry, AuditLog, SavedEvent,
        Notification, AdminAction, PointsLog, EventBonus, SoldTicket,
        PointsQR
    )
    Base.metadata.create_all(bind=engine)
    _migrate_db()

    db = SessionLocal()
    try:
        _seed_rewards(db)
        _seed_events(db)
        _seed_specialists(db)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _migrate_db():
    """Add missing columns to existing tables (works with SQLite and PostgreSQL)."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    _is_pg = DATABASE_URL.startswith("postgresql")
    migrations = {
        "events": [
            ("ticket_url", "VARCHAR(1000)"),
            ("ticket_price_points", "INTEGER DEFAULT 0"),
            ("is_featured", "BOOLEAN DEFAULT false" if _is_pg else "BOOLEAN DEFAULT 0"),
            ("address", "VARCHAR(255)"),
        ],
        "dj_mixes": [
            ("audio_url", "VARCHAR(500)"),
        ],
        "users": [
            ("is_blocked", "BOOLEAN DEFAULT false" if _is_pg else "BOOLEAN DEFAULT 0"),
        ],
    }
    for table, columns in migrations.items():
        existing = {c["name"] for c in inspector.get_columns(table)}
        with engine.connect() as conn:
            for col_name, col_type in columns:
                if col_name not in existing:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                    ))
            conn.commit()


def _seed_rewards(db):
    from bot.models import Reward
    if db.query(Reward).count() > 0:
        return
    from bot.config import REWARDS
    for key, data in REWARDS.items():
        reward = Reward(
            key=key,
            title_ru=data["title_ru"],
            title_lv=data["title_lv"],
            points_required=data["points"],
            is_active=True,
        )
        db.add(reward)


def _seed_events(db):
    from bot.models import Event
    from datetime import datetime, timedelta
    if db.query(Event).count() > 0:
        return
    now = datetime.utcnow()
    events_data = [
        {
            "title": "Weekend Party",
            "title_lv": "Nedēļas nogales ballīte",
            "description": "Лучшие треки и танцы всю ночь!",
            "description_lv": "Labākie treki un dejas visu nakti!",
            "date": now + timedelta(days=7),
            "venue": "Club XO, Daugavpils",
            "price": 15.0,
            "category": "party",
        },
        {
            "title": "Live Concert: Rock Night",
            "title_lv": "Dzīvais koncerts: Roka nakts",
            "description": "Рок-группы со всего региона",
            "description_lv": "Roka grupas no visa reģiona",
            "date": now + timedelta(days=14),
            "venue": "Daugavpils Koncertzāle",
            "price": 25.0,
            "category": "concert",
        },
        {
            "title": "DJ Set: Electronic Vibes",
            "title_lv": "DJ sets: Elektroniskās vibrācijas",
            "description": "Лучшие электронные треки от местных DJ",
            "description_lv": "Labākie elektroniskie treki no vietējiem DJ",
            "date": now + timedelta(days=21),
            "venue": "Club XO, Daugavpils",
            "price": 10.0,
            "category": "party",
        },
    ]
    for ed in events_data:
        event = Event(**ed, is_active=True, moderation_status="approved")
        db.add(event)


def _seed_specialists(db):
    from bot.models import Specialist
    if db.query(Specialist).count() > 0:
        return
    specialists_data = [
        {
            "name": "DJ Alex",
            "stage_name": "DJ Alex",
            "category": "DJ",
            "description": "Опытный DJ, играет house, techno, electronic",
            "description_lv": "Pieredzējis DJ, spēlē house, techno, electronic",
            "experience_years": 5,
            "price_from": 200.0,
            "contacts": "@dj_alex",
            "is_active": True,
            "moderation_status": "approved",
        },
        {
            "name": "Jānis Bērziņš",
            "stage_name": "Jānis Foto",
            "category": "Фотограф / Fotogrāfs",
            "description": "Профессиональный фотограф для мероприятий",
            "description_lv": "Profesionāls fotogrāfs pasākumiem",
            "experience_years": 8,
            "price_from": 150.0,
            "contacts": "@janis_foto",
            "is_active": True,
            "moderation_status": "approved",
        },
    ]
    for sd in specialists_data:
        spec = Specialist(**sd)
        db.add(spec)
