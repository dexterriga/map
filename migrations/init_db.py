"""Initialize database and seed default data."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.database import init_db, SessionLocal
from bot.models import Reward
from bot.config import REWARDS


def seed_rewards():
    db = SessionLocal()
    try:
        existing = db.query(Reward).count()
        if existing > 0:
            print(f"Rewards already seeded: {existing}")
            return

        for key, data in REWARDS.items():
            reward = Reward(
                key=key,
                title_ru=data["title_ru"],
                title_lv=data["title_lv"],
                points_required=data["points"],
                is_active=True,
            )
            db.add(reward)
            print(f"  Added reward: {data['title_ru']} — {data['points']} pts")

        db.commit()
        print(f"Seeded {len(REWARDS)} rewards.")
    finally:
        db.close()


def main():
    print("Initializing database...")
    init_db()
    print("Database tables created.")

    print("Seeding default data...")
    seed_rewards()

    print("\nDone! Database ready.")


if __name__ == "__main__":
    main()
