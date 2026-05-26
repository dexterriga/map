"""Start, registration, and main menu handlers."""

import secrets
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, PointsQR, PointsLog
from bot.config import POINTS, BOT_USERNAME, OWNER_ID
from bot.keyboards.inline import main_menu_keyboard, main_reply_keyboard, language_keyboard
from bot.services.bonus_service import award_points
from bot.services.referral_service import create_referral, process_referral_bonus
from bot.services.event_service import get_featured_events
from bot.utils.helpers import get_role_level, generate_referral_link, parse_referral, has_permission, format_datetime, format_price


async def _send_pinned_events(update, context, lang):
    """Send pinned events with image at the top before welcome message."""
    try:
        db = SessionLocal()
        try:
            pinned = get_featured_events(db, limit=3)
            for ev in pinned:
                title = ev.title_lv if lang == "lv" and ev.title_lv else ev.title
                text = (
                    f"📌 *{title}*\n\n"
                    f"📆 {format_datetime(ev.date)}\n"
                    f"📍 {ev.venue or 'TBA'}"
                )
                if ev.address:
                    text += f"\n🗺️ {ev.address}"
                if ev.price:
                    text += f"\n🏷️ {format_price(ev.price)}"
                if ev.image_url:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=ev.image_url,
                        caption=text,
                        parse_mode="Markdown",
                    )
                    desc = ev.description_lv if lang == "lv" and ev.description_lv else ev.description
                    if desc:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=desc,
                            parse_mode="Markdown",
                        )
                else:
                    desc = ev.description_lv if lang == "lv" and ev.description_lv else ev.description
                    if desc:
                        text += f"\n\n{desc}"
                    await update.message.reply_text(text, parse_mode="Markdown")
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.exception("Pinned event send failed")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    args = context.args
    db = SessionLocal()

    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()

        # Auto-assign super_admin to owner
        if user_tg.id == OWNER_ID:
            if not db_user:
                db_user = User(
                    telegram_id=user_tg.id,
                    username=user_tg.username,
                    first_name=user_tg.first_name,
                    last_name=user_tg.last_name,
                    role="super_admin",
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

                award_points(db, db_user, POINTS["REGISTRATION"],
                             "Регистрация в боте", "Reģistrācija botā")

                await _send_pinned_events(update, context, db_user.language)
                await update.message.reply_text(
                    "👑 *Добро пожаловать, создатель!*\n\n"
                    "Ты назначен Super Admin. Используй /admin для панели управления.",
                    parse_mode="Markdown",
                )
                await _send_persistent_reply(update, db_user.language, is_admin=True, is_bar_admin=False)
                return
            else:
                if db_user.role != "super_admin":
                    db_user.role = "super_admin"
                    db.commit()

        if not db_user:
            referrer = None
            if args and args[0].startswith("ref_"):
                ref_id = parse_referral(args[0])
                if ref_id and ref_id != user_tg.id:
                    referrer = db.query(User).filter(User.telegram_id == ref_id).first()

            db_user = User(
                telegram_id=user_tg.id,
                username=user_tg.username,
                first_name=user_tg.first_name,
                last_name=user_tg.last_name,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            award_points(db, db_user, POINTS["REGISTRATION"],
                         "Регистрация в боте", "Reģistrācija botā")

            if referrer:
                create_referral(db, referrer.id, db_user.id)
                process_referral_bonus(db, referrer, db_user)

            await _send_pinned_events(update, context, db_user.language)
            await update.message.reply_text(
                _get_text("WELCOME", db_user.language),
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(db_user.language),
            )
            is_bar_admin = db_user.role == "bar_admin"
            await _send_persistent_reply(update, db_user.language, is_admin=has_permission(db_user.role, "admin"), is_bar_admin=is_bar_admin)
        else:
            db_user.last_activity = datetime.utcnow()
            db.commit()

            is_bar_admin = db_user.role == "bar_admin"
            await _send_pinned_events(update, context, db_user.language)
            await update.message.reply_text(
                f"🎉 *{db_user.first_name}, с возвращением!* 🎉\n\n"
                f"👇 Используй кнопки внизу экрана или /menu" if db_user.language == "ru"
                else f"🎉 *{db_user.first_name}, ar atgriešanos!* 🎉\n\n"
                     f"👇 Izmanto pogas ekrāna apakšā vai /menu",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(db_user.language),
            )
            await _send_persistent_reply(update, db_user.language, is_admin=has_permission(db_user.role, "admin"), is_bar_admin=is_bar_admin)
    finally:
        db.close()


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = db_user.language if db_user else "ru"

        text = _get_text("MENU_TITLE", lang)
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang)
        )
    finally:
        db.close()


