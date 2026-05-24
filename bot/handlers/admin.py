"""Admin panel handlers with RBAC."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.orm import Session
from datetime import datetime

from bot.database import SessionLocal
from bot.models import User, AuditLog, AdminAction
from bot.config import ROLE_NAMES_RU, ROLE_NAMES_LV
from bot.keyboards.inline import (
    admin_keyboard, admin_users_actions_keyboard,
    role_selection_keyboard, back_keyboard, confirm_keyboard
)
from bot.utils.helpers import has_permission, get_role_level
from bot.services.analytics_service import (
    get_total_users, get_active_users, get_blocked_users,
    get_total_points_earned, get_total_points_spent,
    get_total_referrals, get_upcoming_events_count,
    get_total_bookings, get_pending_bookings,
    get_top_mixes, get_registration_stats,
)


def admin_check(user) -> bool:
    """Check if user has admin permissions (Admin or Super Admin)."""
    return has_permission(user.role, "admin")


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            await update.message.reply_text("🚫 Доступ запрещён. Только для администраторов.")
            return
        lang = user.language
        await update.message.reply_text(
            "⚙️ *Админ-панель*" if lang == "ru" else "⚙️ *Admin panelis*",
            parse_mode="Markdown",
            reply_markup=admin_keyboard(),
        )
    finally:
        db.close()


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_tg = update.effective_user
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            await query.edit_message_text("🚫 Доступ запрещён.")
            return
        lang = user.language

        if data == "admin_panel":
            await query.edit_message_text(
                "⚙️ *Админ-панель*" if lang == "ru" else "⚙️ *Admin panelis*",
                parse_mode="Markdown",
                reply_markup=admin_keyboard(),
            )
        elif data == "admin_users":
            await _admin_users(query, db, lang)
        elif data.startswith("admin_user_"):
            target_id = int(data.split("_")[2])
            target_user = db.query(User).filter(User.id == target_id).first()
            if target_user:
                role = ROLE_NAMES_LV.get(target_user.role, target_user.role) if lang == "lv" else ROLE_NAMES_RU.get(target_user.role, target_user.role)
                status = "🔒 Заблокирован / Bloķēts" if target_user.is_blocked else "✅ Активен / Aktīvs"
                text = (
                    f"👤 *{target_user.first_name or '—'} (@{target_user.username or '—'})*\n"
                    f"Роль / Loma: {role}\n"
                    f"Статус / Statuss: {status}\n"
                    f"💰 {target_user.points_balance} pts\n"
                    f"📅 ID: {target_user.id} (TG: {target_user.telegram_id})"
                )
                from bot.keyboards.inline import admin_users_actions_keyboard
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=admin_users_actions_keyboard(target_id),
                )
        elif data == "admin_events":
            await _admin_events(query, db, lang)
        elif data == "admin_events_create":
            await _admin_event_start(query, context, lang)
        elif data == "admin_events_create_cancel":
            context.user_data.pop("admin_event_data", None)
            await _admin_events(query, db, lang)
        elif data == "admin_specialists":
            await _admin_specialists(query, db, lang)
        elif data == "admin_mixes":
            await _admin_mixes(query, db, lang)
        elif data.startswith("admin_mix_edit_"):
            from bot.models import DjMix
            from bot.keyboards.inline import admin_mix_edit_keyboard
            mix_id = int(data.split("_")[3])
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                text = (
                    f"🎧 *{mix.title}*\n\n"
                    f"DJ: {mix.artist_name or '—'}\n"
                    f"🎵 Жанр: {mix.genre or '—'}\n"
                    f"{'Статус' if lang == 'ru' else 'Statuss'}: {mix.moderation_status}\n"
                    f"👁️ {mix.plays_count}\n\n"
                    f"{mix.description or ''}"
                )
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=admin_mix_edit_keyboard(mix_id),
                )
        elif data.startswith("admin_mix_setfield_"):
            parts = data.split("_", 4)
            mix_id = int(parts[3])
            field = parts[4]
            context.user_data["admin_edit_mix"] = {"id": mix_id, "field": field}
            field_names = {
                "title": "название / nosaukums",
                "genre": "жанр / žanrs",
                "artist_name": "имя DJ / DJ vārds",
                "description": "описание / aprakstu",
            }
            label = field_names.get(field, field)
            await query.edit_message_text(
                f"✏️ Введи новое значение для *{label}*:" if lang == "ru"
                else f"✏️ Ievadi jauno vērtību *{label}*:",
                parse_mode="Markdown",
            )
        elif data.startswith("admin_mix_publish_"):
            from bot.models import DjMix
            mix_id = int(data.split("_")[3])
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                mix.moderation_status = "approved"
                mix.is_published = True
                db.commit()
                await query.answer("✅ Микс опубликован!" if lang == "ru" else "✅ Mikss publicēts!", show_alert=True)
                await _admin_mixes(query, db, lang)
        elif data.startswith("admin_mix_reject_"):
            from bot.models import DjMix
            mix_id = int(data.split("_")[3])
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                mix.moderation_status = "rejected"
                db.commit()
                await query.answer("❌ Микс отклонён!" if lang == "ru" else "❌ Mikss noraidīts!", show_alert=True)
                await _admin_mixes(query, db, lang)
        elif data.startswith("admin_mix_delete_"):
            from bot.models import DjMix
            mix_id = int(data.split("_")[3])
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                db.delete(mix)
                db.commit()
                await query.answer("🗑 Микс удалён!" if lang == "ru" else "🗑 Mikss dzēsts!", show_alert=True)
                await _admin_mixes(query, db, lang)
        elif data == "admin_upload_mix":
            context.user_data["awaiting_mix_upload"] = True
            await query.message.reply_text(
                "📤 *Публикация микса*\n\n"
                "Отправь *MP3 файл* с описанием в подписи к файлу,\n"
                "или напиши текст в формате:\n"
                "`Название | Жанр | Ссылка | Описание`\n\n"
                "Пример:\n"
                "`Summer Vibes | House | https://soundcloud.com/... | Мой летний микс`"
                if lang == "ru" else
                "📤 *Miksa publicēšana*\n\n"
                "Nosūti *MP3 failu* ar aprakstu pielikumā,\n"
                "vai uzraksti tekstu formātā:\n"
                "`Nosaukums | Žanrs | Saite | Apraksts`\n\n"
                "Piemērs:\n"
                "`Summer Vibes | House | https://soundcloud.com/... | Mans vasaras mikss`",
                parse_mode="Markdown",
            )
        elif data == "admin_rewards":
            await _admin_rewards(query, db, lang)
        elif data == "admin_rss":
            await _admin_rss(query, db, lang)
        elif data == "admin_bookings":
            await _admin_bookings(query, db, lang)
        elif data == "admin_analytics":
            await _admin_analytics(query, db, lang)
        elif data == "admin_log":
            await _admin_log(query, db, lang)
        elif data == "admin_bar_earn":
            context.user_data["bar_admin_mode"] = "earn"
            text_ru = "📤 Введи сумму заказа в EUR для начисления бонусов:\n\nНачисление: 2 pts за 1 EUR\nПример: `25`"
            text_lv = "📤 Ievadi pasūtījuma summu EUR bonusu pieskaitīšanai:\n\nPieskaita: 2 pts par 1 EUR\nPiemērs: `25`"
            await query.edit_message_text(
                text_ru if lang == "ru" else text_lv,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]),
            )
        elif data.startswith("admin_points_add_"):
            target_id = int(data.split("_")[3])
            context.user_data["admin_action"] = ("add_points", target_id)
            await _ask_points_amount(query, context, "add", lang)
        elif data.startswith("admin_points_sub_"):
            target_id = int(data.split("_")[3])
            context.user_data["admin_action"] = ("sub_points", target_id)
            await _ask_points_amount(query, context, "sub", lang)
        elif data.startswith("admin_block_"):
            target_id = int(data.split("_")[2])
            await _confirm_action(query, context, "block", target_id, lang)
        elif data.startswith("admin_unblock_"):
            target_id = int(data.split("_")[2])
            await _confirm_action(query, context, "unblock", target_id, lang)
        elif data.startswith("admin_change_role_"):
            target_id = int(data.split("_")[3])
            if get_role_level(user.role) < 4:
                await query.answer("🚫 Только Super Admin может менять роли!", show_alert=True)
                return
            await query.edit_message_text(
                "👑 Выбери новую роль / Izvēlies jaunu lomu:",
                reply_markup=role_selection_keyboard(target_id),
            )
        elif data.startswith("set_role_"):
            _, _, target_id_str, new_role = data.split("_", 3)
            target_id = int(target_id_str)
            if get_role_level(user.role) < 4:
                await query.answer("🚫 Недостаточно прав!", show_alert=True)
                return
            target_user = db.query(User).filter(User.id == target_id).first()
            if target_user:
                old_role = target_user.role
                target_user.role = new_role
                _log_admin_action(db, user, f"Сменил роль: {old_role} -> {new_role}",
                                  target_id=target_user.telegram_id)
                db.commit()
                await query.answer(f"✅ Роль изменена на {new_role}!", show_alert=True)
                await _admin_users(query, db, lang)
        elif data.startswith("confirm_block_"):
            target_id = int(data.split("_")[2])
            target_user = db.query(User).filter(User.id == target_id).first()
            if target_user:
                target_user.is_blocked = True
                _log_admin_action(db, user, f"Заблокировал пользователя {target_user.telegram_id}",
                                  target_id=target_user.telegram_id)
                db.commit()
                await query.answer("✅ Пользователь заблокирован!", show_alert=True)
                await _admin_users(query, db, lang)
        elif data.startswith("confirm_unblock_"):
            target_id = int(data.split("_")[2])
            target_user = db.query(User).filter(User.id == target_id).first()
            if target_user:
                target_user.is_blocked = False
                _log_admin_action(db, user, f"Разблокировал пользователя {target_user.telegram_id}",
                                  target_id=target_user.telegram_id)
                db.commit()
                await query.answer("✅ Пользователь разблокирован!", show_alert=True)
                await _admin_users(query, db, lang)
        elif data.startswith("admin_event_edit_"):
            from bot.models import Event
            event_id = int(data.split("_")[3])
            event = db.query(Event).filter(Event.id == event_id).first()
            if event:
                from bot.keyboards.inline import admin_event_edit_keyboard
                title = event.title_lv if lang == "lv" and event.title_lv else event.title
                desc = event.description_lv if lang == "lv" and event.description_lv else event.description
                text = (
                    f"📅 *{title}*\n\n"
                    f"📆 {event.date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📍 {event.venue or '—'}\n"
                    f"🏷️ {event.price or 0} EUR\n"
                    f"🖼 {event.image_url or '—'}\n\n"
                    f"{desc or ''}"
                )
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=admin_event_edit_keyboard(event_id, is_featured=event.is_featured),
                )
        elif data.startswith("admin_event_setfield_"):
            parts = data.split("_", 4)
            event_id = int(parts[3])
            field = parts[4]
            context.user_data["admin_edit_event"] = {"id": event_id, "field": field}
            field_names = {
                "title": "название / nosaukums",
                "description": "описание / apraksts",
                "date": "дату в формате ДД.ММ.ГГГГ ЧЧ:ММ / datumu formātā DD.MM.GGGG ST:MM",
                "venue": "место / vietu",
                "address": "адрес / adresi",
                "price": "цену в EUR / cenu EUR",
                "ticket_price_points": "цену в бонусных баллах / cenu bonusa punktos",
                "ticket_url": "ссылку на билет / biļetes saiti",
                "image_url": "ссылку на изображение / attēla saiti",
            }
            label = field_names.get(field, field)
            await query.edit_message_text(
                f"✏️ Введи новое значение для *{label}*:" if lang == "ru"
                else f"✏️ Ievadi jauno vērtību *{label}*:",
                parse_mode="Markdown",
            )
        elif data.startswith("admin_event_toggle_featured_"):
            from bot.models import Event
            event_id = int(data.split("_")[4])
            event = db.query(Event).filter(Event.id == event_id).first()
            if event:
                event.is_featured = not event.is_featured
                db.commit()
                status = "📌 Закреплено / Piesprausts" if event.is_featured else "❌ Откреплено / Atsprausts"
                await query.answer(status, show_alert=True)
                from bot.keyboards.inline import admin_event_edit_keyboard
                title = event.title_lv if lang == "lv" and event.title_lv else event.title
                desc = event.description_lv if lang == "lv" and event.description_lv else event.description
                text = (
                    f"📅 *{title}*\n\n"
                    f"📆 {event.date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📍 {event.venue or '—'}\n"
                    f"🏷️ {event.price or 0} EUR\n"
                    f"🖼 {event.image_url or '—'}\n\n"
                    f"{desc or ''}"
                )
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=admin_event_edit_keyboard(event_id, is_featured=event.is_featured),
                )
        elif data.startswith("admin_spec_edit_"):
            from bot.models import Specialist
            spec_id = int(data.split("_")[3])
            spec = db.query(Specialist).filter(Specialist.id == spec_id).first()
            if spec:
                from bot.keyboards.inline import admin_specialist_edit_keyboard
                text = (
                    f"🎭 *{spec.stage_name or spec.name}*\n\n"
                    f"Категория: {spec.category}\n"
                    f"📍 {spec.city or '—'}\n"
                    f"⭐ Опыт: {spec.experience_years or '—'} лет\n"
                    f"🔧 {spec.specialization or '—'}\n"
                    f"💰 Цена от: {spec.price_from or '—'} EUR\n"
                    f"📞 {spec.contacts or '—'}\n"
                    f"📸 Instagram: {spec.instagram or '—'}\n"
                    f"🌐 Сайт: {spec.website or '—'}\n"
                    f"🖼 Фото: {spec.photo_url or '—'}\n\n"
                    f"{spec.description or ''}"
                )
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=admin_specialist_edit_keyboard(spec_id),
                )
        elif data.startswith("admin_spec_setfield_"):
            parts = data.split("_", 4)
            spec_id = int(parts[3])
            field = parts[4]
            context.user_data["admin_edit_spec"] = {"id": spec_id, "field": field}
            field_names = {
                "name": "имя / vārds",
                "category": "категорию / kategoriju",
                "description": "описание / aprakstu",
                "price_from": "цену / cenu",
                "photo_url": "ссылку на фото / foto saiti",
                "instagram": "Instagram",
                "website": "сайт / vietni",
            }
            label = field_names.get(field, field)
            await query.edit_message_text(
                f"✏️ Введи новое значение для *{label}*:" if lang == "ru"
                else f"✏️ Ievadi jauno vērtību *{label}*:",
                parse_mode="Markdown",
            )
        elif data.startswith("cancel_"):
            await query.edit_message_text("❌ Действие отменено.", reply_markup=admin_keyboard())
        elif data.startswith("confirm_points_"):
            action_type, target_id_str = context.user_data.get("admin_action", (None, None))
            amount = context.user_data.get("admin_points_amount", 0)
            if target_id_str and amount > 0:
                target_user = db.query(User).filter(User.id == target_id_str).first()
                if target_user:
                    from bot.services.bonus_service import award_points, deduct_points
                    if action_type == "add_points":
                        award_points(db, target_user, amount,
                                     f"Начислено администратором",
                                     f"Piešķirts administratoram",
                                     admin_id=user.telegram_id)
                        await query.answer(f"✅ +{amount} points!", show_alert=True)
                    else:
                        try:
                            deduct_points(db, target_user, amount,
                                          f"Списано администратором",
                                          f"Norakstīts administratoram",
                                          admin_id=user.telegram_id)
                            await query.answer(f"✅ -{amount} points!", show_alert=True)
                        except ValueError:
                            await query.answer("❌ Недостаточно баллов!", show_alert=True)
                    _log_admin_action(db, user, f"{'Начислил' if action_type == 'add_points' else 'Списал'} {amount} points",
                                      target_id=target_user.telegram_id)
                    await _admin_users(query, db, lang)
    finally:
        db.close()


async def _admin_users(query, db: Session, lang: str):
    total = db.query(User).count()
    users = db.query(User).order_by(User.registered_at.desc()).limit(20).all()
    lines = [f"👥 *Пользователи / Lietotāji:* ({total})"]

    from bot.services.referral_service import count_referrals
    for u in users:
        role = ROLE_NAMES_LV.get(u.role, u.role) if lang == "lv" else ROLE_NAMES_RU.get(u.role, u.role)
        status = "🔒" if u.is_blocked else "✅"
        refs = count_referrals(db, u)
        lines.append(f"{status} {u.first_name or '—'} (@{u.username or '—'}) — {role} — {u.points_balance} pts 👥{refs}")

    # Build user buttons for clickable list
    user_buttons = []
    for u in users[:10]:
        label = f"{'🔒' if u.is_blocked else '✅'} {u.first_name or u.username or f'ID{u.id}'}"
        user_buttons.append([InlineKeyboardButton(label, callback_data=f"admin_user_{u.id}")])

    nav_buttons = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    markup = InlineKeyboardMarkup(user_buttons + nav_buttons)
    text = "\n".join(lines) + ("\n\nНажми на пользователя для действий:" if lang == "ru" else "\n\nNospied uz lietotāju darbībām:")
    await query.edit_message_text(text[:4000], parse_mode="Markdown", reply_markup=markup)


async def _admin_event_start(query, context, lang):
    context.user_data["admin_event_data"] = {}
    context.user_data["admin_event_step"] = "title"
    await query.edit_message_text(
        "📅 *Создание события — Шаг 1/8*\n\nВведи *название* события (RU):" if lang == "ru"
        else "📅 *Pasākuma izveide — 1/8*\n\nIevadi pasākuma *nosaukumu* (LV):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена / Atcelt", callback_data="admin_events_create_cancel")]
        ]),
    )


async def handle_admin_event_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            return
        lang = user.language
        step = context.user_data.get("admin_event_step")
        if not step:
            return

        text = update.message.text.strip()
        data = context.user_data["admin_event_data"]

        if step == "title":
            data["title"] = text
            context.user_data["admin_event_step"] = "desc"
            await update.message.reply_text(
                "✅ Название: " + text + "\n\nШаг 2/8: Введи *описание* события (RU):" if lang == "ru"
                else "✅ Nosaukums: " + text + "\n\n2/8: Ievadi pasākuma *aprakstu* (LV):",
                parse_mode="Markdown",
            )
        elif step == "desc":
            data["description"] = text
            context.user_data["admin_event_step"] = "date"
            await update.message.reply_text(
                "✅ Описание сохранено.\n\nШаг 3/8: Введи *дату* (ДД.ММ.ГГГГ ЧЧ:ММ):" if lang == "ru"
                else "✅ Apraksts saglabāts.\n\n3/8: Ievadi *datumu* (DD.MM.GGGG ST:MM):",
                parse_mode="Markdown",
            )
        elif step == "date":
            from datetime import datetime as dt
            try:
                parsed = dt.strptime(text.strip(), "%d.%m.%Y %H:%M")
                data["date"] = parsed
                context.user_data["admin_event_step"] = "venue"
                await update.message.reply_text(
                    f"✅ Дата: {parsed.strftime('%d.%m.%Y %H:%M')}\n\nШаг 4/8: Введи *место проведения*:" if lang == "ru"
                    else f"✅ Datums: {parsed.strftime('%d.%m.%Y %H:%M')}\n\n4/8: Ievadi *norises vietu*:",
                    parse_mode="Markdown",
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат. Используй ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2026 20:00)" if lang == "ru"
                    else "❌ Nepareizs formāts. Izmanto DD.MM.GGGG ST:MM (piem., 25.12.2026 20:00)",
                )
        elif step == "venue":
            data["venue"] = text
            context.user_data["admin_event_step"] = "image_url"
            await update.message.reply_text(
                f"✅ Место: {text}\n\nШаг 5/8: Введи *ссылку на изображение* (или отправь «—» чтобы пропустить):" if lang == "ru"
                else f"✅ Vieta: {text}\n\n5/8: Ievadi *attēla saiti* (vai nosūti «—» lai izlaistu):",
                parse_mode="Markdown",
            )
        elif step == "image_url":
            data["image_url"] = text if text.strip() != "—" else ""
            context.user_data["admin_event_step"] = "price"
            await update.message.reply_text(
                f"✅ Изображение: {text if text.strip() != '—' else '—'}\n\nШаг 6/8: Введи *цену* билета в EUR (или 0 если бесплатно):" if lang == "ru"
                else f"✅ Attēls: {text if text.strip() != '—' else '—'}\n\n6/8: Ievadi *biļetes cenu* EUR (vai 0 ja bez maksas):",
                parse_mode="Markdown",
            )
        elif step == "price":
            try:
                price = float(text.replace(",", "."))
            except ValueError:
                await update.message.reply_text("❌ Введи число (например: 15.50)")
                return

            data["price"] = price
            context.user_data["admin_event_step"] = "ticket_url"
            await update.message.reply_text(
                f"✅ Цена: {price} EUR\n\nШаг 7/8: Введи *ссылку на покупку билета* (или «—» чтобы пропустить):" if lang == "ru"
                else f"✅ Cena: {price} EUR\n\n7/8: Ievadi *biļetes iegādes saiti* (vai «—» lai izlaistu):",
                parse_mode="Markdown",
            )
        elif step == "ticket_url":
            data["ticket_url"] = text if text.strip() != "—" else ""
            context.user_data["admin_event_step"] = "ticket_points"
            await update.message.reply_text(
                f"✅ Ссылка: {text if text.strip() != '—' else '—'}\n\nШаг 8/8: Введи *цену в бонусных баллах* (или 0 если не продаётся за баллы):" if lang == "ru"
                else f"✅ Saite: {text if text.strip() != '—' else '—'}\n\n8/8: Ievadi *cenu bonusos* (vai 0 ja nepārdod par punktiem):",
                parse_mode="Markdown",
            )
        elif step == "ticket_points":
            try:
                points = int(text.strip())
            except ValueError:
                await update.message.reply_text("❌ Введи целое число (например: 200)")
                return
            data["ticket_price_points"] = points
            await _admin_event_save(update, context, user, db, data, lang)
    finally:
        db.close()


async def _admin_event_save(update, context, admin_user, db, data, lang):
    from bot.models import Event, ModerationStatus

    event = Event(
        title=data.get("title", ""),
        description=data.get("description", ""),
        date=data.get("date", datetime.utcnow()),
        venue=data.get("venue", ""),
        image_url=data.get("image_url", ""),
        ticket_url=data.get("ticket_url", ""),
        ticket_price_points=data.get("ticket_price_points", 0),
        price=float(data.get("price", 0)),
        category="party",
        is_active=True,
        moderation_status=ModerationStatus.APPROVED.value,
        created_by=admin_user.telegram_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    _log_admin_action(db, admin_user, f"Создал событие: {event.title} (ID: {event.id})")
    context.user_data.pop("admin_event_data", None)
    context.user_data.pop("admin_event_step", None)

    await update.message.reply_text(
        f"✅ *Событие создано!*\n\n"
        f"Название: {event.title}\n"
        f"Дата: {event.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Место: {event.venue}\n"
        f"Цена: {event.price} EUR\n"
        f"🎫 Билет за бонусы: {event.ticket_price_points} pts\n"
        f"ID: #{event.id}" if lang == "ru"
        else f"✅ *Pasākums izveidots!*\n\n"
             f"Nosaukums: {event.title}\n"
             f"Datums: {event.date.strftime('%d.%m.%Y %H:%M')}\n"
             f"Vieta: {event.venue}\n"
             f"Cena: {event.price} EUR\n"
             f"🎫 Biļete par bonusiem: {event.ticket_price_points} pts\n"
             f"ID: #{event.id}",
        parse_mode="Markdown",
    )


async def _admin_events(query, db: Session, lang: str):
    from bot.models import Event
    events = db.query(Event).order_by(Event.date.desc()).limit(10).all()
    lines = ["📅 *События / Pasākumi:*\n"]
    kb = []
    if events:
        for e in events:
            title = e.title_lv if lang == "lv" and e.title_lv else e.title
            lines.append(f"• {title[:50]} — {e.date.strftime('%d.%m.%Y')}")
            kb.append([InlineKeyboardButton(f"✏️ {title[:45]}", callback_data=f"admin_event_edit_{e.id}")])
    else:
        lines.append("Нет событий / Nav pasākumu")
    lines.append("")
    kb.append([InlineKeyboardButton("➕ Создать событие / Izveidot", callback_data="admin_events_create")])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def _admin_specialists(query, db: Session, lang: str):
    from bot.models import Specialist
    from bot.keyboards.inline import admin_specialist_edit_keyboard
    specs = db.query(Specialist).order_by(Specialist.created_at.desc()).limit(10).all()
    if not specs:
        await query.edit_message_text(
            "Нет специалистов." if lang == "ru" else "Nav speciālistu.",
            reply_markup=admin_keyboard(),
        )
        return
    lines = ["🎭 *Специалисты / Speciālisti:*\n"]
    kb = []
    for s in specs:
        lines.append(f"• {s.name} — {s.category}")
        kb.append([InlineKeyboardButton(f"✏️ {s.name}", callback_data=f"admin_spec_edit_{s.id}")])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )


async def _admin_mixes(query, db: Session, lang: str):
    from bot.models import DjMix, ModerationStatus
    from bot.keyboards.inline import admin_keyboard as admin_kb
    # Show all mixes grouped by status
    all_mixes = db.query(DjMix).order_by(DjMix.created_at.desc()).limit(20).all()
    if not all_mixes:
        await query.edit_message_text(
            "Нет миксов." if lang == "ru" else "Nav miksu.",
            reply_markup=admin_kb(),
        )
        return

    buttons = []
    for m in all_mixes:
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(m.moderation_status, "❓")
        label = f"{status_icon} {m.title[:25]} — {m.artist_name[:15]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"admin_mix_edit_{m.id}")])

    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    await query.edit_message_text(
        "🎧 *Все миксы / Visi miksi*" if lang == "ru" else "🎧 *Visi miksi*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _admin_rewards(query, db: Session, lang: str):
    from bot.models import Reward
    rewards = db.query(Reward).all()
    lines = ["⭐ *Награды / Balvas:*\n"]
    for r in rewards:
        title = r.title_lv if lang == "lv" else r.title_ru
        lines.append(f"• {title} — {r.points_required} pts {'✅' if r.is_active else '❌'}")
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=admin_keyboard()
    )


async def _admin_rss(query, db: Session, lang: str):
    from bot.models import RssSource
    sources = db.query(RssSource).all()
    if not sources:
        await query.edit_message_text(
            "Нет RSS-источников. Добавь через /addrss {url}" if lang == "ru"
            else "Nav RSS avotu. Pievieno ar /addrss {url}",
            reply_markup=admin_keyboard(),
        )
        return
    lines = ["📰 *RSS Источники / Avoti:*\n"]
    for s in sources:
        status = "✅" if s.is_active else "❌"
        lines.append(f"{status} {s.title or s.url[:40]} — {s.category}")
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=admin_keyboard()
    )


async def _admin_bookings(query, db: Session, lang: str):
    from bot.services.booking_service import get_all_bookings
    bookings = get_all_bookings(db)
    if not bookings:
        await query.edit_message_text(
            "Нет заявок." if lang == "ru" else "Nav pieteikumu.",
            reply_markup=admin_keyboard(),
        )
        return
    lines = ["📋 *Заявки / Pieteikumi:*\n"]
    for b in bookings:
        status = {"pending": "⏳", "approved": "✅", "rejected": "❌", "cancelled": "🚫"}
        s = status.get(b.status, "❓")
        lines.append(f"{s} #{b.id} — {b.client_name} — {b.event_date.strftime('%d.%m.%Y')}")
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=admin_keyboard()
    )


async def _admin_analytics(query, db: Session, lang: str):
    stats = [
        f"👥 Всего пользователей: {get_total_users(db)}",
        f"✅ Активных (30 дн): {get_active_users(db)}",
        f"🔒 Заблокировано: {get_blocked_users(db)}",
        f"📈 Всего заработано points: {get_total_points_earned(db)}",
        f"📉 Всего потрачено points: {get_total_points_spent(db)}",
        f"👥 Рефералов: {get_total_referrals(db)}",
        f"📅 Предстоящих событий: {get_upcoming_events_count(db)}",
        f"📋 Всего заявок: {get_total_bookings(db)}",
        f"⏳ Ожидают: {get_pending_bookings(db)}",
    ]
    text = "📊 *Аналитика / Analytics*\n\n" + "\n".join(stats)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_keyboard())


async def _admin_log(query, db: Session, lang: str):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(15).all()
    if not logs:
        await query.edit_message_text(
            "Журнал пуст." if lang == "ru" else "Žurnāls ir tukšs.",
            reply_markup=admin_keyboard(),
        )
        return
    lines = ["📝 *Журнал действий / Darbību žurnāls:*\n"]
    for log in logs:
        lines.append(f"• [{log.created_at.strftime('%d.%m %H:%M')}] {log.action}")
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=admin_keyboard()
    )


async def _ask_points_amount(query, context, action_type: str, lang: str):
    context.user_data["admin_points_action"] = action_type
    await query.edit_message_text(
        "💰 Введи количество баллов:" if lang == "ru" else "💰 Ievadi punktu skaitu:",
    )


async def _confirm_action(query, context, action, target_id, lang):
    action_label = {
        "block": "заблокировать / bloķēt",
        "unblock": "разблокировать / atbloķēt",
    }
    label = action_label.get(action, action)
    await query.edit_message_text(
        f"❓ {'Подтверди' if lang == 'ru' else 'Apstiprini'} {label} пользователя #{target_id}?",
        reply_markup=confirm_keyboard(action, str(target_id)),
    )


def _log_admin_action(db: Session, admin: User, action: str, target_id: int = None):
    log = AuditLog(
        actor_id=admin.telegram_id,
        action=action,
        target_type="user" if target_id else None,
        target_id=target_id,
    )
    db.add(log)
    db.commit()


async def handle_admin_points_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for points amount."""
    action = context.user_data.get("admin_points_action")
    target_id_str = context.user_data.get("admin_action", (None, None))[1]
    if not action or not target_id_str:
        return
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
        context.user_data["admin_points_amount"] = amount
        context.user_data["admin_points_action"] = None

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
            lang = user.language if user else "ru"
            target_user = db.query(User).filter(User.id == target_id_str).first()
            target_name = target_user.first_name or target_user.username or f"#{target_id_str}"

            from bot.services.bonus_service import award_points, deduct_points
            if action == "add_points":
                award_points(db, target_user, amount,
                             f"Начислено администратором: {amount}",
                             f"Piešķirts administratoram: {amount}",
                             admin_id=user.telegram_id)
                _log_admin_action(db, user, f"Начислил {amount} points пользователю {target_name}",
                                  target_id=target_user.telegram_id)
                await update.message.reply_text(f"✅ +{amount} points пользователю {target_name}!")
            else:
                try:
                    deduct_points(db, target_user, amount,
                                  f"Списано администратором: {amount}",
                                  f"Norakstīts administratoram: {amount}",
                                  admin_id=user.telegram_id)
                    _log_admin_action(db, user, f"Списал {amount} points у пользователя {target_name}",
                                      target_id=target_user.telegram_id)
                    await update.message.reply_text(f"✅ -{amount} points у пользователя {target_name}!")
                except ValueError:
                    await update.message.reply_text("❌ Недостаточно баллов!")
        finally:
            db.close()
    except (ValueError, TypeError):
        await update.message.reply_text("❌ Введи целое положительное число.")


