"""Specialists catalog handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.helpers import escape_markdown
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
            if not spec:
                await query.edit_message_text(
                    "😕 Специалист не найден / Speciālists nav atrasts",
                    reply_markup=back_keyboard("menu_specialists"),
                )
                return
            name = escape_markdown(spec.stage_name or spec.name or "")
            spec_cat = escape_markdown(spec.category or "")
            city = escape_markdown(spec.city or "")
            exp_str = str(spec.experience_years or "—")
            specialization = escape_markdown(spec.specialization or "")
            desc_raw = spec.description_lv if lang == "lv" and spec.description_lv else spec.description
            description = escape_markdown(desc_raw or "")
            price = f"{int(spec.price_from)}" if spec.price_from and spec.price_from == int(spec.price_from) else str(spec.price_from) if spec.price_from else "—"
            contacts = escape_markdown(spec.contacts or "")
            instagram = f"📸 Instagram: {escape_markdown(spec.instagram)}" if spec.instagram else ""
            website = f"🌐 Сайт: {escape_markdown(spec.website)}" if spec.website else ""
            extras = "\n".join(filter(None, [instagram, website]))
            card_text = (
                f"🎭 *{name}*\n\n"
                f"Категория: {spec_cat}\n"
                f"📍 {city}\n"
                f"⭐ Опыт: {exp_str} лет\n"
                f"🔧 {specialization}\n\n"
                f"{description}\n\n"
                f"💰 Цена от: {price} EUR\n"
                f"📞 {contacts}\n"
                f"{extras}"
            )
            try:
                await query.edit_message_text(
                    card_text, parse_mode="Markdown",
                    reply_markup=specialist_detail_keyboard(spec_id, spec.photo_url),
                )
            except Exception:
                await query.edit_message_text(
                    card_text, parse_mode=None,
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
