"""Dating module handlers — profile, payment (Telegram Stars), browsing, admin moderation."""

import logging
import secrets
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, PreCheckoutQueryHandler
)
from sqlalchemy import desc

from bot.database import SessionLocal
from bot.models import (
    User, DatingProfile, DatingPhoto, DatingAccessPackage, DatingPayment,
    DatingProfileView, DatingComplaint, DatingProfileStatus
)
from bot.services.dating_service import (
    get_or_create_profile, get_profile_by_user, create_profile_from_wizard,
    update_profile, add_photo, remove_photo, get_photos,
    get_active_package, get_profiles_for_viewer, get_payment_history,
    get_package_history, file_complaint, get_dating_config, update_dating_config,
    moderate_profile
)

logger = logging.getLogger(__name__)

# wizard step keys
WIZARD_GENDER = "dating_wizard_gender"
WIZARD_AGE = "dating_wizard_age"
WIZARD_NAME = "dating_wizard_name"
WIZARD_BIO = "dating_wizard_bio"
WIZARD_PHONE = "dating_wizard_phone"
WIZARD_CITY = "dating_wizard_city"
WIZARD_PHOTOS = "dating_wizard_photos"
WIZARD_RULES = "dating_wizard_rules"

_wizard_steps = {
    "gender": WIZARD_GENDER,
    "age": WIZARD_AGE,
    "name": WIZARD_NAME,
    "bio": WIZARD_BIO,
    "phone": WIZARD_PHONE,
    "city": WIZARD_CITY,
    "photos": WIZARD_PHOTOS,
    "rules": WIZARD_RULES,
}


def _(user: User, ru_text: str, lv_text: str) -> str:
    return ru_text if user.language == "ru" else lv_text


async def dating_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        profile = get_profile_by_user(db, user)
        await _show_dating_main_menu(update, context, user, profile, db)
    finally:
        db.close()


