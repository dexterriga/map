"""RSS management and auto-publishing handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, RssSource
from bot.config import RSS_FETCH_INTERVAL_MINUTES
from bot.services.rss_service import add_rss_source, import_rss_entries, get_active_sources
from bot.keyboards.inline import back_keyboard
from bot.utils.helpers import has_permission


async def add_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new RSS source. Usage: /addrss <url> [category] [auto_publish]"""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not has_permission(user.role, "admin"):
            await update.message.reply_text("🚫 Только для администраторов.")
            return
        lang = user.language

        args = context.args
        if not args:
            await update.message.reply_text(
                "📰 *Добавление RSS*\n\n"
                "Использование:\n"
                "`/addrss <url> [категория] [авто]`\n\n"
                "Категории: news, afisha, concerts, festivals, city_events\n"
                "Авто: yes / no (автопубликация без модерации)\n\n"
                "Пример:\n"
                "`/addrss https://example.com/rss afisha yes`"
                if lang == "ru" else
                "📰 *RSS pievienošana*\n\n"
                "Lietošana:\n"
                "`/addrss <url> [kategorija] [auto]`\n\n"
                "Kategorijas: news, afisha, concerts, festivals, city_events\n"
                "Auto: yes / no (automātiska publicēšana bez moderācijas)\n\n"
                "Piemērs:\n"
                "`/addrss https://example.com/rss afisha yes`",
                parse_mode="Markdown",
            )
            return

        url = args[0]
        category = args[1] if len(args) > 1 else "news"
        auto_publish = len(args) > 2 and args[2].lower() in ("yes", "true", "1")

        if category not in ("news", "afisha", "concerts", "festivals", "city_events"):
            await update.message.reply_text(
                "❌ Неверная категория. Доступны: news, afisha, concerts, festivals, city_events"
                if lang == "ru" else
                "❌ Nepareiza kategorija. Pieejamas: news, afisha, concerts, festivals, city_events"
            )
            return

        source = add_rss_source(db, url, category, auto_publish, user.telegram_id)

        # Try to import immediately
        count = import_rss_entries(db, source)

        await update.message.reply_text(
            f"✅ RSS-источник добавлен!\n"
            f"URL: {url}\n"
            f"Категория: {category}\n"
            f"Автопубликация: {'да' if auto_publish else 'нет'}\n"
            f"Импортировано записей: {count}"
            if lang == "ru" else
            f"✅ RSS avots pievienots!\n"
            f"URL: {url}\n"
            f"Kategorija: {category}\n"
            f"Automātiskā publicēšana: {'jā' if auto_publish else 'nē'}\n"
            f"Importēti ieraksti: {count}",
        )
    finally:
        db.close()


async def list_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all RSS sources."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not has_permission(user.role, "admin"):
            await update.message.reply_text("🚫 Только для администраторов.")
            return
        lang = user.language

        sources = db.query(RssSource).all()
        if not sources:
            await update.message.reply_text(
                "📰 Нет RSS-источников." if lang == "ru" else "📰 Nav RSS avotu."
            )
            return

        lines = ["📰 *RSS Источники / Avoti:*\n"]
        for s in sources:
            status = "✅" if s.is_active else "❌"
            last_fetch = s.last_fetched.strftime("%d.%m.%Y") if s.last_fetched else "—"
            lines.append(f"{status} {s.title or s.url[:50]}")
            lines.append(f"   Категория: {s.category}, Последний: {last_fetch}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


async def fetch_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger RSS fetch for all sources."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not has_permission(user.role, "admin"):
            await update.message.reply_text("🚫 Только для администраторов.")
            return
        lang = user.language

        sources = get_active_sources(db)
        total = 0
        for source in sources:
            count = import_rss_entries(db, source)
            total += count

        await update.message.reply_text(
            f"✅ RSS импорт завершён. Импортировано: {total} записей."
            if lang == "ru" else
            f"✅ RSS imports pabeigts. Importēti: {total} ieraksti."
        )
    finally:
        db.close()


async def remove_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove RSS source. Usage: /removerss <id>"""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not has_permission(user.role, "admin"):
            await update.message.reply_text("🚫 Только для администраторов.")
            return

        args = context.args
        if not args:
            await update.message.reply_text("Использование: /removerss <id>")
            return

        source_id = int(args[0])
        source = db.query(RssSource).filter(RssSource.id == source_id).first()
        if not source:
            await update.message.reply_text("❌ Источник не найден.")
            return

        source.is_active = False
        db.commit()
        await update.message.reply_text(f"✅ RSS-источник #{source_id} отключён.")
    finally:
        db.close()


async def moderate_rss_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for moderating RSS entries."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("rss_approve_"):
        entry_id = int(data.split("_")[2])
        db = SessionLocal()
        try:
            from bot.models import RssEntry
            entry = db.query(RssEntry).filter(RssEntry.id == entry_id).first()
            if entry:
                entry.moderation_status = "approved"
                from bot.services.rss_service import _create_event_from_rss
                source = db.query(RssSource).filter(RssSource.id == entry.source_id).first()
                if source:
                    _create_event_from_rss(db, entry, source)
                db.commit()
                await query.edit_message_text(f"✅ Запись одобрена: {entry.title[:50]}")
        finally:
            db.close()
    elif data.startswith("rss_reject_"):
        entry_id = int(data.split("_")[2])
        db = SessionLocal()
        try:
            from bot.models import RssEntry
            entry = db.query(RssEntry).filter(RssEntry.id == entry_id).first()
            if entry:
                entry.moderation_status = "rejected"
                db.commit()
                await query.edit_message_text(f"❌ Запись отклонена: {entry.title[:50]}")
        finally:
            db.close()


def register(application):
    application.add_handler(CommandHandler("addrss", add_rss))
    application.add_handler(CommandHandler("listrss", list_rss))
    application.add_handler(CommandHandler("fetchrss", fetch_rss))
    application.add_handler(CommandHandler("removerss", remove_rss))
    application.add_handler(CallbackQueryHandler(moderate_rss_callback, pattern=r"^rss_"))
