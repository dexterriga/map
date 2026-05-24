"""RBAC middleware for role-based access control."""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User
from bot.utils.helpers import has_permission


def require_role(role: str):
    """Decorator to require a minimum role for a handler."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_tg = update.effective_user
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_tg.id).first()
                if not user or not has_permission(user.role, role):
                    await update.message.reply_text(
                        "🚫 У тебя нет прав для этого действия.\n"
                        "🚫 Tev nav tiesību šai darbībai."
                    )
                    return
                return await func(update, context)
            finally:
                db.close()
        return wrapper
    return decorator