async def _show_dating_main_menu(update, context, user, profile, db):
    lang = user.language or "ru"
    if not profile or profile.status == DatingProfileStatus.DRAFT.value:
        text = _query(
            user,
            "💕 *Знакомства*\n\nУ тебя ещё нет анкеты. Создай её, чтобы начать знакомиться!",
            "💕 *Iepazīšanās*\n\nTev vēl nav profila. Izveido to, lai sāktu iepazīties!"
        )
        buttons = [
            [InlineKeyboardButton("📝 Создать анкету / Izveidot profilu", callback_data="dating_create")],
            [InlineKeyboardButton("ℹ️ Правила / Noteikumi", callback_data="dating_rules")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]
    elif profile.status == DatingProfileStatus.PENDING_MODERATION.value:
        text = _query(
            user,
            "💕 *Знакомства*\n\n⏳ Твоя анкета на модерации. Ожидай проверки администратором.",
            "💕 *Iepazīšanās*\n\n⏳ Tavs profils tiek moderēts. Gaidi administratora pārbaudi."
        )
        buttons = [
            [InlineKeyboardButton("📋 Моя анкета / Mans profils", callback_data="dating_my_profile")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]
    elif profile.status == DatingProfileStatus.REJECTED.value:
        text = _query(
            user,
            "💕 *Знакомства*\n\n❌ Твоя анкета отклонена. Свяжись с администратором для уточнения причин.",
            "💕 *Iepazīšanās*\n\n❌ Tavs profils ir noraidīts. Sazinies ar administratoru, lai uzzinātu iemeslus."
        )
        buttons = [
            [InlineKeyboardButton("📋 Моя анкета / Mans profils", callback_data="dating_my_profile")],
            [InlineKeyboardButton("🔄 Создать заново / Izveidot no jauna", callback_data="dating_create")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]
    elif profile.status == DatingProfileStatus.BLOCKED.value:
        text = _query(
            user,
            "💕 *Знакомства*\n\n🚫 Твоя анкета заблокирована. Свяжись с администратором.",
            "💕 *Iepazīšanās*\n\n🚫 Tavs profils ir bloķēts. Sazinies ar administratoru."
        )
        buttons = [
            [InlineKeyboardButton("📩 Поддержка / Atbalsts", callback_data="dating_support")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]
    else:
        pkg = get_active_package(db, profile)
        remaining = (pkg.total_views - pkg.used_views) if pkg else 0
        status_text = _query(
            user,
            f"✅ Анкета активна\n📸 Осталось просмотров: {remaining}",
            f"✅ Profils aktīvs\n📸 Atlikuši skatījumi: {remaining}"
        )
        text = _query(
            user,
            f"💕 *Знакомства*\n\n{status_text}",
            f"💕 *Iepazīšanās*\n\n{status_text}"
        )
        buttons = [
            [InlineKeyboardButton("👀 Смотреть анкеты / Skatīt profilus", callback_data="dating_browse")],
            [InlineKeyboardButton("📋 Моя анкета / Mans profils", callback_data="dating_my_profile")],
            [InlineKeyboardButton("✏️ Редактировать / Rediģēt", callback_data="dating_edit")],
            [InlineKeyboardButton("⭐ Купить просмотры / Pirkt skatījumus", callback_data="dating_buy")],
            [InlineKeyboardButton("📦 Мои покупки / Mani pirkumi", callback_data="dating_purchases")],
            [InlineKeyboardButton("ℹ️ Правила / Noteikumi", callback_data="dating_rules")],
            [InlineKeyboardButton("📩 Поддержка / Atbalsts", callback_data="dating_support")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ]

    reply_markup = InlineKeyboardMarkup(buttons)
    if hasattr(update, "edit_message_text"):
        await update.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif hasattr(update, "callback_query") and update.callback_query is not None:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


# ========== Callback handler ==========

async def dating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        profile = get_profile_by_user(db, user)
        lang = user.language or "ru"

        if data == "dating_main":
            await _show_dating_main_menu(query, context, user, profile, db)

        elif data == "dating_rules":
            await _show_rules(query, user, lang)

        elif data == "dating_support":
            await _show_support(query, user, lang)

        elif data == "dating_create":
            if profile and profile.status not in (DatingProfileStatus.DRAFT.value, DatingProfileStatus.REJECTED.value):
                await query.edit_message_text(
                    _query(user, "Анкета уже существует! / Profils jau pastāv!"),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="dating_main")]
                    ])
                )
                return
            context.user_data["dating_wizard"] = {}
            context.user_data["dating_wizard_step"] = "gender"
            await _ask_gender(query, context, user, lang)

        elif data.startswith("dating_set_gender_"):
            gender = data.split("_")[3]
            context.user_data.setdefault("dating_wizard", {})["gender"] = gender
            context.user_data["dating_wizard_step"] = "age"
            await query.edit_message_text(
                _query(user,
                       f"✅ Пол: {'Мужской' if gender == 'male' else 'Женский'}\n\nСколько тебе лет?",
                       f"✅ Dzimums: {'Vīrietis' if gender == 'male' else 'Sieviete'}\n\nCik tev gadu?")
            )

        elif data == "dating_my_profile":
            await _show_my_profile(query, user, profile, lang, db)

        elif data == "dating_edit":
            await _show_edit_menu(query, user, profile, lang)

        elif data == "dating_edit_gender":
            context.user_data["dating_wizard"] = {}
            context.user_data["dating_wizard_step"] = "gender"
            await _ask_gender(query, context, user, lang, edit_mode=True)

        elif data == "dating_edit_age":
            context.user_data["dating_wizard_step"] = "age"
            await query.edit_message_text(
                _query(user, "✏️ Введи возраст:", "✏️ Ievadi vecumu:")
            )

        elif data == "dating_edit_name":
            context.user_data["dating_wizard_step"] = "name"
            await query.edit_message_text(
                _query(user, "✏️ Введи имя или псевдоним:", "✏️ Ievadi vārdu vai segvārdu:")
            )

        elif data == "dating_edit_bio":
            context.user_data["dating_wizard_step"] = "bio"
            await query.edit_message_text(
                _query(user, "✏️ Напиши o себе:", "✏️ Uzraksti par sevi:")
            )

        elif data == "dating_edit_phone":
            context.user_data["dating_wizard_step"] = "phone"
            await query.edit_message_text(
                _query(user, "✏️ Введи номер телефона:", "✏️ Ievadi telefona numuru:")
            )

        elif data == "dating_edit_city":
            context.user_data["dating_wizard_step"] = "city"
            await query.edit_message_text(
                _query(user, "✏️ Введи город:", "✏️ Ievadi pilsētu:")
            )

        elif data == "dating_edit_photo":
            context.user_data["dating_wizard_step"] = "photos"
            await query.edit_message_text(
                _query(user,
                       "📤 Отправь фото (до 3 штук).\n"
                       "После отправки всех фото нажми «✅ Готово».",
                       "📤 Nosūti foto (līdz 3 gab.).\n"
                       "Pēc visu foto nosūtīšanas nospied «✅ Gatavs»."),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Готово / Gatavs", callback_data="dating_edit_photo_done")]
                ])
            )

        elif data == "dating_edit_photo_done":
            context.user_data.pop("dating_wizard_step", None)
            await _show_edit_menu(query, user, profile, lang)

        elif data == "dating_edit_rules":
            await _ask_rules_accept(query, context, user, lang, edit_mode=True)

        elif data == "dating_accept_rules":
            wizard = context.user_data.get("dating_wizard", {})
            edit_mode = context.user_data.get("dating_wizard_edit_mode", False)
            if edit_mode and profile:
                await _finish_wizard_edit(query, context, user, profile, db)
            else:
                await _finish_wizard(query, context, user, db)

        elif data == "dating_decline_rules":
            context.user_data.pop("dating_wizard", None)
            context.user_data.pop("dating_wizard_step", None)
            await _show_dating_main_menu(query, context, user, profile, db)

        elif data == "dating_buy":
            await _buy_package(query, context, user, profile, lang)

        elif data == "dating_buy_confirm":
            await _confirm_buy(query, context, user, profile, lang)

        elif data == "dating_browse":
            await _browse_profiles(query, context, user, profile, lang, db)

        elif data.startswith("dating_like_"):
            target_id = int(data.split("_")[2])
            target = db.query(DatingProfile).filter(DatingProfile.id == target_id).first()
            if target:
                existing_view = db.query(DatingProfileView).filter(
                    DatingProfileView.viewer_profile_id == profile.id,
                    DatingProfileView.target_profile_id == target_id,
                ).first()
                if existing_view:
                    existing_view.show_phone = True
                    db.commit()
                phone_text = ""
                if target.phone and not get_dating_config().get("safe_mode", True):
                    phone_text = f"\n📞 {target.phone}"
                await query.answer("❤️", show_alert=False)
                await _show_next_profile(query, context, user, profile, lang, db)
            else:
                await query.answer("Анкета не найдена / Profils nav atrasts", show_alert=True)

        elif data == "dating_dislike":
            await _show_next_profile(query, context, user, profile, lang, db)

        elif data == "dating_complaint":
            current_target = context.user_data.get("dating_current_target_id")
            if current_target:
                context.user_data["dating_wizard_step"] = "complaint"
                await query.edit_message_text(
                    _query(user,
                           "Опиши причину жалобы:",
                           "Apraksti sūdzības iemeslu:"),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="dating_browse")]
                    ])
                )

        elif data == "dating_purchases":
            await _show_purchases(query, user, profile, lang, db)

        elif data == "dating_wizard_cancel":
            context.user_data.pop("dating_wizard", None)
            context.user_data.pop("dating_wizard_step", None)
            context.user_data.pop("dating_wizard_edit_mode", None)
            profile = get_profile_by_user(db, user)
            await _show_dating_main_menu(query, context, user, profile, db)

    finally:
        db.close()


