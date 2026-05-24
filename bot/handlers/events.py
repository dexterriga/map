"""Events/afisha handlers."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session

from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.inline import (
    events_keyboard, event_detail_keyboard, back_keyboard
)
from bot.services.event_service import (
    get_upcoming_events, get_event_by_id, save_event_for_user, get_featured_events
)
from bot.utils.helpers import format_datetime, format_price
from bot.config import POINTS


def _format_events_list(events, lang):
    """Build a formatted text list of events with date/time/venue/image."""
    lines = []
    for ev in events:
        title = ev.title_lv if lang == "lv" and ev.title_lv else ev.title
        dt = ev.date.strftime("%d.%m.%Y %H:%M")
        venue = ev.venue or "TBA"
        price = f"{ev.price} EUR" if ev.price else "—"
        line = f"📅 {dt} — *{title}*\n📍 {venue} | 🏷️ {price}"
        if ev.image_url:
            line += f"\n🖼 [{'Афиша' if lang == 'ru' else 'Afiša'}]({ev.image_url})"
        lines.append(line)
    return "\n\n".join(lines)


async def _send_pinned_event(update, context, event, lang):
    """Send pinned event card with image, date, venue, address."""
    title = event.title_lv if lang == "lv" and event.title_lv else event.title
    text = (
        f"📌 *{title}*\n\n"
        f"📆 {format_datetime(event.date)}\n"
        f"📍 {event.venue or 'TBA'}"
    )
    if event.address:
        text += f"\n🗺️ {event.address}"
    if event.price:
        text += f"\n🏷️ {format_price(event.price)}"

    if event.image_url:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=event.image_url,
            caption=text,
            parse_mode="Markdown",
        )
        desc = event.description_lv if lang == "lv" and event.description_lv else event.description
        if desc:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=desc,
                parse_mode="Markdown",
            )
    else:
        desc = event.description_lv if lang == "lv" and event.description_lv else event.description
        if desc:
            text += f"\n\n{desc}"
        await update.message.reply_text(text, parse_mode="Markdown")


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        lang = user.language if user else "ru"
        events_list = get_upcoming_events(db, limit=5)
        if not events_list:
            await update.message.reply_text(
                "📅 *Афиша событий*\n\n😕 Пока нет предстоящих событий.\n\n"
                "Следи за обновлениями — скоро появятся новые вечеринки!"
                if lang == "ru"
                else "📅 *Pasākumu afiša*\n\n😕 Pašlaik nav gaidāmu pasākumu.\n\n"
                     "Seko jaunumiem — drīz parādīsies jaunas ballītes!",
                parse_mode="Markdown",
                reply_markup=back_keyboard("menu_main"),
            )
            return

        # Send pinned events at the top with image, date, venue
        pinned = get_featured_events(db, limit=3)
        for ev in pinned:
            await _send_pinned_event(update, context, ev, lang)

        header = "📅 *Афиша событий*" if lang == "ru" else "📅 *Pasākumu afiša*"
        body = _format_events_list(events_list, lang)
        text = f"{header}\n\n{body}"
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=events_keyboard(events_list, 0, lang),
        )
    finally:
        db.close()


async def events_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        lang = user.language if user else "ru"

        if data == "menu_events":
            events_list = get_upcoming_events(db, limit=5)
            if not events_list:
                await query.edit_message_text(
                    "📅 *Афиша событий*\n\n😕 Пока нет предстоящих событий."
                    if lang == "ru"
                    else "📅 *Pasākumu afiša*\n\n😕 Pašlaik nav gaidāmu pasākumu.",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard("menu_main"),
                )
                return

            # Send pinned event as new message (inline callback can't edit to add photo)
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
                    await query.message.reply_text(text, parse_mode="Markdown")

            header = "📅 *Афиша событий*" if lang == "ru" else "📅 *Pasākumu afiša*"
            body = _format_events_list(events_list, lang)
            text = f"{header}\n\n{body}"
            await query.edit_message_text(
                text, parse_mode="Markdown",
                reply_markup=events_keyboard(events_list, 0, lang),
            )
        elif data.startswith("event_toggle_featured_"):
            from bot.utils.helpers import has_permission as _hp
            event_id = int(data.split("_")[3])
            event = get_event_by_id(db, event_id)
            if event and user and _hp(user.role, "admin"):
                event.is_featured = not event.is_featured
                db.commit()
                status = "📌 Закреплено / Piesprausts" if event.is_featured else "❌ Откреплено / Atsprausts"
                await query.answer(status, show_alert=True)
                title = event.title_lv if lang == "lv" and event.title_lv else event.title
                desc = event.description_lv if lang == "lv" and event.description_lv else event.description
                bonus_info = ""
                if event.points_bonus:
                    bonus_info = f"🎁 *Бонус:* +{event.points_bonus} points"
                ticket_info = ""
                if event.ticket_price_points and event.ticket_price_points > 0:
                    ticket_info = f"🎫 *Билет:* {event.price} EUR / {event.ticket_price_points} pts"
                elif event.price:
                    ticket_info = f"🎫 *Билет:* {event.price} EUR"
                image_info = ""
                if event.image_url:
                    image_info = f"\n🖼 [Смотреть афишу]({event.image_url})"
                detail_text = (
                    f"📅 *{title}*{image_info}\n\n"
                    f"📆 {format_datetime(event.date)}\n"
                    f"📍 {event.venue or 'TBA'}\n"
                    f"🏷️ {format_price(event.price)}\n"
                    f"{ticket_info}\n\n"
                    f"{desc or ''}\n\n"
                    f"{bonus_info}"
                )
                await query.edit_message_text(
                    detail_text, parse_mode="Markdown",
                    reply_markup=event_detail_keyboard(
                        event_id, event.ticket_url, event.ticket_price_points,
                        is_admin=True, is_featured=event.is_featured,
                    ),
                )
        elif data.startswith("event_"):
            event_id = int(data.split("_")[1])
            event = get_event_by_id(db, event_id)
            if event:
                title = event.title_lv if lang == "lv" and event.title_lv else event.title
                desc = event.description_lv if lang == "lv" and event.description_lv else event.description
                bonus_info = ""
                if event.points_bonus:
                    bonus_info = f"🎁 *Бонус:* +{event.points_bonus} points"
                ticket_info = ""
                if event.ticket_price_points and event.ticket_price_points > 0:
                    ticket_info = f"🎫 *Билет:* {event.price} EUR / {event.ticket_price_points} pts"
                elif event.price:
                    ticket_info = f"🎫 *Билет:* {event.price} EUR"
                image_info = ""
                if event.image_url:
                    image_info = f"\n🖼 [Смотреть афишу]({event.image_url})"
                text = (
                    f"📅 *{title}*{image_info}\n\n"
                    f"📆 {format_datetime(event.date)}\n"
                    f"📍 {event.venue or 'TBA'}\n"
                    f"🏷️ {format_price(event.price)}\n"
                    f"{ticket_info}\n\n"
                    f"{desc or ''}\n\n"
                    f"{bonus_info}"
                )
                from bot.utils.helpers import has_permission as _hp
                is_admin = user and _hp(user.role, "admin")
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=event_detail_keyboard(event_id, event.ticket_url, event.ticket_price_points, is_admin=is_admin, is_featured=event.is_featured),
                )
        elif data.startswith("event_save_"):
            event_id = int(data.split("_")[2])
            save_event_for_user(db, user.id, event_id)
            await query.answer("✅ Сохранено / Saglabāts!", show_alert=True)
        elif data.startswith("event_share_"):
            event_id = int(data.split("_")[2])
            event = get_event_by_id(db, event_id)
            if event:
                share_text = f"🎉 {event.title}\n📆 {format_datetime(event.date)}\n📍 {event.venue}"
                await query.edit_message_text(
                    f"📤 *Поделиться:*\n\n```\n{share_text}\n```",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard("menu_events"),
                )
        elif data.startswith("events_page_"):
            page = int(data.split("_")[2])
            events_list = get_upcoming_events(db, limit=5, offset=page * 5)
            header = "📅 *Афиша событий*" if lang == "ru" else "📅 *Pasākumu afiša*"
            body = _format_events_list(events_list, lang)
            text = f"{header}\n\n{body}"
            await query.edit_message_text(
                text, parse_mode="Markdown",
                reply_markup=events_keyboard(events_list, page, lang),
            )
        elif data.startswith("event_bonus_"):
            event_id = int(data.split("_")[2])
            event = get_event_by_id(db, event_id)
            if event and event.points_bonus:
                from bot.services.bonus_service import award_points
                if user:
                    award_points(db, user, event.points_bonus,
                                 f"Бонус за событие: {event.title}",
                                 f"Bonuss par pasākumu: {event.title_lv or event.title}",
                                 reference_type="event", reference_id=event_id)
                    await query.answer(
                        f"🎉 +{event.points_bonus} points!",
                        show_alert=True
                    )
    finally:
        db.close()


def register(application):
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CallbackQueryHandler(
        events_callback,
        pattern=r"^(menu_events|event_(?:\d+|save_|share_|bonus_|toggle_featured_)|events_page_)",
    ))
