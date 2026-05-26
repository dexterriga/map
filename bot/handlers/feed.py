"""News feed handler — shows latest events, mixes, specialists, and admin posts."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy import desc

from bot.database import SessionLocal
from bot.models import User, FeedPost
from bot.keyboards.inline import back_keyboard


POST_ICONS = {
    "event": "📅",
    "mix": "🎧",
    "specialist": "🎭",
    "admin_post": "📢",
}


async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language

        page = context.user_data.get("feed_page", 0)
        posts = db.query(FeedPost).order_by(desc(FeedPost.created_at)).offset(page * 5).limit(5).all()

        if not posts:
            await update.message.reply_text(
                "📰 *Лента новостей*\n\nПока нет записей." if lang == "ru"
                else "📰 *Jaunumu lente*\n\nVēl nav ierakstu.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
                ]),
            )
            return

        text = "📰 *Лента новостей / Jaunumu lente*\n\n" if lang == "ru" else "📰 *Jaunumu lente*\n\n"
        for p in posts:
            icon = POST_ICONS.get(p.post_type, "📌")
            text += f"{icon} *{p.title}*\n{p.text_content or ''}\n\n"

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data="feed_page_prev"))
        if len(posts) >= 5:
            nav.append(InlineKeyboardButton("▶️", callback_data="feed_page_next"))
        buttons = [nav] if nav else []
        buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])

        await update.message.reply_text(
            text[:4000], parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    finally:
        db.close()


async def feed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "feed_page_next":
        context.user_data["feed_page"] = context.user_data.get("feed_page", 0) + 1
    elif data == "feed_page_prev":
        context.user_data["feed_page"] = max(0, context.user_data.get("feed_page", 0) - 1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language
        page = context.user_data.get("feed_page", 0)
        posts = db.query(FeedPost).order_by(desc(FeedPost.created_at)).offset(page * 5).limit(5).all()

        if not posts:
            await query.edit_message_text(
                "📰 *Лента новостей*\n\nПока нет записей." if lang == "ru"
                else "📰 *Jaunumu lente*\n\nVēl nav ierakstu.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
                ]),
            )
            return

        text = "📰 *Лента новостей / Jaunumu lente*\n\n" if lang == "ru" else "📰 *Jaunumu lente*\n\n"
        for p in posts:
            icon = POST_ICONS.get(p.post_type, "📌")
            text += f"{icon} *{p.title}*\n{p.text_content or ''}\n\n"

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data="feed_page_prev"))
        if len(posts) >= 5:
            nav.append(InlineKeyboardButton("▶️", callback_data="feed_page_next"))
        buttons = [nav] if nav else []
        buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])

        await query.edit_message_text(
            text[:4000], parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    finally:
        db.close()


def add_feed_post(db, post_type, title, text_content="", image_url="", link="", created_by=None, reference_id=None):
    """Helper to add a post to the feed."""
    post = FeedPost(
        post_type=post_type,
        reference_id=reference_id,
        title=title,
        text_content=text_content,
        image_url=image_url,
        link=link,
        created_by=created_by,
    )
    db.add(post)
    db.commit()


def register(application):
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CallbackQueryHandler(feed_callback, pattern=r"^feed_"))
