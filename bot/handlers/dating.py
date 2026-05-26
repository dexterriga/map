"""Dating profile handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.inline import back_keyboard


async def dating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"

        if user and user.dating_photo:
            caption = (
                f"💕 *{'Твой профиль знакомств' if lang == 'ru' else 'Tavs iepazīšanās profils'}*\n\n"
                f"{user.dating_bio or ('—' if lang == 'ru' else '—')}"
            )
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=user.dating_photo,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=__dating_keyboard(lang),
            )
        else:
            text = (
                "💕 *Знакомства*\n\n"
                "У тебя ещё нет профиля знакомств.\n"
                "Отправь своё *фото* и *несколько слов о себе*, чтобы другие могли тебя найти!"
                if lang == "ru"
                else "💕 *Iepazīšanās*\n\n"
                     "Tev vēl nav iepazīšanās profila.\n"
                     "Nosūti savu *foto* un *dažus vārdus par sevi*, lai citi tevi var atrast!"
            )
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=__dating_keyboard(lang))
    finally:
        db.close()


def __dating_keyboard(lang):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        [InlineKeyboardButton("📤 Загрузить фото / Augšupielādēt foto", callback_data="dating_upload_photo")],
        [InlineKeyboardButton("✏️ Редактировать bio / Rediģēt bio", callback_data="dating_edit_bio")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


async def dating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"

        if data == "dating_upload_photo":
            context.user_data["dating_awaiting_photo"] = True
            await query.edit_message_text(
                "📤 Отправь своё *фото* для профиля знакомств."
                if lang == "ru"
                else "📤 Nosūti savu *foto* iepazīšanās profilam.",
                parse_mode="Markdown",
            )
        elif data == "dating_edit_bio":
            context.user_data["dating_awaiting_bio"] = True
            await query.edit_message_text(
                "✏️ Напиши *несколько слов о себе* (или отправь «—» чтобы удалить bio)."
                if lang == "ru"
                else "✏️ Uzraksti *dažus vārdus par sevi* (vai nosūti «—» lai dzēstu bio).",
                parse_mode="Markdown",
            )
    finally:
        db.close()


async def handle_dating_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("dating_awaiting_photo"):
        return
    if not update.message.photo:
        return
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language or "ru"
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        user.dating_photo = photo_file.file_id
        db.commit()
        context.user_data.pop("dating_awaiting_photo", None)
        await update.message.reply_text(
            "✅ Фото загружено! Твой профиль знакомств обновлён."
            if lang == "ru"
            else "✅ Foto augšupielādēts! Tavs iepazīšanās profils atjaunināts.",
        )
    finally:
        db.close()


async def handle_dating_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("dating_awaiting_bio"):
        return
    if update.message.photo:
        return
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language or "ru"
        text = update.message.text.strip()
        if text == "—":
            user.dating_bio = None
        else:
            user.dating_bio = text
        db.commit()
        context.user_data.pop("dating_awaiting_bio", None)
        await update.message.reply_text(
            "✅ Bio обновлён!" if lang == "ru" else "✅ Bio atjaunināts!",
        )
    finally:
        db.close()


def register(application):
    application.add_handler(CallbackQueryHandler(dating_callback, pattern=r"^dating_"))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_dating_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dating_bio))
