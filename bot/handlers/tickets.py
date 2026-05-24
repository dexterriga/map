"""Ticket purchase and QR code handlers."""

import secrets
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User, Event, SoldTicket
from bot.keyboards.inline import back_keyboard
from bot.services.bonus_service import deduct_points


def generate_ticket_code() -> str:
    """Generate a unique 27-character ticket code."""
    return secrets.token_urlsafe(20)[:27]


async def buy_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language

        if data.startswith("ticket_points_confirm_"):
            parts = data.split("_")
            event_id = int(parts[3])
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                return
            cost = event.ticket_price_points or 0
            title = event.title_lv if lang == "lv" and event.title_lv else event.title
            text = (
                f"🎫 *{title}*\n\n"
                f"💰 {'Стоимость' if lang == 'ru' else 'Cena'}: {cost} pts\n"
                f"💳 {'У тебя' if lang == 'ru' else 'Tev ir'}: {user.points_balance} pts\n\n"
                f"{'Подтверди покупку:' if lang == 'ru' else 'Apstiprini pirkumu:'}"
            )
            buttons = [
                [InlineKeyboardButton("✅ Купить / Nopirkt", callback_data=f"ticket_points_execute_{event_id}")],
                [InlineKeyboardButton("❌ Отмена / Atcelt", callback_data=f"event_{event_id}")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
            ]
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

        elif data.startswith("ticket_points_execute_"):
            parts = data.split("_")
            event_id = int(parts[3])
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                return
            cost = event.ticket_price_points or 0
            if user.points_balance < cost:
                await query.edit_message_text(
                    f"❌ {'Недостаточно баллов!' if lang == 'ru' else 'Nepietiek punktu!'}\n\n"
                    f"{'Нужно' if lang == 'ru' else 'Nepieciešams'}: {cost} pts\n"
                    f"{'У тебя' if lang == 'ru' else 'Tev ir'}: {user.points_balance} pts",
                    reply_markup=back_keyboard(f"event_{event_id}"),
                )
                return
            code = generate_ticket_code()
            ticket = SoldTicket(
                event_id=event_id,
                user_id=user.id,
                unique_code=code,
                points_spent=cost,
                is_used=False,
            )
            db.add(ticket)
            deduct_points(db, user, cost, f"Покупка билета: {event.title}",
                          f"Biļetes iegāde: {event.title}")
            db.commit()
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={code}"
            text = (
                f"✅ *{'Билет куплен!' if lang == 'ru' else 'Biļete nopirkta!'}*\n\n"
                f"🎫 {'Код' if lang == 'ru' else 'Kods'}: `{code}`\n"
                f"📅 {event.title}\n"
                f"💰 -{cost} pts\n\n"
                f"🖼 [{'Показать QR-код' if lang == 'ru' else 'Rādīt QR kodu'}]({qr_url})\n\n"
                f"📋 {'Покажи этот код на входе' if lang == 'ru' else 'Uzrādi šo kodu pie ieejas'}"
            )
            await query.edit_message_text(
                text, parse_mode="Markdown",
                reply_markup=back_keyboard("menu_main"),
            )

        elif data.startswith("ticket_verify_"):
            code = data.split("_", 2)[2]
            ticket = db.query(SoldTicket).filter(SoldTicket.unique_code == code).first()
            if not ticket:
                await query.answer("❌ Билет не найден!" if lang == "ru" else "❌ Biļete nav atrasta!", show_alert=True)
                return
            ev = db.query(Event).filter(Event.id == ticket.event_id).first()
            buyer = db.query(User).filter(User.id == ticket.user_id).first()
            status = "✅ Использован" if ticket.is_used else "🟢 Действителен"
            msg = (
                f"🎫 *{'Билет' if lang == 'ru' else 'Biļete'}*\n"
                f"{'Статус' if lang == 'ru' else 'Statuss'}: {status}\n"
                f"{'Событие' if lang == 'ru' else 'Pasākums'}: {ev.title if ev else '—'}\n"
                f"{'Покупатель' if lang == 'ru' else 'Pircējs'}: {buyer.first_name or buyer.username or '—'}\n"
                f"{'Код' if lang == 'ru' else 'Kods'}: `{code}`\n"
                f"{'Куплен' if lang == 'ru' else 'Nopirkts'}: {ticket.purchased_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=back_keyboard("admin_panel"))

    finally:
        db.close()


async def verify_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify a ticket by code (/verify <code>)."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language
        from bot.utils.helpers import has_permission
        if not has_permission(user.role, "moderator"):
            await update.message.reply_text("🚫 Только для модераторов.")
            return
        if not context.args:
            await update.message.reply_text(
                "Используй: /verify <код>" if lang == "ru" else "Izmanto: /verify <kods>"
            )
            return
        code = context.args[0]
        ticket = db.query(SoldTicket).filter(SoldTicket.unique_code == code).first()
        if not ticket:
            await update.message.reply_text(
                "❌ Билет не найден." if lang == "ru" else "❌ Biļete nav atrasta."
            )
            return
        ev = db.query(Event).filter(Event.id == ticket.event_id).first()
        buyer = db.query(User).filter(User.id == ticket.user_id).first()
        status = "✅ Использован" if ticket.is_used else "🟢 Действителен"
        msg = (
            f"🎫 *{'Билет' if lang == 'ru' else 'Biļete'}*\n"
            f"{'Статус' if lang == 'ru' else 'Statuss'}: {status}\n"
            f"{'Событие' if lang == 'ru' else 'Pasākums'}: {ev.title if ev else '—'}\n"
            f"{'Покупатель' if lang == 'ru' else 'Pircējs'}: {buyer.first_name or buyer.username or '—'}\n"
            f"💰 {ticket.points_spent} pts\n"
            f"🆔 `{code}`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    finally:
        db.close()


async def use_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark a ticket as used (/use <code>)."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language
        from bot.utils.helpers import has_permission
        if not has_permission(user.role, "moderator"):
            await update.message.reply_text("🚫 Только для модераторов.")
            return
        if not context.args:
            await update.message.reply_text(
                "Используй: /use <код>" if lang == "ru" else "Izmanto: /use <kods>"
            )
            return
        code = context.args[0]
        ticket = db.query(SoldTicket).filter(SoldTicket.unique_code == code).first()
        if not ticket:
            await update.message.reply_text(
                "❌ Билет не найден." if lang == "ru" else "❌ Biļete nav atrasta."
            )
            return
        if ticket.is_used:
            await update.message.reply_text(
                "❌ Билет уже использован." if lang == "ru" else "❌ Biļete jau izmantota."
            )
            return
        ticket.is_used = True
        ticket.used_at = __import__("datetime").datetime.utcnow()
        db.commit()
        await update.message.reply_text(
            "✅ Билет отмечен как использованный!" if lang == "ru" else "✅ Biļete atzīmēta kā izmantota!"
        )
    finally:
        db.close()


def register(application):
    application.add_handler(CommandHandler("verify", verify_ticket))
    application.add_handler(CommandHandler("use", use_ticket))
    application.add_handler(CallbackQueryHandler(
        buy_ticket_callback,
        pattern=r"^(ticket_points_confirm_|ticket_points_execute_|ticket_verify_)",
    ))
