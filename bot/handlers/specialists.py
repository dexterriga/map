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

        if lang == "ru":
            text = (
                "🎭 *Специалисты*\n\n"
                "Здесь ты можешь найти DJ, фотографов, ведущих и других\n"
                "специалистов для твоего мероприятия.\n\n"
                "👇 Выбери категорию:\n\n"
                "— *Хочешь стать специалистом?*\n"
                "Нажми «🎤 Я – специалист» в главном меню или используй /djregister,\n"
                "заполни анкету и после модерации ты появишься в каталоге!"
            )
        else:
            text = (
                "🎭 *Speciālisti*\n\n"
                "Šeit tu vari atrast DJ, fotogrāfus, vadītājus un citus\n"
                "speciālistus savam pasākumam.\n\n"
                "👇 Izvēlies kategoriju:\n\n"
                "— *Vēlies kļūt par speciālistu?*\n"
                "Nospied «🎤 Es esmu speciālists» galvenajā izvēlnē vai izmanto /djregister,\n"
                "aizpildi anketu un pēc moderācijas tu parādīsies katalogā!"
            )
        await update.message.reply_text(
            text, parse_mode="Markdown",
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

            def _esc(t):
                import re
                if not t:
                    return "—"
                # Escape MarkdownV2 special characters
                return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(t))

            name = _esc(spec.stage_name or spec.name)
            spec_cat = _esc(spec.category)
            city = _esc(spec.city)
            exp_str = str(spec.experience_years or "—")
            specialization = _esc(spec.specialization)
            desc_raw = spec.description_lv if lang == "lv" and spec.description_lv else spec.description
            description = _esc(desc_raw)
            price_val = int(spec.price_from) if spec.price_from and spec.price_from == int(spec.price_from) else spec.price_from
            price = str(price_val) if price_val else "—"
            contacts = _esc(spec.contacts)
            instagram = f"📸 Instagram: {_esc(spec.instagram)}" if spec.instagram else ""
            website = f"🌐 Vietne: {_esc(spec.website)}" if spec.website else ""
            extras = "\n".join(filter(None, [instagram, website]))
            cat_label = "Категория" if lang == "ru" else "Kategorija"
            exp_label = "Опыт" if lang == "ru" else "Pieredze"
            years_label = "лет" if lang == "ru" else "gadi"
            price_label = "Цена от" if lang == "ru" else "Cena no"
            site_label = "Сайт" if lang == "ru" else "Vietne"
            website = f"🌐 {site_label}: {_esc(spec.website)}" if spec.website else ""
            extras = "\n".join(filter(None, [instagram, website]))
            card_text = (
                f"🎭 *{name}*\n\n"
                f"{cat_label}: {spec_cat}\n"
                f"📍 {city}\n"
                f"⭐ {exp_label}: {exp_str} {years_label}\n"
                f"🔧 {specialization}\n\n"
                f"{description}\n\n"
                f"💰 {price_label}: {price} EUR\n"
                f"📞 {contacts}\n"
                f"{extras}"
            )
            try:
                if spec.photo_url:
                    await query.message.delete()
                    await query.message.chat.send_photo(
                        photo=spec.photo_url,
                        caption=card_text,
                        parse_mode="MarkdownV2",
                        reply_markup=specialist_detail_keyboard(spec_id),
                    )
                else:
                    await query.edit_message_text(
                        card_text, parse_mode="MarkdownV2",
                        reply_markup=specialist_detail_keyboard(spec_id),
                    )
            except Exception:
                try:
                    if spec.photo_url:
                        await query.message.delete()
                        await query.message.chat.send_photo(
                            photo=spec.photo_url, caption=card_text,
                            parse_mode=None,
                            reply_markup=specialist_detail_keyboard(spec_id),
                        )
                    else:
                        await query.edit_message_text(
                            card_text.replace("\\", ""), parse_mode=None,
                            reply_markup=specialist_detail_keyboard(spec_id),
                        )
                except Exception:
                    await query.edit_message_text(
                        f"🎭 {name}\n\n{description[:200]}",
                        parse_mode=None,
                        reply_markup=specialist_detail_keyboard(spec_id),
                    )
        elif data.startswith("book_"):
            spec_id = int(data.split("_")[1])
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
