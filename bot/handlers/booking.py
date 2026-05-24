"""Booking request form handlers (conversation)."""

from telegram import Update
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ConversationHandler
)
from datetime import datetime

from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.inline import back_keyboard, confirm_keyboard
from bot.services.booking_service import create_booking
from bot.utils.validators import validate_name, validate_phone, validate_date, validate_budget

# Conversation states
(
    NAME, PHONE, EVENT_DATE, EVENT_TYPE, VENUE,
    COMMENT, BUDGET, CONFIRM
) = range(8)


async def ask_name(query, lang: str):
    await query.edit_message_text(
        "📝 *Заявка на бронирование*\n\nШаг 1/6: Введи своё имя:" if lang == "ru"
        else "📝 *Rezervācijas pieteikums*\n\n1/6: Ievadi savu vārdu:",
        parse_mode="Markdown",
    )
    return NAME


async def booking_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    is_valid, result = validate_name(text)
    if not is_valid:
        await update.message.reply_text(result)
        return NAME
    context.user_data["booking_client_name"] = result
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    await update.message.reply_text(
        f"✅ Имя: {result}\n\nШаг 2/6: Введи номер телефона (или /skip):" if lang == "ru"
        else f"✅ Vārds: {result}\n\n2/6: Ievadi tālruņa numuru (vai /skip):",
    )
    return PHONE


async def booking_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    is_valid, result = validate_phone(text)
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    if not is_valid:
        context.user_data["booking_phone"] = None
    else:
        context.user_data["booking_phone"] = result
    await update.message.reply_text(
        f"Шаг 3/6: Введи дату мероприятия (ДД.ММ.ГГГГ):" if lang == "ru"
        else f"3/6: Ievadi pasākuma datumu (DD.MM.GGGG):",
    )
    return EVENT_DATE


async def booking_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    is_valid, result = validate_date(text)
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    if not is_valid:
        await update.message.reply_text(
            "❌ Неверный формат даты. Используй ДД.ММ.ГГГГ" if lang == "ru"
            else "❌ Nepareizs datuma formāts. Izmanto DD.MM.GGGG",
        )
        return EVENT_DATE
    context.user_data["booking_event_date"] = result
    await update.message.reply_text(
        f"✅ Дата: {result.strftime('%d.%m.%Y')}\n\nШаг 4/6: Тип мероприятия (или /skip):" if lang == "ru"
        else f"✅ Datums: {result.strftime('%d.%m.%Y')}\n\n4/6: Pasākuma veids (vai /skip):",
    )
    return EVENT_TYPE


async def booking_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["booking_event_type"] = text if text != "/skip" else None
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    await update.message.reply_text(
        f"Шаг 5/6: Место проведения (или /skip):" if lang == "ru"
        else f"5/6: Norises vieta (vai /skip):",
    )
    return VENUE


async def booking_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["booking_venue"] = text if text != "/skip" else None
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()
    await update.message.reply_text(
        f"Шаг 6/6: Комментарий или бюджет (или /skip):" if lang == "ru"
        else f"6/6: Komentārs vai budžets (vai /skip):",
    )
    return COMMENT


async def booking_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["booking_comment"] = text if text != "/skip" else None
    await show_booking_confirmation(update, context)
    return CONFIRM


async def show_booking_confirmation(update, context):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
    finally:
        db.close()

    data = context.user_data
    summary = (
        f"📝 *{'Подтверждение заявки' if lang == 'ru' else 'Pieteikuma apstiprinājums'}*\n\n"
        f"👤 {'Имя' if lang == 'ru' else 'Vārds'}: {data.get('booking_client_name')}\n"
        f"📞 {'Телефон' if lang == 'ru' else 'Tālrunis'}: {data.get('booking_phone', '—')}\n"
        f"📅 {'Дата' if lang == 'ru' else 'Datums'}: {data.get('booking_event_date').strftime('%d.%m.%Y') if data.get('booking_event_date') else '—'}\n"
        f"🎉 {'Тип' if lang == 'ru' else 'Veids'}: {data.get('booking_event_type', '—')}\n"
        f"📍 {'Место' if lang == 'ru' else 'Vieta'}: {data.get('booking_venue', '—')}\n"
        f"💬 {'Комментарий' if lang == 'ru' else 'Komentārs'}: {data.get('booking_comment', '—')}\n\n"
        f"{'Всё верно?' if lang == 'ru' else 'Viss pareizi?'}"
    )
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=confirm_keyboard("booking", "save"),
    )


