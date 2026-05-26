"""User profile handlers."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, DjMix
from bot.keyboards.inline import profile_keyboard, back_keyboard, main_menu_keyboard
from bot.services.referral_service import count_referrals, get_referrals
from bot.services.event_service import get_saved_events
from bot.services.booking_service import get_user_bookings
from bot.utils.helpers import format_date, has_permission
from bot.config import ROLE_NAMES_RU, ROLE_NAMES_LV


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Сначала используй /start")
            return

        lang = user.language
        referrals_count = count_referrals(db, user)
        referred_list = get_referrals(db, user)
        referred_text = ""
        if referred_list:
            names = []
            for ref in referred_list[:10]:
                u = db.query(User).filter(User.id == ref.referred_id).first()
                if u:
                    names.append(f"@{u.username or u.first_name or '—'}")
            if names:
                referred_text = "\n👥 " + (", ".join(names) if lang == "ru" else ", ".join(names))

        days_in_bot = (datetime.utcnow() - user.registered_at).days if user.registered_at else 0

        # DJ mixes section
        user_mixes = (
            db.query(DjMix)
            .filter(DjMix.user_id == user.id)
            .order_by(DjMix.created_at.desc())
            .limit(5)
            .all()
        )
        mixes_text = ""
        if user_mixes:
            mixes_text = "\n\n🎧 *Миксы / Miksi:* ({})".format(len(user_mixes))
            for m in user_mixes:
                mixes_text += "\n• {} — 👁️{}".format(m.title, m.plays_count)
        is_admin = has_permission(user.role, "admin")
        admin_mode = context.user_data.get("admin_mode", True)

        if lang == "ru":
            role_name = ROLE_NAMES_RU.get(user.role, user.role)
            text = (
                f"👤 *Профиль*\n\n"
                f"Имя: {user.first_name or '—'}\n"
                f"Username: @{user.username or '—'}\n"
                f"Роль: {role_name}\n"
                f"Язык: Русский\n\n"
                f"💰 *Бонусные очки:* {user.points_balance} pts\n"
                f"📈 Всего заработано: {user.total_earned}\n"
                f"📉 Всего потрачено: {user.total_spent}\n"
                f"👥 Пригласил друзей: {referrals_count}{referred_text}\n"
                f"📅 В боте с: {format_date(user.registered_at)}\n"
                f"📆 Дней в боте: {days_in_bot}"
                f"{mixes_text}"
            )
            if is_admin and admin_mode:
                text += (
                    f"\n\n━━━━━━━━━━━━━━━━\n"
                    f"⚙️ *Режим администратора*\n"
                    f"📅 /events — все события\n"
                    f"➕ Создать событие — меню «События»\n"
                    f"👥 /admin — полная админ-панель"
                )
        else:
            role_name = ROLE_NAMES_LV.get(user.role, user.role)
            text = (
                f"👤 *Profils*\n\n"
                f"Vārds: {user.first_name or '—'}\n"
                f"Username: @{user.username or '—'}\n"
                f"Loma: {role_name}\n"
                f"Valoda: Latviešu\n\n"
                f"💰 *Bonusa punkti:* {user.points_balance} pts\n"
                f"📈 Kopā nopelnīts: {user.total_earned}\n"
                f"📉 Kopā iztērēts: {user.total_spent}\n"
                f"👥 Uzaicināti draugi: {referrals_count}{referred_text}\n"
                f"📅 Botā no: {format_date(user.registered_at)}\n"
                f"📆 Dienas botā: {days_in_bot}"
                f"{mixes_text}"
            )
            if is_admin and admin_mode:
                text += (
                    f"\n\n━━━━━━━━━━━━━━━━\n"
                    f"⚙️ *Administratora režīms*\n"
                    f"📅 /events — visi pasākumi\n"
                    f"➕ Izveidot pasākumu — izvēlne «Pasākumi»\n"
                    f"👥 /admin — pilna admin panelis"
                )
        is_superadmin = user.role == "super_admin"
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=profile_keyboard(lang, is_admin=is_admin, admin_mode=admin_mode, is_superadmin=is_superadmin),
        )
    finally:
        db.close()


async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language

        if data == "menu_profile":
            await _build_profile_text(query, user, db, context)
        elif data == "profile_rewards":
            await _show_rewards(query, user, db, lang)
        elif data == "profile_saved":
            await _show_saved(query, user, db, lang)
        elif data == "profile_bookings":
            await _show_bookings(query, user, db, lang)
        elif data == "profile_admin_toggle":
            current = context.user_data.get("admin_mode", True)
            context.user_data["admin_mode"] = not current
            await _build_profile_text(query, user, db, context)
        elif data == "profile_use_bonus_bar":
            await _use_bonus_bar(query, user, db, lang, context)
        elif data == "profile_bar_earn":
            await _bar_earn_qr(query, user, db, lang, context)
    finally:
        db.close()


async def _build_profile_text(query, user, db: Session, context):
    """Rebuild profile text and keyboard for inline edit."""
    lang = user.language
    referrals_count = count_referrals(db, user)
    referred_list = get_referrals(db, user)
    referred_text = ""
    if referred_list:
        names = []
        for ref in referred_list[:10]:
            u = db.query(User).filter(User.id == ref.referred_id).first()
            if u:
                names.append(f"@{u.username or u.first_name or '—'}")
        if names:
            referred_text = "\n👥 " + (", ".join(names) if lang == "ru" else ", ".join(names))
    days_in_bot = (datetime.utcnow() - user.registered_at).days if user.registered_at else 0
    user_mixes = (
        db.query(DjMix)
        .filter(DjMix.user_id == user.id)
        .order_by(DjMix.created_at.desc())
        .limit(5)
        .all()
    )
    mixes_text = ""
    if user_mixes:
        mixes_text = "\n\n🎧 *Миксы / Miksi:* ({})".format(len(user_mixes))
        for m in user_mixes:
            mixes_text += "\n• {} — 👁️{}".format(m.title, m.plays_count)
    is_admin = has_permission(user.role, "admin")
    admin_mode = context.user_data.get("admin_mode", True)
    if lang == "ru":
        role_name = ROLE_NAMES_RU.get(user.role, user.role)
        text = (
            f"👤 *Профиль*\n\n"
            f"Имя: {user.first_name or '—'}\n"
            f"Username: @{user.username or '—'}\n"
            f"Роль: {role_name}\n"
            f"Язык: Русский\n\n"
            f"💰 *Бонусные очки:* {user.points_balance} pts\n"
            f"📈 Всего заработано: {user.total_earned}\n"
            f"📉 Всего потрачено: {user.total_spent}\n"
            f"👥 Пригласил друзей: {referrals_count}{referred_text}\n"
            f"📅 В боте с: {format_date(user.registered_at)}\n"
            f"📆 Дней в боте: {days_in_bot}"
            f"{mixes_text}"
        )
        if is_admin and admin_mode:
            text += (
                f"\n\n━━━━━━━━━━━━━━━━\n"
                f"⚙️ *Режим администратора*\n"
                f"📅 /events — все события\n"
                f"➕ Создать событие — меню «События»\n"
                f"👥 /admin — полная админ-панель"
            )
    else:
        role_name = ROLE_NAMES_LV.get(user.role, user.role)
        text = (
            f"👤 *Profils*\n\n"
            f"Vārds: {user.first_name or '—'}\n"
            f"Username: @{user.username or '—'}\n"
            f"Loma: {role_name}\n"
            f"Valoda: Latviešu\n\n"
            f"💰 *Bonusa punkti:* {user.points_balance} pts\n"
            f"📈 Kopā nopelnīts: {user.total_earned}\n"
            f"📉 Kopā iztērēts: {user.total_spent}\n"
            f"👥 Uzaicināti draugi: {referrals_count}{referred_text}\n"
            f"📅 Botā no: {format_date(user.registered_at)}\n"
            f"📆 Dienas botā: {days_in_bot}"
            f"{mixes_text}"
        )
        if is_admin and admin_mode:
            text += (
                f"\n\n━━━━━━━━━━━━━━━━\n"
                f"⚙️ *Administratora režīms*\n"
                f"📅 /events — visi pasākumi\n"
                f"➕ Izveidot pasākumu — izvēlne «Pasākumi»\n"
                f"👥 /admin — pilna admin panelis"
            )
    is_superadmin = user.role == "super_admin"
    await query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=profile_keyboard(lang, is_admin=is_admin, admin_mode=admin_mode, is_superadmin=is_superadmin),
    )


async def _bar_earn_qr(query, user, db: Session, lang: str, context):
    """Generate bar earn QR from admin profile."""
    context.user_data["bar_admin_mode"] = "earn"
    text_ru = "📤 Введи сумму заказа в EUR для начисления бонусов:\n\nНачисление: 2 pts за 1 EUR\nПример: `25`"
    text_lv = "📤 Ievadi pasūtījuma summu EUR bonusu pieskaitīšanai:\n\nPieskaita: 2 pts par 1 EUR\nPiemērs: `25`"
    await query.edit_message_text(
        text_ru if lang == "ru" else text_lv,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


async def _use_bonus_bar(query, user, db: Session, lang: str, context):
    """Ask user how many points to spend at bar, generate QR."""
    context.user_data["bar_client_mode"] = "pending_amount"
    text_ru = "🍸 Введи количество бонусов для использования в баре:\n\nПример: `50`\n\nДоступно: {} pts"
    text_lv = "🍸 Ievadi bonusu daudzumu izmantošanai bārā:\n\nPiemērs: `50`\n\nPieejams: {} pts"
    await query.edit_message_text(
        (text_ru if lang == "ru" else text_lv).format(user.points_balance),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )
    context.user_data["bar_client_user_id"] = user.id


async def _show_rewards(query, user, db: Session, lang: str):
    from bot.services.bonus_service import get_user_redemptions
    redemptions = get_user_redemptions(db, user)
    if not redemptions:
        await query.edit_message_text(
            "⭐ У тебя пока нет активированных наград." if lang == "ru"
            else "⭐ Tev vēl nav aktivizētu balvu.",
            reply_markup=back_keyboard("menu_profile"),
        )
        return
    text_lines = ["⭐ *Мои награды / Manas balvas*:\n"]
    for r in redemptions:
        text_lines.append(
            f"• {r.reward.title_ru if lang == 'ru' else r.reward.title_lv}"
            f" — {r.points_spent} pts ({r.redeemed_at.strftime('%d.%m.%Y')})"
        )
    await query.edit_message_text(
        "\n".join(text_lines), parse_mode="Markdown",
        reply_markup=back_keyboard("menu_profile"),
    )


async def _show_saved(query, user, db: Session, lang: str):
    saved = get_saved_events(db, user.id)
    if not saved:
        await query.edit_message_text(
            "📭 Нет сохранённых событий." if lang == "ru" else "📭 Nav saglabātu pasākumu.",
            reply_markup=back_keyboard("menu_profile"),
        )
        return
    text_lines = ["💾 *Сохранённые события / Saglabātie pasākumi*:\n"]
    for s in saved:
        if s.event:
            title = s.event.title_lv if lang == "lv" and s.event.title_lv else s.event.title
            text_lines.append(f"• {title} — {s.event.date.strftime('%d.%m.%Y')}")
    await query.edit_message_text(
        "\n".join(text_lines), parse_mode="Markdown",
        reply_markup=back_keyboard("menu_profile"),
    )


async def _show_bookings(query, user, db: Session, lang: str):
    bookings = get_user_bookings(db, user.id)
    if not bookings:
        await query.edit_message_text(
            "📭 Нет заявок на бронирование." if lang == "ru" else "📭 Nav rezervācijas pieteikumu.",
            reply_markup=back_keyboard("menu_profile"),
        )
        return
    text_lines = ["📋 *Мои заявки / Mani pieteikumi*:\n"]
    for b in bookings:
        status = {
            "pending": "⏳ Ожидание", "approved": "✅ Подтверждено",
            "rejected": "❌ Отклонено", "cancelled": "🚫 Отменено"
        }
        s = status.get(b.status, b.status)
        text_lines.append(f"• #{b.id} — {b.event_date.strftime('%d.%m.%Y')} — {s}")
    await query.edit_message_text(
        "\n".join(text_lines), parse_mode="Markdown",
        reply_markup=back_keyboard("menu_profile"),
    )


def register(application):
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CallbackQueryHandler(profile_callback, pattern=r"^(menu_profile|profile_)"))
