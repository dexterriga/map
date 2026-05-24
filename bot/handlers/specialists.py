"""Specialists catalog handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, Specialist
from bot.keyboards.inline import (
    specialist_categories_keyboard, specialists_keyboard,
    specialist_detail_keyboard, back_keyboard
)
from bot.services.booking_service import get_specialists_for_category, get_specialist_by_id


async def specialists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"

        await update.message.reply_text(
            "🎭 *Категории специалистов*\n\n"
            "Выбери категорию:" if lang == "ru"
            else "🎭 *Speciālistu kategorijas*\n\nIzvēlies kategoriju:",
            parse_mode="Markdown",
            reply_markup=specialist_categories_keyboard(lang),
        )
    finally:
        db.close()


async def specialists_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        lang = user.language if user else "ru"

        if data == "menu_specialists":
            await query.edit_message_text(
                "🎭 *Категории специалистов*\n\nВыбери категорию:" if lang == "ru"
                else "🎭 *Speciālistu kategorijas*\n\nIzvēlies kategoriju:",
                parse_mode="Markdown",
                reply_markup=specialist_categories_keyboard(lang),
            )
        elif data.startswith("spec_cat_"):
            category = data[9:]
            specs = get_specialists_for_category(db, category.split(" / ")[0])
            if not specs:
                await query.edit_message_text(
                    "😕 В этой категории пока нет специалистов." if lang == "ru"
                    else "😕 Šajā kategorijā vēl nav speciālistu.",
                    reply_markup=back_keyboard("menu_specialists"),
                )
                return
            await query.edit_message_text(
                f"🎭 *{category}*",
                parse_mode="Markdown",
                reply_markup=specialists_keyboard(specs, lang),
            )
        elif data.startswith("spec_"):
            spec_id = int(data.split("_")[1])
            spec = get_specialist_by_id(db, spec_id)
            if spec:
                desc = spec.description_lv if lang == "lv" and spec.description_lv else spec.description
                instagram = f"📸 Instagram: {spec.instagram}" if spec.instagram else ""
                website = f"🌐 Сайт: {spec.website}" if spec.website else ""
                photo = f"🖼 [Фото / Foto]({spec.photo_url})" if spec.photo_url else ""
                extras = "\n".join(filter(None, [instagram, website, photo]))
                text = (
                    f"🎭 *{spec.stage_name or spec.name}*\n\n"
                    f"Категория: {spec.category}\n"
                    f"📍 {spec.city or '—'}\n"
                    f"⭐ Опыт: {spec.experience_years or '—'} лет\n"
                    f"🔧 {spec.specialization or '—'}\n\n"
                    f"{desc or ''}\n\n"
                    f"💰 Цена от: {spec.price_from or '—'} EUR\n"
                    f"📞 {spec.contacts or '—'}\n"
                    f"{extras}"
                )
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=specialist_detail_keyboard(spec_id, spec.photo_url),
                )
        elif data.startswith("book_"):
            spec_id = int(data.split("_")[1])
            from bot.services.booking_service import get_specialist_by_id
            spec = get_specialist_by_id(db, spec_id)
            if spec:
                context.user_data["booking_specialist_id"] = spec_id
                context.user_data["booking_specialist_type"] = spec.category
            await _ask_name(update, context, lang)
        elif data.startswith("request_"):
            spec_id = int(data.split("_")[1])
            spec = get_specialist_by_id(db, spec_id)
            if spec:
                context.user_data["booking_specialist_id"] = spec_id
                context.user_data["booking_specialist_type"] = spec.category
                await _ask_name(update, context, lang)
    finally:
        db.close()


async def _ask_name(update, context, lang):
    query = update.callback_query
    await query.edit_message_text(
        "📝 *Заявка на бронирование*\n\nШаг 1/5: Введи своё имя:" if lang == "ru"
        else "📝 *Rezervācijas pieteikums*\n\n1/5: Ievadi savu vārdu:",
        parse_mode="Markdown",
    )
    context.user_data["booking_step"] = "name"


def register(application):
    application.add_handler(CommandHandler("specialists", specialists))
    application.add_handler(CallbackQueryHandler(specialists_callback, pattern=r"^(menu_specialists|spec_|book_|request_)"))