# ========== Wizard and Edit helpers ==========

async def _ask_gender(query, context, user, lang, edit_mode=False):
    buttons = [
        [InlineKeyboardButton("👨 Мужской / Vīrietis", callback_data="dating_set_gender_male")],
        [InlineKeyboardButton("👩 Женский / Sieviete", callback_data="dating_set_gender_female")],
    ]
    if edit_mode:
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="dating_edit")])
    else:
        buttons.append([InlineKeyboardButton("❌ Отмена / Atcelt", callback_data="dating_wizard_cancel")])
    if edit_mode:
        context.user_data["dating_wizard_edit_mode"] = True
    await query.edit_message_text(
        _query(user,
               "💕 *Создание анкеты*\n\nВыбери свой *пол*:",
               "💕 *Profila izveide*\n\nIzvēlies savu *dzimumu*:"),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _ask_rules_accept(query_or_update, context, user, lang, edit_mode=False):
    text = _query(user,
                  "📋 *Правила раздела Знакомства*\n\n"
                  "1. Запрещены оскорбления и непристойное поведение\n"
                  "2. Запрещена реклама и спам\n"
                  "3. Фото должны быть реальными\n"
                  "4. Администрация вправе заблокировать анкету без объяснения причин\n\n"
                  "Подтверждаешь согласие с правилами?",
                  "📋 *Iepazīšanās sadaļas noteikumi*\n\n"
                  "1. Aizliegti apvainojumi un nepieklājīga uzvedība\n"
                  "2. Aizliegta reklāma un surogātpasts\n"
                  "3. Fotoattēliem jābūt reāliem\n"
                  "4. Administrācijai ir tiesības bloķēt profilu bez paskaidrojuma\n\n"
                  "Apstiprini piekrišanu noteikumiem?")
    buttons = [
        [InlineKeyboardButton("✅ Да / Jā", callback_data="dating_accept_rules")],
        [InlineKeyboardButton("❌ Нет / Nē", callback_data="dating_decline_rules")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif hasattr(query_or_update, "callback_query") and query_or_update.callback_query is not None:
        await query_or_update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await query_or_update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def _finish_wizard(query, context, user, db):
    wizard = context.user_data.get("dating_wizard", {})
    profile = get_or_create_profile(db, user)
    data = {
        "display_name": wizard.get("name", user.first_name),
        "gender": wizard.get("gender"),
        "age": wizard.get("age"),
        "bio": wizard.get("bio", ""),
        "phone": wizard.get("phone", ""),
        "city": wizard.get("city", "Daugavpils"),
    }
    create_profile_from_wizard(db, user, data)
    context.user_data.pop("dating_wizard", None)
    context.user_data.pop("dating_wizard_step", None)
    await query.edit_message_text(
        _query(user,
               "✅ *Анкета отправлена на модерацию!*\n\n"
               "Ожидай проверки администратором. Это обычно занимает до 24 часов.",
               "✅ *Profils nosūtīts moderācijai!*\n\n"
               "Gaidi administratora pārbaudi. Parasti tas aizņem līdz 24 stundām."),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Моя анкета / Mans profils", callback_data="dating_my_profile")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
        ])
    )


async def _finish_wizard_edit(query, context, user, profile, db):
    wizard = context.user_data.get("dating_wizard", {})
    update_data = {}
    if "gender" in wizard:
        update_data["gender"] = wizard["gender"]
    if "age" in wizard:
        update_data["age"] = wizard["age"]
    if "name" in wizard:
        update_data["display_name"] = wizard["name"]
    if "bio" in wizard:
        update_data["bio"] = wizard["bio"]
    if "phone" in wizard:
        update_data["phone"] = wizard["phone"]
    if "city" in wizard:
        update_data["city"] = wizard["city"]

    profile.rules_accepted = True
    if update_data:
        update_profile(db, profile, update_data)

    context.user_data.pop("dating_wizard", None)
    context.user_data.pop("dating_wizard_step", None)
    context.user_data.pop("dating_wizard_edit_mode", None)
    await query.edit_message_text(
        _query(user,
               "✅ Анкета обновлена!",
               "✅ Profils atjaunināts!"),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Моя анкета / Mans profils", callback_data="dating_my_profile")],
            [InlineKeyboardButton("◀️ Назад", callback_data="dating_main")],
        ])
    )