async def approve_mix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a DJ mix (/approvemix <id>)."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            await update.message.reply_text("🚫 Доступ запрещён.")
            return
        lang = user.language
        if not context.args:
            await update.message.reply_text("Используй: /approvemix <id>" if lang == "ru" else "Izmanto: /approvemix <id>")
            return
        from bot.models import DjMix, ModerationStatus
        mix_id = int(context.args[0])
        mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
        if not mix:
            await update.message.reply_text("❌ Микс не найден." if lang == "ru" else "❌ Mikss nav atrasts.")
            return
        mix.moderation_status = ModerationStatus.APPROVED.value
        mix.is_published = True
        mix.published_at = datetime.utcnow()
        _log_admin_action(db, user, f"Одобрил микс: {mix.title} (ID: {mix.id})")
        db.commit()
        await update.message.reply_text(
            f"✅ Микс «{mix.title}» одобрен и опубликован!" if lang == "ru"
            else f"✅ Mikss «{mix.title}» apstiprināts un publicēts!"
        )
    finally:
        db.close()


async def reject_mix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject a DJ mix (/rejectmix <id>)."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            await update.message.reply_text("🚫 Доступ запрещён.")
            return
        lang = user.language
        if not context.args:
            await update.message.reply_text("Используй: /rejectmix <id>" if lang == "ru" else "Izmanto: /rejectmix <id>")
            return
        from bot.models import DjMix, ModerationStatus
        mix_id = int(context.args[0])
        mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
        if not mix:
            await update.message.reply_text("❌ Микс не найден." if lang == "ru" else "❌ Mikss nav atrasts.")
            return
        mix.moderation_status = ModerationStatus.REJECTED.value
        _log_admin_action(db, user, f"Отклонил микс: {mix.title} (ID: {mix.id})")
        db.commit()
        await update.message.reply_text(
            f"❌ Микс «{mix.title}» отклонён." if lang == "ru" else
            f"❌ Mikss «{mix.title}» noraidīts."
        )
    finally:
        db.close()