async def _send_persistent_reply(update, lang, is_admin=False, is_bar_admin=False):
    await update.message.reply_text(
        "👇" if lang == "ru" else "👇",
        reply_markup=main_reply_keyboard(lang, is_admin=is_admin, is_bar_admin=is_bar_admin),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_tg = update.effective_user

    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = db_user.language if db_user else "ru"

        if data == "menu_main":
            await query.edit_message_text(
                _get_text("MENU_TITLE", lang),
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang),
            )
        elif data == "menu_help":
            await query.edit_message_text(
                _get_text("HELP_TEXT", lang),
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang),
            )
        elif data == "menu_dating":
            from bot.handlers.dating import dating_menu
            await dating_menu(update, context)
        elif data == "lang_ru":
            if db_user:
                db_user.language = "ru"
                db.commit()
            await query.edit_message_text(
                "✅ Язык изменён на русский.",
                reply_markup=main_menu_keyboard("ru"),
            )
        elif data == "lang_lv":
            if db_user:
                db_user.language = "lv"
                db.commit()
            await query.edit_message_text(
                "✅ Valoda mainīta uz latviešu.",
                reply_markup=main_menu_keyboard("lv"),
            )
    finally:
        db.close()


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери язык / Izvēlies valodu:",
        reply_markup=language_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        lang = user.language if user else "ru"
        await update.message.reply_text(
            _get_text("HELP_TEXT", lang),
            parse_mode="Markdown",
        )
    finally:
        db.close()


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        lang = user.language if user else "ru"
        await update.message.reply_text(
            _get_text("DESCRIPTION", lang),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    finally:
        db.close()


def _get_text(key: str, lang: str = "ru") -> str:
    if lang == "lv":
        from texts import lv as t
    else:
        from texts import ru as t
    return getattr(t, key, key)


async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_tg = update.effective_user

    # If text matches any reply keyboard button, cancel any pending mode and dispatch
    _reply_buttons = {
        "📋 Меню", "📋 Menu",
        "📅 Афиша", "⭐ Бонусы", "🎭 Специалисты", "🎧 DJ Миксы",
        "👤 Профиль", "👥 Пригласи друга", "🎤 Я – специалист", "📸 Сканировать QR",
        "💕 Знакомства", "📰 Лента",
        "📩 Администратору", "ℹ️ Помощь", "🌐 LV / RU", "⚙️ Admin", "🍸 Bar Admin",
        "📅 Afiša", "⭐ Bonusi", "🎭 Speciālisti", "🎧 Miksi",
        "👤 Profils", "👥 Uzaicini draugu", "🎤 Es esmu speciālists", "📸 Skenēt QR",
        "💕 Iepazīšanās", "📰 Jaunumi",
        "📩 Administratoram", "ℹ️ Palīdzība", "🌐 RU / LV",
    }
    if text in _reply_buttons:
        context.user_data.pop("scan_mode", None)
        context.user_data.pop("bar_client_mode", None)
        context.user_data.pop("bar_admin_mode", None)
        context.user_data.pop("booking_step", None)
        # Fall through to dispatch below

    # Check if user is in scan_mode (entering QR code manually)
    elif context.user_data.get("scan_mode"):
        db = SessionLocal()
        try:
            user_tg = update.effective_user
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not db_user:
                return

            lang = db_user.language or "ru"
            qr_entry = db.query(PointsQR).filter(PointsQR.code == text.strip(), PointsQR.is_used == False).first()
            if not qr_entry:
                await update.message.reply_text(
                    "❌ Неверный код / Nepareizs kods\nПопробуй снова или /scan <код>"
                )
                return

            context.user_data.pop("scan_mode", None)

            if qr_entry.action == "use":
                target_user = db.query(User).filter(User.id == qr_entry.user_id).first()
                if not target_user:
                    await update.message.reply_text("❗ Ошибка: пользователь не найден / Kļūda: lietotājs nav atrasts")
                    return

                if target_user.bonus_points < qr_entry.amount:
                    await update.message.reply_text(
                        f"❌ У клиента недостаточно бонусов / Klientam nepietiek bonusu\n"
                        f"Требуется: {qr_entry.amount} pts\nУ клиента: {target_user.bonus_points} pts"
                    )
                    return

                target_user.bonus_points -= qr_entry.amount
                qr_entry.is_used = True
                qr_entry.used_at = datetime.utcnow()

                log = PointsLog(
                    user_id=target_user.id,
                    points=-qr_entry.amount,
                    reason_ru="Списание в баре",
                    reason_lv="Norakstīšana bārā",
                )
                db.add(log)

                bar_admin_name = db_user.first_name or db_user.username or f"ID{db_user.telegram_id}"
                db.commit()
                await update.message.reply_text(
                    f"✅ Списано {qr_entry.amount} бонусов у клиента / Norakstīti {qr_entry.amount} bonusi klientam\n"
                    f"💰 Баланс клиента: {target_user.bonus_points} pts\n"
                    f"🍸 Админ: {bar_admin_name}" if lang == "ru" else
                    f"✅ Norakstīti {qr_entry.amount} bonusi klientam\n"
                    f"💰 Klienta bilance: {target_user.bonus_points} pts\n"
                    f"🍸 Admins: {bar_admin_name}"
                )
                # Notify client about deduction
                client_lang = target_user.language or "ru"
                try:
                    await context.application.bot.send_message(
                        chat_id=target_user.telegram_id,
                        text=(
                            f"🍸 Списано {qr_entry.amount} бонусов в баре / Norakstīti {qr_entry.amount} bonusi bārā\n"
                            f"💰 Баланс: {target_user.bonus_points} pts\n"
                            f"🍸 Админ: {bar_admin_name}"
                        ) if client_lang == "ru" else (
                            f"🍸 Norakstīti {qr_entry.amount} bonusi bārā\n"
                            f"💰 Bilance: {target_user.bonus_points} pts\n"
                            f"🍸 Admins: {bar_admin_name}"
                        ),
                    )
                except Exception:
                    pass
            else:
                award_amount = qr_entry.amount
                db_user.bonus_points += award_amount
                qr_entry.is_used = True
                qr_entry.used_at = datetime.utcnow()

                log = PointsLog(
                    user_id=db_user.id,
                    points=award_amount,
                    reason_ru="Начисление за заказ в баре",
                    reason_lv="Pieskaitīts par pasūtījumu bārā",
                )
                db.add(log)
                db.commit()
                await update.message.reply_text(
                    f"✅ Начислено {award_amount} бонусов / Pieskaitīti {award_amount} bonusi\n"
                    f"💰 Баланс: {db_user.bonus_points} pts"
                )
                # Notify bar admin who created the QR
                if qr_entry.bar_admin and qr_entry.bar_admin.telegram_id:
                    admin_lang = qr_entry.bar_admin.language or "ru"
                    client_name = db_user.first_name or db_user.username or f"ID{db_user.telegram_id}"
                    try:
                        await context.application.bot.send_message(
                            chat_id=qr_entry.bar_admin.telegram_id,
                            text=(
                                f"✅ Клиент {client_name} активировал QR на {award_amount} бонусов\n"
                                f"💰 Начислено: +{award_amount} pts"
                            ) if admin_lang == "ru" else (
                                f"✅ Klients {client_name} aktivizēja QR uz {award_amount} bonusiem\n"
                                f"💰 Pieskaitīts: +{award_amount} pts"
                            ),
                        )
                    except Exception:
                        pass
        finally:
            db.close()
        return

    # Check if user is in contact_admin_mode (sending message to admin)
    if context.user_data.get("contact_admin_mode"):
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not db_user:
                return
            lang = db_user.language or "ru"
            context.user_data.pop("contact_admin_mode", None)

            # Forward message to all admins
            admin_users = db.query(User).filter(User.role.in_(["admin", "super_admin"])).all()
            user_info = f"👤 {db_user.first_name or '—'} (@{db_user.username or '—'}, ID: {db_user.id})"
            sent = 0
            for admin in admin_users:
                try:
                    await context.bot.send_message(
                        chat_id=admin.telegram_id,
                        text=f"📩 *Сообщение от пользователя*\n\n{user_info}\n\n{text}",
                        parse_mode="Markdown",
                    )
                    sent += 1
                except Exception:
                    pass

            await update.message.reply_text(
                "✅ Твоё сообщение отправлено администратору! Ожидай ответа." if lang == "ru"
                else "✅ Tava ziņa nosūtīta administratoram! Gaidi atbildi."
            )
            return
        finally:
            db.close()

    # Check if user is in bar_client_mode (entering amount for bar bonus usage)
    client_mode = context.user_data.get("bar_client_mode")
    if client_mode == "pending_amount":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❗ Введи положительное число / Ievadi pozitīvu skaitli")
            return

        amount = int(text)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not user:
                return

            if user.points_balance < amount:
                await update.message.reply_text(
                    f"❌ Недостаточно бонусов / Nepietiek bonusu\n"
                    f"Доступно / Pieejams: {user.points_balance} pts"
                )
                return

            lang = user.language or "ru"
            code = secrets.token_urlsafe(16)[:24]
            qr_entry = PointsQR(
                code=code,
                action="use",
                user_id=user.id,
                amount=amount,
            )
            db.add(qr_entry)
            db.commit()

            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={code}"
            text_ru = f"🍸 Покажи этот QR-код бармену для списания {amount} бонусов\n\nКод: `{code}`"
            text_lv = f"🍸 Parādi šo QR kodu barmanam, lai norakstītu {amount} bonusus\n\nKods: `{code}`"
            caption = f"{text_ru}\n\n{text_lv}" if lang == "ru" else f"{text_lv}\n\n{text_ru}"

            await update.message.reply_photo(
                photo=qr_url,
                caption=caption,
                parse_mode="Markdown",
            )

            context.user_data.pop("bar_client_mode", None)
            context.user_data.pop("bar_client_user_id", None)
        finally:
            db.close()
        return

    # Check if user is in bar_admin_mode (entering amount for deduct/earn)
    admin_mode = context.user_data.get("bar_admin_mode")
    if admin_mode in ("deduct", "earn"):
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❗ Введи положительное число / Ievadi pozitīvu skaitli")
            return

        amount = int(text)
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not db_user:
                return

            bar_admin_check = db_user and (db_user.role == "bar_admin" or has_permission(db_user.role, "admin"))
            if not bar_admin_check:
                return

            lang = db_user.language or "ru"

            if admin_mode == "earn":
                points = amount * POINTS["BAR_EARN_PER_EUR"]
                action = "earn"
                label_ru = f"📤 Начисление {points} бонусов за заказ {amount} EUR"
                label_lv = f"📤 Pieskaitīt {points} bonusus par pasūtījumu {amount} EUR"
            else:
                points = amount
                action = "use"
                label_ru = f"📥 Списание {points} бонусов"
                label_lv = f"📥 Norakstīt {points} bonusus"

            code = secrets.token_urlsafe(16)[:24]
            qr_entry = PointsQR(
                code=code,
                action=action,
                user_id=db_user.id,
                bar_admin_id=db_user.id,
                amount=points,
            )
            db.add(qr_entry)
            db.commit()

            from bot.keyboards.inline import bar_confirm_keyboard
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={code}"
            msg_text = f"{label_ru}\n\n{label_lv}" if lang == "ru" else f"{label_lv}\n\n{label_ru}"
            msg_text += f"\n\n🔑 Код: `{code}`\n\nПопроси клиента отсканировать QR или ввести код через /scan"
            await update.message.reply_photo(
                photo=qr_url,
                caption=msg_text,
                parse_mode="Markdown",
                reply_markup=bar_confirm_keyboard(code, action),
            )

            context.user_data.pop("bar_admin_mode", None)
        finally:
            db.close()
        return

    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = db_user.language if db_user else "ru"
    finally:
        db.close()

    commands_ru = {
        "📅 Афиша": "menu_events",
        "⭐ Бонусы": "menu_bonuses",
        "🎭 Специалисты": "menu_specialists",
        "🎧 DJ Миксы": "menu_mixes",
        "👤 Профиль": "menu_profile",
        "👥 Пригласи друга": "menu_referrals",
        "💕 Знакомства": "menu_dating",
        "🎤 Я – специалист": "menu_dj_register",
        "📰 Лента": "menu_feed",
        "ℹ️ Помощь": "menu_help",
        "🍸 Bar Admin": "menu_bar_admin",
    }
    commands_lv = {
        "📅 Afiša": "menu_events",
        "⭐ Bonusi": "menu_bonuses",
        "🎭 Speciālisti": "menu_specialists",
        "🎧 Miksi": "menu_mixes",
        "👤 Profils": "menu_profile",
        "👥 Uzaicini draugu": "menu_referrals",
        "💕 Iepazīšanās": "menu_dating",
        "🎤 Es esmu speciālists": "menu_dj_register",
        "📰 Jaunumi": "menu_feed",
        "ℹ️ Palīdzība": "menu_help",
        "🍸 Bar Admin": "menu_bar_admin",
    }

    if text in ("📋 Меню", "📋 Menu"):
        await menu(update, context)
        return

    if text == "🌐 LV / RU" or text == "🌐 RU / LV":
        await language(update, context)
        return

    if text == "⚙️ Admin":
        from bot.handlers.admin import admin_panel
        await admin_panel(update, context)
        return

    if text == "🍸 Bar Admin":
        from bot.handlers.bar_admin import bar_admin_panel
        await bar_admin_panel(update, context)
        return

    if text in ("📸 Сканировать QR", "📸 Skenēt QR"):
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            lang = db_user.language if db_user else "ru"
        finally:
            db.close()

        text_ru = "📸 Отправь QR-код или введи код вручную:\n\nНапример: `/scan ABC123`\n\nИли просто отправь код текстом."
        text_lv = "📸 Nosūti QR kodu vai ievadi kodu manuāli:\n\nPiemēram: `/scan ABC123`\n\nVai vienkārši nosūti kodu tekstā."
        await update.message.reply_text(
            text_ru if lang == "ru" else text_lv,
            parse_mode="Markdown",
        )
        context.user_data["scan_mode"] = True
        return

    if text in commands_ru:
        category = commands_ru[text]
    elif text in commands_lv:
        category = commands_lv[text]
    elif text.startswith("📩") or text in ("📩 Администратору", "📩 Administratoram"):
        context.user_data["contact_admin_mode"] = True
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            lang = db_user.language if db_user else "ru"
        finally:
            db.close()
        await update.message.reply_text(
            "✏️ Напиши своё сообщение, и оно будет отправлено администратору.\n\n"
            "Отправь «—» чтобы отменить." if lang == "ru"
            else "✏️ Uzraksti savu ziņu, tā tiks nosūtīta administratoram.\n\n"
                 "Nosūti «—» lai atceltu."
        )
        return
    else:
        # Forward unhandled user messages to admins (contact feature)
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if db_user and db_user.role not in ("admin", "super_admin") and not context.user_data.get("admin_event_step") and not context.user_data.get("admin_edit_event") and not context.user_data.get("admin_edit_mix") and not context.user_data.get("admin_edit_spec") and not context.user_data.get("admin_points_action"):
                lang = db_user.language or "ru"
                admin_users = db.query(User).filter(User.role.in_(["admin", "super_admin"])).all()
                user_info = f"👤 {db_user.first_name or '—'} (@{db_user.username or '—'}, ID: {db_user.id})"
                sent = 0
                for admin in admin_users:
                    try:
                        await context.bot.send_message(
                            chat_id=admin.telegram_id,
                            text=f"💬 *Сообщение от пользователя*\n\n{user_info}\n\n{text}",
                            parse_mode="Markdown",
                        )
                        sent += 1
                    except Exception:
                        pass
                if sent > 0:
                    await update.message.reply_text(
                        "✅ Твоё сообщение отправлено администратору!" if lang == "ru"
                        else "✅ Tava ziņa nosūtīta administratoram!"
                    )
        finally:
            db.close()
        return

    if category == "menu_events":
        from bot.handlers.events import events
        await events(update, context)
    elif category == "menu_specialists":
        from bot.handlers.specialists import specialists
        await specialists(update, context)
    elif category == "menu_mixes":
        from bot.handlers.dj_mixes import mixes
        await mixes(update, context)
    elif category == "menu_bonuses":
        from bot.handlers.bonuses import bonuses
        await bonuses(update, context)
    elif category == "menu_profile":
        from bot.handlers.profile import profile
        await profile(update, context)
    elif category == "menu_referrals":
        from bot.handlers.referrals import referral
        await referral(update, context)
    elif category == "menu_help":
        await help_command(update, context)
    elif category == "menu_dating":
        from bot.handlers.dating import dating_menu
        await dating_menu(update, context)
    elif category == "menu_feed":
        from bot.handlers.feed import feed
        await feed(update, context)


def register(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^(menu_main|menu_help|menu_dating|lang_)"))