async def _show_edit_menu(query_or_update, user, profile, lang):
    if not profile:
        return
    photos_count = profile.photos.count()
    gender = {"male": "👨 Мужской / Vīrietis", "female": "👩 Женский / Sieviete"}.get(profile.gender, "—")
    text = _query(user,
                  f"✏️ *Редактировать анкету*\n\n"
                  f"👤 Пол: {gender}\n"
                  f"🎂 Возраст: {profile.age or '—'}\n"
                  f"📝 Имя: {profile.display_name or '—'}\n"
                  f"📄 О себе: {(profile.bio or '—')[:50]}\n"
                  f"📞 Телефон: {profile.phone or '—'}\n"
                  f"🏙 Город: {profile.city or '—'}\n"
                  f"🖼 Фото: {photos_count}/3\n"
                  f"📋 Статус: {profile.status}",
                  f"✏️ *Rediģēt profilu*\n\n"
                  f"👤 Dzimums: {gender}\n"
                  f"🎂 Vecums: {profile.age or '—'}\n"
                  f"📝 Vārds: {profile.display_name or '—'}\n"
                  f"📄 Par sevi: {(profile.bio or '—')[:50]}\n"
                  f"📞 Tālrunis: {profile.phone or '—'}\n"
                  f"🏙 Pilsēta: {profile.city or '—'}\n"
                  f"🖼 Foto: {photos_count}/3\n"
                  f"📋 Statuss: {profile.status}")
    buttons = [
        [InlineKeyboardButton("👤 Пол / Dzimums", callback_data="dating_edit_gender")],
        [InlineKeyboardButton("🎂 Возраст / Vecums", callback_data="dating_edit_age")],
        [InlineKeyboardButton("📝 Имя / Vārds", callback_data="dating_edit_name")],
        [InlineKeyboardButton("📄 О себе / Par sevi", callback_data="dating_edit_bio")],
        [InlineKeyboardButton("📞 Телефон / Tālrunis", callback_data="dating_edit_phone")],
        [InlineKeyboardButton("🏙 Город / Pilsēta", callback_data="dating_edit_city")],
        [InlineKeyboardButton("🖼 Фото / Foto", callback_data="dating_edit_photo")],
        [InlineKeyboardButton("📋 Принять правила / Pieņemt noteikumus", callback_data="dating_edit_rules")],
        [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif hasattr(query_or_update, "callback_query") and query_or_update.callback_query is not None:
        await query_or_update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await query_or_update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def _show_my_profile(query, user, profile, lang, db):
    if not profile:
        await query.edit_message_text(
            _query(user, "Анкета не найдена / Profils nav atrasts"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="dating_main")]
            ])
        )
        return
    photos = get_photos(db, profile)
    gender = {"male": "👨 Мужской", "female": "👩 Женский"}.get(profile.gender, "—")
    status_emoji = {
        "draft": "📝", "pending_moderation": "⏳", "active": "✅",
        "rejected": "❌", "blocked": "🚫", "deleted": "🗑"
    }.get(profile.status, "❓")
    text = _query(user,
                  f"💕 *Твоя анкета*\n\n"
                  f"Статус: {status_emoji} {profile.status}\n"
                  f"👤 {profile.display_name or '—'}\n"
                  f"Пол: {gender}\n"
                  f"🎂 Возраст: {profile.age or '—'}\n"
                  f"📄 {profile.bio or '—'}\n"
                  f"📞 {profile.phone or '—'}\n"
                  f"🏙 {profile.city or '—'}\n"
                  f"🖼 Фото: {photos.count()}/3",
                  f"💕 *Tavs profils*\n\n"
                  f"Statuss: {status_emoji} {profile.status}\n"
                  f"👤 {profile.display_name or '—'}\n"
                  f"Dzimums: {gender}\n"
                  f"🎂 Vecums: {profile.age or '—'}\n"
                  f"📄 {profile.bio or '—'}\n"
                  f"📞 {profile.phone or '—'}\n"
                  f"🏙 {profile.city or '—'}\n"
                  f"🖼 Foto: {photos.count()}/3")
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редактировать / Rediģēt", callback_data="dating_edit")],
        [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
    ])
    try:
        if photos.count() > 0:
            first_photo = photos[0]
            if query.message.caption:
                await query.edit_message_caption(
                    caption=text, parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
            else:
                await query.message.reply_photo(
                    photo=first_photo.telegram_file_id,
                    caption=text, parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                await query.message.delete()
            return
    except Exception:
        pass
    await query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def _show_rules(query, user, lang):
    await query.edit_message_text(
        _query(user,
               "📋 *Правила раздела Знакомства*\n\n"
               "1. Запрещены оскорбления и непристойное поведение\n"
               "2. Запрещена реклама и спам\n"
               "3. Фото должны быть реальными\n"
               "4. Нельзя выдавать себя за другого человека\n"
               "5. Администрация вправе заблокировать анкету без объяснения причин\n\n"
               "Нарушение правил ведёт к блокировке анкеты.",
               "📋 *Iepazīšanās sadaļas noteikumi*\n\n"
               "1. Aizliegti apvainojumi un nepieklājīga uzvedība\n"
               "2. Aizliegta reklāma un surogātpasts\n"
               "3. Fotoattēliem jābūt reāliem\n"
               "4. Nedrīkst uzdoties par citu personu\n"
               "5. Administrācijai ir tiesības bloķēt profilu bez paskaidrojuma\n\n"
               "Noteikumu pārkāpšana noved pie profila bloķēšanas."),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")]
        ])
    )