async def booking_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_tg = update.effective_user
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"

        if data == "confirm_booking_save":
            bd = context.user_data
            booking = create_booking(
                db=db,
                user_id=user.id,
                specialist_id=bd.get("booking_specialist_id"),
                specialist_type=bd.get("booking_specialist_type"),
                client_name=bd.get("booking_client_name", ""),
                event_date=bd.get("booking_event_date", datetime.utcnow()),
                phone=bd.get("booking_phone"),
                telegram_username=user_tg.username,
                event_type=bd.get("booking_event_type"),
                venue=bd.get("booking_venue"),
                comment=bd.get("booking_comment"),
            )
            context.user_data.clear()
            await query.edit_message_text(
                f"✅ *{'Заявка отправлена!' if lang == 'ru' else 'Pieteikums nosūtīts!'}*\n\n"
                f"{'Номер заявки' if lang == 'ru' else 'Pieteikuma nr.'}: #{booking.id}\n"
                f"{'Мы свяжемся с тобой в ближайшее время.' if lang == 'ru' else 'Mēs ar tevi sazināsimies tuvākajā laikā.'}",
                parse_mode="Markdown",
                reply_markup=back_keyboard("menu_main"),
            )
        elif data == "cancel_booking":
            context.user_data.clear()
            await query.edit_message_text(
                "❌ Заявка отменена." if lang == "ru" else "❌ Pieteikums atcelts.",
                reply_markup=back_keyboard("menu_main"),
            )
    finally:
        db.close()
    return ConversationHandler.END


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await booking_phone(update, context) if context.user_data.get("booking_step") == "phone" else None


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено / Atcelts")
    return ConversationHandler.END


async def bookings_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Сначала используй /start")
            return
        lang = user.language
        from bot.services.booking_service import get_user_bookings
        bookings = get_user_bookings(db, user.id)
        if not bookings:
            await update.message.reply_text(
                "📭 Нет заявок на бронирование." if lang == "ru"
                else "📭 Nav rezervācijas pieteikumu.",
                reply_markup=back_keyboard("menu_main"),
            )
            return
        lines = ["📋 *Мои заявки / Mani pieteikumi*:\n"]
        statuses = {
            "pending": "⏳", "approved": "✅", "rejected": "❌", "cancelled": "🚫"
        }
        for b in bookings:
            emoji = statuses.get(b.status, "❓")
            lines.append(f"{emoji} #{b.id} — {b.event_date.strftime('%d.%m.%Y')} — {b.client_name}")
        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=back_keyboard("menu_main"),
        )
    finally:
        db.close()


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: ask_name(u.callback_query, "ru"),
                                 pattern=r"^request_"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_name)],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, booking_phone),
                CommandHandler("skip", booking_phone),
            ],
            EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_date)],
            EVENT_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, booking_event_type),
                CommandHandler("skip", booking_event_type),
            ],
            VENUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, booking_venue),
                CommandHandler("skip", booking_venue),
            ],
            COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, booking_comment),
                CommandHandler("skip", booking_comment),
            ],
            CONFIRM: [
                CallbackQueryHandler(booking_confirm, pattern=r"^(confirm_booking|cancel_booking)"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="booking_conversation",
        persistent=False,
    )


def register(application):
    application.add_handler(CommandHandler("bookings", bookings_list))
    application.add_handler(get_conversation_handler())
