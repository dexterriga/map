"""
Party Map Daugavpils Telegram Bot — Main Entry Point
=====================================================
Telegram bot for Daugavpils nightlife: events, loyalty, booking, DJ mixes.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram.ext import ApplicationBuilder, CommandHandler
from bot.config import BOT_TOKEN, LOG_LEVEL, LOG_FILE
from bot.database import init_db, SessionLocal


def setup_logging():
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def register_all_handlers(application):
    """Register all bot handlers."""
    from bot.handlers import (
        start, events, profile, bonuses, referrals,
        specialists, booking, dj_mixes, dj_register, admin, rss, tickets, bar_admin, dating, feed
    )
    # dj_register must be before start so ConversationHandler catches reply keyboard buttons
    dj_register.register(application)
    start.register(application)
    # tickets must be before events so event_ticket_buy_ is caught by tickets handler
    tickets.register(application)
    events.register(application)
    profile.register(application)
    bonuses.register(application)
    referrals.register(application)
    specialists.register(application)
    booking.register(application)
    dj_mixes.register(application)
    admin.register(application)
    rss.register(application)
    bar_admin.register(application)
    dating.register(application)
    feed.register(application)


async def post_init(application):
    """Run after bot initialization."""
    logging.info("Party Map Daugavpils Bot started!")
    logging.info(f"Bot username: {application.bot.username}")

    # Schedule cleanup of past events
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from bot.services.event_service import cleanup_past_events

    scheduler = AsyncIOScheduler()
    
    async def cleanup_job():
        db = SessionLocal()
        try:
            count = cleanup_past_events(db)
            if count > 0:
                logging.info(f"Cleaned up {count} past events")
        finally:
            db.close()

    scheduler.add_job(cleanup_job, "interval", hours=1, id="event_cleanup")
    scheduler.add_job(cleanup_job, "cron", hour=3, minute=0, id="event_cleanup_daily")
    scheduler.start()
    logging.info("Scheduler started for event cleanup")


async def error_handler(update, context):
    """Global error handler."""
    logging.error(f"Update {update} caused error {context.error}")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("ERROR: BOT_TOKEN not set! Create .env file from .env.example")
        print("Get your token from @BotFather")
        sys.exit(1)

    setup_logging()
    logging.info("Initializing database...")
    init_db()
    logging.info("Database initialized.")

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .get_updates_connection_pool_size(1)
        .get_updates_pool_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )

    application.add_error_handler(error_handler)
    register_all_handlers(application)

    logging.info("Starting polling...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