async def _show_support(query, user, lang):
    await query.edit_message_text(
        _query(user,
               "📩 *Поддержка*\n\n"
               "По всем вопросам обращайся к администратору:\n"
               "Напиши /help или отправь сообщение через кнопку «📩 Администратору» в главном меню.",
               "📩 *Atbalsts*\n\n"
               "Visos jautājumos sazinies ar administratoru:\n"
               "Raksti /help vai nosūti ziņu caur pogu «📩 Administratoram» galvenajā izvēlnē."),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")]
        ])
    )


# ========== Payment ==========

async def _buy_package(query, context, user, profile, lang):
    config = get_dating_config()
    price = config["package_price_stars"]
    size = config["package_size"]
    await query.edit_message_text(
        _query(user,
               f"⭐ *Купить просмотры*\n\n"
               f"📸 {size} просмотров анкет\n"
               f"💰 Цена: {price} ⭐ Stars\n\n"
               f"После оплаты ты получишь {size} случайных анкет противоположного пола.",
               f"⭐ *Pirkt skatījumus*\n\n"
               f"📸 {size} profilu skatījumi\n"
               f"💰 Cena: {price} ⭐ Stars\n\n"
               f"Pēc apmaksas tu saņemsi {size} nejaušus pretējā dzimuma profilus."),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⭐ Купить за {price} Stars", callback_data="dating_buy_confirm")],
            [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
        ])
    )


