"""DJ/Specialist registration and portfolio form (conversation)."""

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ConversationHandler
)

from bot.database import SessionLocal
from bot.models import User, Specialist
from bot.keyboards.inline import back_keyboard
from bot.config import POINTS

# States
NAME, CATEGORY, DESCRIPTION, EXPERIENCE, PRICE, CONTACTS, PHOTO, CONFIRM = range(8)

CATEGORIES = ["DJ", "Producer", "MC", "Sound Engineer", "Light Designer"]

async def dj_register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Сначала используй /start")
            return ConversationHandler.END
        lang = user.language
    finally:
        db.close()

    context.user_data["dj_reg"] = {}
    text = (
        "🎧 *Регистрация DJ / специалиста*\n\n"
        "Шаг 1/6: Введи своё *сценическое имя* (или имя):" if lang == "ru"
        else "🎧 *DJ / speciālista reģistrācija*\n\n"
             "1/6: Ievadi savu *skatuves vārdu* (vai vārdu):"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["dj_reg"]["name"] = text
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    buttons = [[InlineKeyboardButton(cat, callback_data=f"dj_cat_{cat}")] for cat in CATEGORIES]
    await update.message.reply_text(
        f"✅ Имя: {text}\n\nШаг 2/6: Выбери *категорию*:" if lang == "ru"
        else f"✅ Vārds: {text}\n\n2/6: Izvēlies *kategoriju*:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return CATEGORY


async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("_")[2]
    context.user_data["dj_reg"]["category"] = category

    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    await query.edit_message_text(
        f"✅ Категория: {category}\n\nШаг 3/6: Напиши *о себе* (стиль, опыт, ссылки):" if lang == "ru"
        else f"✅ Kategorija: {category}\n\n3/6: Uzraksti *par sevi* (stils, pieredze, saites):",
        parse_mode="Markdown",
    )
    return DESCRIPTION


async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["dj_reg"]["description"] = text
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    await update.message.reply_text(
        f"✅ Описание сохранено.\n\nШаг 4/6: Сколько лет *опыта*? (число или 0):" if lang == "ru"
        else f"✅ Apraksts saglabāts.\n\n4/6: Cik gadu *pieredzes*? (skaitlis vai 0):",
        parse_mode="Markdown",
    )
    return EXPERIENCE


async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        exp = int(update.message.text.strip())
    except ValueError:
        exp = 0
    context.user_data["dj_reg"]["experience"] = exp
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    await update.message.reply_text(
        f"✅ Опыт: {exp} лет\n\nШаг 5/6: Цена *от* (EUR, число или 0):" if lang == "ru"
        else f"✅ Pieredze: {exp} gadi\n\n5/6: Cena *no* (EUR, skaitlis vai 0):",
        parse_mode="Markdown",
    )
    return PRICE


async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip().replace(",", "."))
    except ValueError:
        price = 0
    context.user_data["dj_reg"]["price"] = price
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    await update.message.reply_text(
        f"✅ Цена: от {price} EUR\n\nШаг 6/6: *Контакты* (телефон, Instagram, портфолио):" if lang == "ru"
        else f"✅ Cena: no {price} EUR\n\n6/6: *Kontakti* (tālrunis, Instagram, portfolio):",
        parse_mode="Markdown",
    )
    return CONTACTS


async def ask_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dj_reg"]["contacts"] = update.message.text.strip()
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    await update.message.reply_text(
        f"✅ Контакты сохранены.\n\nШаг 7/7: Отправь *фото* (не обязательно) или напиши «—» чтобы пропустить.\n\n"
        f"Ты можешь прикрепить фото как файл." if lang == "ru"
        else f"✅ Kontakti saglabāti.\n\n7/7: Nosūti *foto* (nav obligāti) vai uzraksti «—» lai izlaistu.\n\n"
             f"Vari pievienot foto kā failu.",
        parse_mode="Markdown",
    )
    return PHOTO


async def ask_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    photo_url = ""

    if update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        context.user_data["dj_reg"]["photo_url"] = photo_file.file_id
        await update.message.reply_text("✅ Фото получено!" if lang == "ru" else "✅ Foto saņemts!")
    elif update.message.document:
        doc = update.message.document
        if doc.mime_type and doc.mime_type.startswith("image/"):
            photo_file = await doc.get_file()
            context.user_data["dj_reg"]["photo_url"] = photo_file.file_id
            await update.message.reply_text("✅ Фото получено!" if lang == "ru" else "✅ Foto saņemts!")
        else:
            await update.message.reply_text(
                "Пожалуйста, отправь изображение или «—» чтобы пропустить." if lang == "ru"
                else "Lūdzu, nosūti attēlu vai «—» lai izlaistu."
            )
            return PHOTO
    else:
        text = update.message.text.strip()
        if text == "—" or text.lower() == "skip":
            context.user_data["dj_reg"]["photo_url"] = ""
        else:
            context.user_data["dj_reg"]["photo_url"] = text

    await show_confirmation(update, context)
    return CONFIRM


async def show_confirmation(update, context):
    data = context.user_data["dj_reg"]
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    photo_info = "\n🖼 Фото: есть" if data.get("photo_url") else "\n🖼 Фото: нет"
    summary = (
        f"🎧 *{'Подтверждение анкеты' if lang == 'ru' else 'Anketas apstiprinājums'}*\n\n"
        f"👤 Имя: {data.get('name', '—')}\n"
        f"🎭 Категория: {data.get('category', '—')}\n"
        f"📝 Описание: {data.get('description', '—')[:100]}\n"
        f"⭐ Опыт: {data.get('experience', 0)} лет\n"
        f"💰 Цена от: {data.get('price', 0)} EUR\n"
        f"📞 Контакты: {data.get('contacts', '—')}{photo_info}\n\n"
        f"{'Всё верно?' if lang == 'ru' else 'Viss pareizi?'}"
        if lang == "ru"
        else
        f"🎧 *Anketas apstiprinājums*\n\n"
        f"👤 Vārds: {data.get('name', '—')}\n"
        f"🎭 Kategorija: {data.get('category', '—')}\n"
        f"📝 Apraksts: {data.get('description', '—')[:100]}\n"
        f"⭐ Pieredze: {data.get('experience', 0)} gadi\n"
        f"💰 Cena no: {data.get('price', 0)} EUR\n"
        f"📞 Kontakti: {data.get('contacts', '—')}{photo_info}\n\n"
        f"Viss pareizi?"
    )
    buttons = [
        [InlineKeyboardButton("✅ Да / Jā", callback_data="dj_confirm_yes")],
        [InlineKeyboardButton("❌ Заново / No jauna", callback_data="dj_confirm_no")],
    ]
    await update.message.reply_text(
        summary, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "dj_confirm_no":
        context.user_data.pop("dj_reg", None)
        await query.edit_message_text("❌ Регистрация отменена. Начни заново через /djregister" if query.message.text else "Atcelts.")
        return ConversationHandler.END

    reg_data = context.user_data["dj_reg"]
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"

        specialist = Specialist(
            user_id=user.id,
            name=reg_data.get("name", ""),
            stage_name=reg_data.get("name", ""),
            category=reg_data.get("category", "DJ"),
            description=reg_data.get("description", ""),
            description_lv=reg_data.get("description", ""),
            experience_years=reg_data.get("experience", 0),
            price_from=float(reg_data.get("price", 0)),
            contacts=reg_data.get("contacts", ""),
            photo_url=reg_data.get("photo_url", ""),
            is_active=True,
            moderation_status="pending",
            created_by=user.telegram_id,
        )
        db.add(specialist)
        db.commit()

        # Update user role to DJ
        if user.role == "user":
            user.role = "dj_performer"
            db.commit()

        # Award bonus points for DJ registration
        from bot.services.bonus_service import award_points
        award_points(db, user, POINTS["DJ_REGISTRATION"],
                     "Регистрация DJ / специалиста",
                     "DJ / speciālista reģistrācija")

        context.user_data.pop("dj_reg", None)
        await query.edit_message_text(
            f"✅ *{'Анкета отправлена на модерацию!' if lang == 'ru' else 'Anketa nosūtīta moderācijai!'}*\n\n"
            f"{'После проверки ты появишься в каталоге специалистов.' if lang == 'ru' else 'Pēc pārbaudes tu parādīsies speciālistu katalogā.'}\n\n"
            f"💰 **+{POINTS['DJ_REGISTRATION']} pts** {'за регистрацию!' if lang == 'ru' else 'par reģistrāciju!'}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu_main"),
        )
    finally:
        db.close()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("dj_reg", None)
    await update.message.reply_text("❌ Отменено / Atcelts")
    return ConversationHandler.END


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("djregister", dj_register_start),
            MessageHandler(filters.Text("🎤 Стать DJ"), dj_register_start),
            MessageHandler(filters.Text("🎤 Kļūt par DJ"), dj_register_start),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            CATEGORY: [CallbackQueryHandler(ask_category, pattern=r"^dj_cat_")],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_description)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_price)],
            CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_contacts)],
            PHOTO: [
                MessageHandler(filters.PHOTO, ask_photo),
                MessageHandler(filters.Document.ALL, ask_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_photo),
            ],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^dj_confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="dj_registration",
        persistent=False,
    )


def register(application):
    application.add_handler(get_conversation_handler())
