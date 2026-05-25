"""Bar admin handler — QR-based points deduct/earn flow."""

import secrets
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, PointsQR, PointsLog
from bot.keyboards.inline import bar_admin_keyboard, bar_confirm_keyboard, main_menu_keyboard
from bot.utils.helpers import has_permission


def _get_bar_admin(db_user):
    return db_user and (db_user.role == "bar_admin" or has_permission(db_user.role, "admin"))


async def bar_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not _get_bar_admin(db_user):
            msg = "🚫 У вас нет доступа / Jums nav piekļuves"
            if update.callback_query:
                await update.callback_query.edit_message_text(msg)
            else:
                await update.message.reply_text(msg)
            return

        lang = db_user.language if db_user else "ru"
        text_ru = "🍸 *Bar Admin панель*\n\nВыбери действие:"
        text_lv = "🍸 *Bar Admin panelis*\n\nIzvēlies darbību:"
        text = text_ru if lang == "ru" else text_lv

        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=bar_admin_keyboard(lang))
        else:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=bar_admin_keyboard(lang))
    finally:
        db.close()


async def bar_scan_deduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bar admin scans client's QR code to deduct points."""
    query = update.callback_query
    await query.answer()
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not _get_bar_admin(db_user):
            await query.edit_message_text("🚫 Доступ запрещён / Piekļuve liegta")
            return

        lang = db_user.language if db_user else "ru"
        context.user_data["bar_admin_mode"] = "deduct"
        text_ru = "📥 Введи количество бонусов для списания с клиента:\n\nПример: `50`"
        text_lv = "📥 Ievadi bonusu daudzumu norakstīšanai no klienta:\n\nPiemērs: `50`"
        await query.edit_message_text(
            text_ru if lang == "ru" else text_lv,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    finally:
        db.close()


async def bar_earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bar admin generates QR for client to earn points."""
    query = update.callback_query
    await query.answer()
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not _get_bar_admin(db_user):
            await query.edit_message_text("🚫 Доступ запрещён / Piekļuve liegta")
            return

        lang = db_user.language if db_user else "ru"
        context.user_data["bar_admin_mode"] = "earn"
        text_ru = "📤 Введи сумму заказа в EUR для начисления бонусов:\n\nНачисление: 2 pts за 1 EUR\nПример: `25`"
        text_lv = "📤 Ievadi pasūtījuma summu EUR bonusu pieskaitīšanai:\n\nPieskaita: 2 pts par 1 EUR\nPiemērs: `25`"
        await query.edit_message_text(
            text_ru if lang == "ru" else text_lv,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    finally:
        db.close()


async def bar_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute a PointsQR action (called after bar admin confirms)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_", 3)
    if len(parts) < 4:
        await query.edit_message_text("❗ Ошибка / Kļūda")
        return

    action = parts[2]
    code = parts[3]

    db = SessionLocal()
    try:
        qr_entry = db.query(PointsQR).filter(PointsQR.code == code, PointsQR.is_used == False).first()
        if not qr_entry:
            await query.edit_message_text(
                "❗ QR-код не найден или уже использован / QR kods nav atrasts vai jau izmantots",
                reply_markup=main_menu_keyboard("ru"),
            )
            return

        lang = "ru"
        bar_admin = db.query(User).filter(User.id == qr_entry.bar_admin_id).first()
        if bar_admin:
            lang = bar_admin.language or "ru"

        if action == "use":
            # Client needs to scan — we show instructions
            text_ru = "📤 QR-код готов для списания бонусов!\n\nПопроси клиента отсканировать код через /scan или ввести код вручную."
            text_lv = "📤 QR kods gatavs bonusu norakstīšanai!\n\nLūdz klientam skenēt kodu ar /scan vai ievadīt kodu manuāli."
            await query.edit_message_text(
                f"{text_ru}\n\n{text_lv}" if lang == "ru" else f"{text_lv}\n\n{text_ru}",
                reply_markup=main_menu_keyboard(lang),
            )
        else:
            # earn — show instructions
            text_ru = "📥 QR-код отправлен клиенту для начисления бонусов.\n\nКлиент должен отсканировать код через /scan."
            text_lv = "📥 QR kods nosūtīts klientam bonusu pieskaitīšanai.\n\nKlientam jāskenē kods ar /scan."
            await query.edit_message_text(
                f"{text_ru}\n\n{text_lv}" if lang == "ru" else f"{text_lv}\n\n{text_ru}",
                reply_markup=main_menu_keyboard(lang),
            )
    finally:
        db.close()


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Client/bar admin scans a QR code or enters a code manually."""
    args = context.args
    db = SessionLocal()
    try:
        user_tg = update.effective_user
        db_user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not db_user:
            await update.message.reply_text("❗ Сначала зарегистрируйся / Vispirms reģistrējies")
            return

        lang = db_user.language or "ru"

        if not args:
            text_ru = "📸 Отсканируй QR-код или введи код после /scan\n\nПример: `/scan ABC123`"
            text_lv = "📸 Skenē QR kodu vai ievadi kodu pēc /scan\n\nPiemērs: `/scan ABC123`"
            await update.message.reply_text(
                text_ru if lang == "ru" else text_lv,
                parse_mode="Markdown",
            )
            return

        code = args[0]

        qr_entry = db.query(PointsQR).filter(PointsQR.code == code, PointsQR.is_used == False).first()
        if not qr_entry:
            await update.message.reply_text(
                "❗ Код не найден или уже использован / Kods nav atrasts vai jau izmantots"
            )
            return

        if qr_entry.action == "use":
            # Client wants to spend points — deduct from the QR owner (client), not the scanner
            target_user = db.query(User).filter(User.id == qr_entry.user_id).first()
            if not target_user:
                await update.message.reply_text("❗ Ошибка: пользователь не найден / Kļūda: lietotājs nav atrasts")
                return

            if target_user.bonus_points < qr_entry.amount:
                await update.message.reply_text(
                    f"❌ У клиента недостаточно бонусов / Klientam nepietiek bonusu\n\n"
                    f"Требуется: {qr_entry.amount} pts\n"
                    f"У клиента: {target_user.bonus_points} pts"
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

        elif qr_entry.action == "earn":
            # Bar admin created this QR for client — credit the scanner (client)
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


def register(application):
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CallbackQueryHandler(bar_admin_panel, pattern=r"^bar_panel$"))
    application.add_handler(CallbackQueryHandler(bar_scan_deduct, pattern=r"^bar_scan_deduct$"))
    application.add_handler(CallbackQueryHandler(bar_earn, pattern=r"^bar_earn$"))
    application.add_handler(CallbackQueryHandler(bar_execute, pattern=r"^bar_execute_"))