async def handle_admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for admin editing (events and specialists)."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user or not admin_check(user):
            return
        lang = user.language
        text = update.message.text.strip()

        # Event editing
        edit_event = context.user_data.get("admin_edit_event")
        if edit_event:
            from bot.models import Event
            event_id = edit_event["id"]
            field = edit_event["field"]
            event = db.query(Event).filter(Event.id == event_id).first()
            if event:
                if field == "date":
                    from datetime import datetime as dt
                    try:
                        parsed = dt.strptime(text, "%d.%m.%Y %H:%M")
                        setattr(event, field, parsed)
                    except ValueError:
                        await update.message.reply_text(
                            "❌ Неверный формат. Используй ДД.ММ.ГГГГ ЧЧ:ММ" if lang == "ru"
                            else "❌ Nepareizs formāts. Izmanto DD.MM.GGGG ST:MM",
                        )
                        db.close()
                        return
                elif field == "price":
                    try:
                        setattr(event, field, float(text.replace(",", ".")))
                    except ValueError:
                        await update.message.reply_text("❌ Введи число")
                        db.close()
                        return
                elif field == "ticket_price_points":
                    try:
                        setattr(event, field, int(text))
                    except ValueError:
                        await update.message.reply_text("❌ Введи целое число")
                        db.close()
                        return
                else:
                    setattr(event, field, text)
                db.commit()
                context.user_data.pop("admin_edit_event", None)
                await update.message.reply_text(
                    f"✅ Поле «{field}» обновлено!" if lang == "ru"
                    else f"✅ Lauks «{field}» atjaunināts!",
                )
            db.close()
            return

        # Mix editing
        edit_mix = context.user_data.get("admin_edit_mix")
        if edit_mix:
            from bot.models import DjMix
            mix_id = edit_mix["id"]
            field = edit_mix["field"]
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                setattr(mix, field, text)
                db.commit()
                context.user_data.pop("admin_edit_mix", None)
                await update.message.reply_text(
                    f"✅ Поле «{field}» обновлено!" if lang == "ru"
                    else f"✅ Lauks «{field}» atjaunināts!",
                )
            db.close()
            return

        # Specialist editing
        edit_spec = context.user_data.get("admin_edit_spec")
        if edit_spec:
            from bot.models import Specialist
            spec_id = edit_spec["id"]
            field = edit_spec["field"]
            spec = db.query(Specialist).filter(Specialist.id == spec_id).first()
            if spec:
                if field == "price_from":
                    try:
                        setattr(spec, field, float(text.replace(",", ".")))
                    except ValueError:
                        await update.message.reply_text("❌ Введи число")
                        db.close()
                        return
                else:
                    setattr(spec, field, text)
                db.commit()
                context.user_data.pop("admin_edit_spec", None)
                await update.message.reply_text(
                    f"✅ Поле «{field}» обновлено!" if lang == "ru"
                    else f"✅ Lauks «{field}» atjaunināts!",
                )
    finally:
        db.close()


def register(application):
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("panel", admin_panel))
    application.add_handler(CommandHandler("approvemix", approve_mix))
    application.add_handler(CommandHandler("rejectmix", reject_mix))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^(admin_|set_role_|confirm_|cancel_)"))

    # Handle text messages for admin points input
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_admin_points_text,
        ),
        group=2,
    )

    # Handle text messages for admin event creation
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_admin_event_text,
        ),
        group=3,
    )

    # Handle text messages for admin editing (events and specialists)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_admin_edit_text,
        ),
        group=4,
    )