async def _confirm_buy(query, context, user, profile, lang):
    config = get_dating_config()
    price = config["package_price_stars"]
    size = config["package_size"]
    payload = f"dating_pkg_{profile.id}_{secrets.token_hex(8)}"
    context.user_data["dating_invoice_payload"] = payload

    await context.bot.send_invoice(
        chat_id=user.telegram_id,
        title=_query(user, "Просмотр анкет / Profilu skatīšana"),
        description=_query(
            user,
            f"Доступ к {size} анкетам противоположного пола",
            f"Piekļuve {size} pretējā dzimuma profiliem"
        ),
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(
            _query(user, f"{size} просмотров / skatījumi", f"{size} skatījumi"),
            price
        )],
    )

    # Record pending payment
    from bot.services.dating_service import create_payment_record
    payment_db = SessionLocal()
    try:
        create_payment_record(
            db=payment_db,
            profile=profile,
            telegram_user_id=user.telegram_id,
            amount_stars=price,
            package_size=size,
            invoice_payload=payload,
        )
    finally:
        payment_db.close()


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    payload = query.invoice_payload
    if payload.startswith("dating_pkg_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Unknown invoice")


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    tg_charge_id = payment.telegram_payment_charge_id
    provider_charge_id = payment.provider_payment_charge_id

    db = SessionLocal()
    try:
        from bot.services.dating_service import confirm_payment
        pkg = confirm_payment(db, payload, tg_charge_id, provider_charge_id)
        if pkg:
            user_tg = update.effective_user
            user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            lang = user.language if user else "ru"
            await update.message.reply_text(
                _query_r(lang,
                         f"✅ *Оплата успешна!*\n\n"
                         f"Тебе доступно {pkg.total_views} просмотров анкет.\n"
                         f"Нажми «👀 Смотреть анкеты», чтобы начать!",
                         f"✅ *Apmaksa veiksmīga!*\n\n"
                         f"Tev pieejami {pkg.total_views} profilu skatījumi.\n"
                         f"Nospied «👀 Skatīt profilus», lai sāktu!"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👀 Смотреть анкеты / Skatīt profilus",
                                          callback_data="dating_browse")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
                ])
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка обработки платежа. Свяжись с администратором."
            )
    finally:
        db.close()


async def _show_purchases(query, user, profile, lang, db):
    if not profile:
        return
    payments = get_payment_history(db, profile)
    packages = get_package_history(db, profile)

    text = _query(user, "📦 *Мои покупки*\n\n", "📦 *Mani pirkumi*\n\n")
    if not packages:
        text += _query(user, "У тебя ещё нет покупок.", "Tev vēl nav pirkumu.")
    else:
        for p in packages:
            status = "✅" if p.status == "active" else "⏳" if p.status == "exhausted" else "❌"
            left = p.total_views - p.used_views
            text += f"{status} {p.total_views} просмотров / skatījumi — осталось / atlicis: {left}\n"

    await query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Купить ещё / Pirkt vēl", callback_data="dating_buy")],
            [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
        ])
    )


# ========== Profile browsing ==========

async def _browse_profiles(query, context, user, profile, lang, db):
    if not profile:
        return
    pkg = get_active_package(db, profile)
    if not pkg or pkg.used_views >= pkg.total_views:
        await query.edit_message_text(
            _query(user,
                   "😕 У тебя нет активных просмотров.\n\n"
                   "Купи пакет просмотров, чтобы увидеть анкеты!",
                   "😕 Tev nav aktīvu skatījumu.\n\n"
                   "Pērc skatījumu paketi, lai redzētu profilus!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Купить просмотры / Pirkt skatījumus",
                                      callback_data="dating_buy")],
                [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
            ])
        )
        return

    candidates = get_profiles_for_viewer(db, profile)
    if not candidates:
        await query.edit_message_text(
            _query(user,
                   "😕 Пока нет новых анкет. Загляни позже!",
                   "😕 Pašlaik nav jaunu profilu. Ieskaties vēlāk!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить / Atsvaidzināt",
                                      callback_data="dating_browse")],
                [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
            ])
        )
        return

    context.user_data["dating_candidates"] = [c.id for c in candidates]
    context.user_data["dating_current_index"] = 0
    await _show_candidate(query, context, user, profile, lang, db)
async def _show_candidate(query, context, user, profile, lang, db):
    candidates = context.user_data.get("dating_candidates", [])
    index = context.user_data.get("dating_current_index", 0)
    if index >= len(candidates):
        pkg = get_active_package(db, profile)
        remaining = (pkg.total_views - pkg.used_views) if pkg else 0
        if remaining > 0:
            await _browse_profiles(query, context, user, profile, lang, db)
            return
        await query.edit_message_text(
            _query(user,
                   "🎉 Ты просмотрел(а) все доступные анкеты!\n\n"
                   "Купи ещё просмотров, чтобы продолжить!",
                   "🎉 Tu esi apskatījis visus pieejamos profilus!\n\n"
                   "Pērc vēl skatījumus, lai turpinātu!"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Купить просмотры / Pirkt skatījumus",
                                      callback_data="dating_buy")],
                [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
            ])
        )
        return

    target_id = candidates[index]
    target = db.query(DatingProfile).filter(DatingProfile.id == target_id).first()
    if not target or target.status != DatingProfileStatus.ACTIVE.value:
        context.user_data["dating_current_index"] = index + 1
        await _show_candidate(query, context, user, profile, lang, db)
        return

    context.user_data["dating_current_target_id"] = target_id
    target_user = db.query(User).filter(User.id == target.user_id).first()
    photos = get_photos(db, target)
    safe_mode = get_dating_config().get("safe_mode", True)

    age_text = f", {target.age}" if target.age else ""
    caption = (
        f"💕 {target.display_name or '—'}{age_text}\n\n"
        f"{target.bio or ''}"
    )
    if not safe_mode and target.phone:
        caption += f"\n📞 {target.phone}"

    buttons = [
        [
            InlineKeyboardButton("👎", callback_data="dating_dislike"),
            InlineKeyboardButton("❤️", callback_data=f"dating_like_{target_id}"),
        ],
        [InlineKeyboardButton("🚩 Пожаловаться / Sūdzēties", callback_data="dating_complaint")],
        [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data="dating_main")],
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    try:
        if photos:
            first_photo = photos[0]
            if query.message.caption:
                await query.edit_message_caption(
                    caption=caption, parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=first_photo.telegram_file_id,
                    caption=caption, parse_mode="Markdown",
                    reply_markup=reply_markup,
                )
                await query.message.delete()
            return
    except Exception:
        pass
    await query.edit_message_text(
        caption, parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def _show_next_profile(query, context, user, profile, lang, db):
    index = context.user_data.get("dating_current_index", 0) + 1
    context.user_data["dating_current_index"] = index
    await _show_candidate(query, context, user, profile, lang, db)


# ========== Text handler ==========

async def handle_dating_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("dating_wizard_step")
    if not step:
        return

    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language or "ru"
        profile = get_profile_by_user(db, user)
        text = update.message.text.strip()

        if step == "age":
            try:
                age = int(text)
                if age < 16 or age > 120:
                    raise ValueError
            except ValueError:
                await update.message.reply_text(
                    _query_r(lang, "❌ Введи число от 16 до 120.", "❌ Ievadi skaitli no 16 līdz 120.")
                )
                return
            context.user_data.setdefault("dating_wizard", {})["age"] = age
            if context.user_data.get("dating_wizard_edit_mode"):
                context.user_data.pop("dating_wizard_step", None)
                await update.message.reply_text(f"✅ Возраст: {age}")
                profile = get_profile_by_user(db, user)
                await _show_edit_menu(update, context, user, profile, lang)
            else:
                context.user_data["dating_wizard_step"] = "name"
                await update.message.reply_text(
                    _query_r(lang,
                             f"✅ Возраст: {age}\n\nВведи имя или псевдоним:",
                             f"✅ Vecums: {age}\n\nIevadi vārdu vai segvārdu:")
                )

        elif step == "name":
            if len(text) > 100:
                await update.message.reply_text("❌ Слишком длинное имя / Vārds pārāk garš")
                return
            context.user_data.setdefault("dating_wizard", {})["name"] = text
            context.user_data["dating_wizard_step"] = "bio"
            await update.message.reply_text(
                _query_r(lang,
                         f"✅ Имя: {text}\n\nНапиши немного о себе:",
                         f"✅ Vārds: {text}\n\nUzraksti nedaudz par sevi:")
            )

        elif step == "bio":
            if len(text) > 500:
                await update.message.reply_text("❌ Слишком длинное описание / Apraksts pārāk garš")
                return
            context.user_data.setdefault("dating_wizard", {})["bio"] = text
            if context.user_data.get("dating_wizard_edit_mode"):
                context.user_data.pop("dating_wizard_step", None)
                await update.message.reply_text(f"✅ Описание обновлено / Apraksts atjaunināts")
                await _show_edit_menu(update, context, user, profile, lang)
            else:
                context.user_data["dating_wizard_step"] = "phone"
                await update.message.reply_text(
                    _query_r(lang,
                             f"✅ Описание сохранено!\n\nВведи номер телефона (или отправь «—» чтобы пропустить):",
                             f"✅ Apraksts saglabāts!\n\nIevadi telefona numuru (vai nosūti «—» lai izlaistu):")
                )

        elif step == "phone":
            if text != "—" and text.strip():
                context.user_data.setdefault("dating_wizard", {})["phone"] = text
            else:
                context.user_data.setdefault("dating_wizard", {})["phone"] = ""
            if context.user_data.get("dating_wizard_edit_mode"):
                context.user_data.pop("dating_wizard_step", None)
                await update.message.reply_text(f"✅ Телефон обновлён / Tālrunis atjaunināts")
                await _show_edit_menu(update, context, user, profile, lang)
            else:
                context.user_data["dating_wizard_step"] = "city"
                await update.message.reply_text(
                    _query_r(lang,
                             f"✅ Телефон сохранён!\n\nВведи город (или отправь «—» для Даугавпилса):",
                             f"✅ Tālrunis saglabāts!\n\nIevadi pilsētu (vai nosūti «—» Daugavpilij):")
                )

        elif step == "city":
            city = text if text != "—" else "Daugavpils"
            context.user_data.setdefault("dating_wizard", {})["city"] = city
            if context.user_data.get("dating_wizard_edit_mode"):
                context.user_data.pop("dating_wizard_step", None)
                await update.message.reply_text(f"✅ Город обновлён / Pilsēta atjaunināta")
                await _show_edit_menu(update, context, user, profile, lang)
            else:
                context.user_data["dating_wizard_step"] = "photos"
                await update.message.reply_text(
                    _query_r(lang,
                             f"✅ Город: {city}\n\n"
                             f"📸 Отправь свои фото (до 3 штук).\n"
                             f"После отправки всех фото нажми /done или просто напиши /done.",
                             f"✅ Pilsēta: {city}\n\n"
                             f"📸 Nosūti savas foto (līdz 3 gab.).\n"
                             f"Pēc visu foto nosūtīšanas nospied /done vai vienkārši uzraksti /done.")
                )

        elif step == "complaint":
            target_id = context.user_data.get("dating_current_target_id")
            if target_id and text != "—":
                target = db.query(DatingProfile).filter(DatingProfile.id == target_id).first()
                if target:
                    file_complaint(db, target, user.telegram_id, text)
                    await update.message.reply_text(
                        _query_r(lang,
                                 "✅ Жалоба отправлена администратору.",
                                 "✅ Sūdzība nosūtīta administratoram.")
                    )
            context.user_data.pop("dating_wizard_step", None)
            await _show_dating_main_menu(update, context, user, get_profile_by_user(db, user), db)

    finally:
        db.close()


async def handle_dating_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("dating_wizard_step")
    if step != "photos":
        return

    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        profile = get_or_create_profile(db, user)
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        result = add_photo(db, profile, photo_file.file_id)
        if result:
            await update.message.reply_text(
                "✅ Фото добавлено! / Foto pievienots!"
            )
        else:
            await update.message.reply_text(
                "❌ Максимум 3 фото / Maksimums 3 foto"
            )
    finally:
        db.close()


async def handle_dating_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("dating_wizard_step")
    if step == "photos":
        user_tg = update.effective_user
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not user:
                return
            profile = get_profile_by_user(db, user)
            context.user_data.pop("dating_wizard_step", None)
            if context.user_data.get("dating_wizard_edit_mode"):
                context.user_data.pop("dating_wizard_edit_mode", None)
                await update.message.reply_text(
                    "✅ Фото обновлены / Foto atjaunināti",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Моя анкета / Mans profils",
                                              callback_data="dating_my_profile")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="dating_main")],
                    ])
                )
            else:
                await _ask_rules_accept(update, context, user, user.language or "ru")
        finally:
            db.close()


# ========== Utility helpers ==========

def _query(user, ru_text: str, lv_text: str = None) -> str:
    if lv_text is None:
        return ru_text
    return ru_text if user.language == "ru" else lv_text


def _query_r(lang: str, ru_text: str, lv_text: str) -> str:
    return ru_text if lang == "ru" else lv_text


def register(application):
    application.add_handler(CallbackQueryHandler(dating_callback, pattern=r"^dating_"))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_dating_photo))
    # handle_dating_text in group 1 so it runs after reply_keyboard_handler in group 0
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dating_text), group=1)
    application.add_handler(CommandHandler("done", handle_dating_done))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT, successful_payment_handler
    ))
