"""DJ Mixes handlers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy.orm import Session
from datetime import datetime

from bot.database import SessionLocal
from bot.models import User, DjMix, MixListen
from bot.keyboards.inline import (
    dj_mixes_keyboard, mix_detail_keyboard, back_keyboard
)
from bot.config import POINTS
from bot.utils.helpers import has_permission


def _get_mixes(db, sort="new", limit=10):
    q = db.query(DjMix).filter(DjMix.is_published == True, DjMix.moderation_status == "approved")
    if sort == "popular":
        q = q.order_by(DjMix.plays_count.desc(), DjMix.published_at.desc())
    else:
        q = q.order_by(DjMix.published_at.desc())
    return q.limit(limit).all()


async def _send_mix_as_audio(update, context, mix, lang):
    """Send a single mix as an audio player message."""
    caption = (
        f"🎧 *{mix.title}*\n"
        f"DJ: {mix.artist_name}\n"
        f"🎵 {mix.genre or '—'}  👁️ {mix.plays_count}\n\n"
        f"{mix.description or ''}"
    )
    await context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=mix.audio_url,
        title=mix.title,
        performer=mix.artist_name,
        caption=caption,
        parse_mode="Markdown",
    )


async def mixes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language
        sort = context.user_data.get("mixes_sort", "new")
        mixes_list = _get_mixes(db, sort=sort)

        if not mixes_list:
            text = (
                "🎧 Пока нет опубликованных миксов.\n\n"
                "🎤 Ты DJ? Отправь /djregister чтобы зарегистрироваться,\n"
                "а затем /uploadmix чтобы загрузить свой микс!"
                if lang == "ru"
                else "🎧 Vēl nav publicētu miksu.\n\n"
                     "🎤 Esi DJ? Nosūti /djregister lai reģistrētos,\n"
                     "pēc tam /uploadmix lai augšupielādētu savu miksu!"
            )
            await update.message.reply_text(
                text,
                reply_markup=back_keyboard("menu_main"),
            )
            return

        is_dj = user and has_permission(user.role, "dj_performer")

        # Send sort/controls message
        await update.message.reply_text(
            "🎧 *DJ Миксы / Miksi*",
            parse_mode="Markdown",
            reply_markup=dj_mixes_keyboard([], lang, sort, show_sort_only=True),
        )

        # Send each mix as audio player (if has audio_url) or text link
        link_only_mixes = []
        for mix in mixes_list:
            if mix.audio_url:
                mix.plays_count += 1
                listen = MixListen(mix_id=mix.id, user_id=user.id)
                db.add(listen)
                await _send_mix_as_audio(update, context, mix, lang)
            else:
                link_only_mixes.append(mix)
        db.commit()

        # Show mixes without audio as text links
        if link_only_mixes:
            lines = [f"🎵 {'Миксы по ссылкам / Miksi ar saitēm':*}" if lang == "ru" else '🎵 Miksi ar saitēm:']
            for m in link_only_mixes:
                lines.append(f"• {m.title} — {m.artist_name}: {m.external_link or '—'}")
            await update.message.reply_text("\n".join(lines))

        # Upload hint for DJs
        if is_dj:
            await update.message.reply_text(
                "📤 /uploadmix — Загрузить свой микс / Augšupielādēt savu miksu"
                if lang == "ru"
                else "📤 /uploadmix — Augšupielādēt savu miksu",
                reply_markup=back_keyboard("menu_main"),
            )

    finally:
        db.close()


async def mixes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            return
        lang = user.language

        if data == "menu_mixes":
            await mixes(update, context)
        elif data == "mixes_sort_new":
            context.user_data["mixes_sort"] = "new"
            await mixes(update, context)
        elif data == "mixes_sort_popular":
            context.user_data["mixes_sort"] = "popular"
            await mixes(update, context)
        elif data == "mix_upload_manual":
            await query.edit_message_text(
                "📤 *Публикация микса (текст)*\n\n"
                "Отправь данные в формате:\n"
                "`Название | Жанр | Ссылка | Описание`\n\n"
                "Пример:\n"
                "`Summer Vibes | House | https://soundcloud.com/... | Мой летний микс`"
                if lang == "ru" else
                "📤 *Miksa publicēšana (teksts)*\n\n"
                "Nosūti datus formātā:\n"
                "`Nosaukums | Žanrs | Saite | Apraksts`\n\n"
                "Piemērs:\n"
                "`Summer Vibes | House | https://soundcloud.com/... | Mans vasaras mikss`",
                parse_mode="Markdown",
            )
        elif data.startswith("mix_"):
            parts = data.split("_")
            action = parts[1]
            mix_id = int(parts[2]) if len(parts) > 2 else None

            if action == "listen" and mix_id:
                mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
                if mix:
                    mix.plays_count += 1
                    listen = MixListen(mix_id=mix_id, user_id=user.id if user else None)
                    db.add(listen)
                    db.commit()

                    if mix.audio_url:
                        await context.bot.send_audio(
                            chat_id=update.effective_chat.id,
                            audio=mix.audio_url,
                            title=mix.title,
                            performer=mix.artist_name,
                            caption=mix.description or "",
                        )
                        await query.edit_message_text(
                            f"▶️ *{mix.title}*\n\n"
                            f"{'Аудио отправлено выше ↑' if lang == 'ru' else 'Audio nosūtīts augstāk ↑'}",
                            parse_mode="Markdown",
                            reply_markup=mix_detail_keyboard(mix_id, has_audio=True),
                        )
                    else:
                        link = mix.external_link or ""
                        await query.edit_message_text(
                            f"🎵 *{mix.title}*\n\n"
                            f"{'Ссылка для прослушивания:' if lang == 'ru' else 'Klausīšanās saite:'}\n"
                            f"{link}\n\n"
                            f"{'Если это ссылка на SoundCloud / Mixcloud, просто перейди по ней.' if lang == 'ru' else 'Ja tā ir SoundCloud / Mixcloud saite, vienkārši atver to.'}",
                            parse_mode="Markdown",
                            reply_markup=mix_detail_keyboard(mix_id),
                        )
            elif mix_id:
                mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
                if mix:
                    # Send audio player directly if available
                    if mix.audio_url:
                        mix.plays_count += 1
                        listen = MixListen(mix_id=mix_id, user_id=user.id if user else None)
                        db.add(listen)
                        db.commit()

                        caption = (
                            f"🎧 *{mix.title}*\n"
                            f"DJ: {mix.artist_name}\n"
                            f"🎵 {mix.genre or '—'}  👁️{mix.plays_count}\n\n"
                            f"{mix.description or ''}"
                        )
                        await context.bot.send_audio(
                            chat_id=update.effective_chat.id,
                            audio=mix.audio_url,
                            title=mix.title,
                            performer=mix.artist_name,
                            caption=caption,
                            parse_mode="Markdown",
                        )
                        # Replace list message with mini-player view
                        from bot.keyboards.inline import mix_detail_keyboard
                        await query.edit_message_text(
                            f"▶️ *{mix.title}*\n\n"
                            f"{'Аудио отправлено выше ↑' if lang == 'ru' else 'Audio nosūtīts augstāk ↑'}",
                            parse_mode="Markdown",
                            reply_markup=mix_detail_keyboard(mix_id, has_audio=True),
                        )
                    else:
                        desc = mix.description_lv if lang == "lv" and mix.description_lv else mix.description
                        text = (
                            f"🎧 *{mix.title}*\n\n"
                            f"DJ: {mix.artist_name or '—'}\n"
                            f"🎵 Жанр: {mix.genre or '—'}\n"
                            f"📅 {mix.published_at.strftime('%d.%m.%Y') if mix.published_at else '—'}\n"
                            f"👁️ Прослушиваний: {mix.plays_count}\n\n"
                            f"{desc or ''}"
                        )
                        has_audio = bool(mix.audio_url)
                        buttons = [mix_detail_keyboard(mix_id, has_audio=has_audio)]
                        if user and mix.user_id == user.id:
                            from bot.keyboards.inline import mix_owner_edit_keyboard
                            extra = mix_owner_edit_keyboard(mix_id).inline_keyboard
                            buttons[0].inline_keyboard.extend(extra)
                        await query.edit_message_text(
                            text, parse_mode="Markdown",
                            reply_markup=buttons[0] if buttons else None,
                        )
        elif data.startswith("mix_edit_"):
            parts = data.split("_", 3)
            mix_id = int(parts[2])
            field = parts[3]
            context.user_data["mix_edit_field"] = {"id": mix_id, "field": field}
            field_names = {
                "title": "название / nosaukums",
                "genre": "жанр / žanrs",
                "description": "описание / aprakstu",
            }
            label = field_names.get(field, field)
            await query.edit_message_text(
                f"✏️ Введи новое значение для *{label}*:" if lang == "ru"
                else f"✏️ Ievadi jauno vērtību *{label}*:",
                parse_mode="Markdown",
            )
        elif data.startswith("mix_delete_"):
            mix_id = int(data.split("_")[2])
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix and mix.user_id == user.id:
                db.delete(mix)
                db.commit()
                await query.edit_message_text(
                    "🗑 Микс удалён / Mikss dzēsts",
                    reply_markup=back_keyboard("menu_main"),
                )
    finally:
        db.close()


async def upload_mix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mix upload flow."""
    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language
        is_admin = user.role in ("admin", "super_admin", "moderator")
        is_dj = has_permission(user.role, "dj_performer")

        if not is_dj and not is_admin:
            await update.message.reply_text(
                "🚫 Только DJ и администраторы могут публиковать миксы."
            )
            return

        context.user_data["awaiting_mix_upload"] = True
        text = (
            "📤 *Публикация микса*\n\n"
            "1. Нажми на скрепку 📎 рядом с полем ввода\n"
            "2. Выбери *аудиофайл* (MP3)\n"
            "3. Добавь *описание* в подписи к файлу\n\n"
            "Или используй текст:\n"
            "`Название | Жанр | Ссылка | Описание`"
            if lang == "ru" else
            "📤 *Miksa publicēšana*\n\n"
            "1. Spied uz saspraudes 📎 blakus ievades laukam\n"
            "2. Izvēlies *audio failu* (MP3)\n"
            "3. Pievieno *aprakstu* faila pielikumā\n\n"
            "Vai izmanto tekstu:\n"
            "`Nosaukums | Žanrs | Saite | Apraksts`"
        )
        buttons = [[InlineKeyboardButton(
            "✏️ Ввести вручную / Ievadīt manuāli",
            callback_data="mix_upload_manual"
        )]]
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    finally:
        db.close()


async def handle_mix_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle mix edit text input
    edit_field = context.user_data.get("mix_edit_field")
    if edit_field:
        mix_id = edit_field["id"]
        field = edit_field["field"]
        text = update.message.text.strip()
        db = SessionLocal()
        try:
            mix = db.query(DjMix).filter(DjMix.id == mix_id).first()
            if mix:
                setattr(mix, field, text)
                db.commit()
                user_tg = update.effective_user
                user = db.query(User).filter(User.telegram_id == user_tg.id).first()
                lang = user.language if user else "ru"
                await update.message.reply_text(
                    f"✅ Поле «{field}» обновлено!" if lang == "ru"
                    else f"✅ Lauks «{field}» atjaunināts!",
                )
        finally:
            db.close()
        context.user_data.pop("mix_edit_field", None)
        return

    if not context.user_data.get("awaiting_mix_upload"):
        return

    user_tg = update.effective_user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            return
        lang = user.language

        title = ""
        genre = ""
        link = ""
        description = ""
        artist_name = user.first_name or user.username

        # Handle audio file upload
        if update.message.audio:
            audio = update.message.audio
            title = audio.title or audio.file_name or "Без названия / Bez nosaukuma"
            artist_name = audio.performer or artist_name
            genre = ""
            description = update.message.caption or ""
            file_id = audio.file_id
            link = file_id  # Store file_id for playback via Telegram
        else:
            # Handle text format: Title | Genre | Link | Description
            text = update.message.text.strip()
            parts = text.split("|", 3)
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ Неверный формат. Используй:\n"
                    "`Название | Жанр | Ссылка | Описание`\n"
                    "или отправь MP3 файл с описанием в подписи."
                )
                db.close()
                return
            title = parts[0].strip()
            genre = parts[1].strip() if len(parts) > 1 else ""
            link = parts[2].strip() if len(parts) > 2 else ""
            description = parts[3].strip() if len(parts) > 3 else ""

        context.user_data["awaiting_mix_upload"] = False

        mix = DjMix(
            user_id=user.id,
            title=title,
            artist_name=artist_name,
            genre=genre,
            description=description,
            external_link=link if not update.message.audio else "",
            audio_url=link if update.message.audio else "",
            moderation_status="pending",
        )
        db.add(mix)
        db.commit()

        # Award bonus points for mix upload
        from bot.services.bonus_service import award_points
        award_points(db, user, POINTS["DJ_UPLOAD_MIX"],
                     "Загрузка микса", "Miksa augšupielāde")

        await update.message.reply_text(
            f"✅ *{'Микс отправлен на модерацию!' if lang == 'ru' else 'Mikss nosūtīts moderācijai!'}*\n\n"
            f"{'Название' if lang == 'ru' else 'Nosaukums'}: {title}\n"
            f"{'Жанр' if lang == 'ru' else 'Žanrs'}: {genre or '—'}\n"
            f"{'DJ' if lang == 'ru' else 'DJ'}: {artist_name}\n\n"
            f"{'После проверки модератором микс будет опубликован.' if lang == 'ru' else 'Pēc moderatora pārbaudes mikss tiks publicēts.'}\n\n"
            f"💰 **+{POINTS['DJ_UPLOAD_MIX']} pts** {'за загрузку!' if lang == 'ru' else 'par augšupielādi!'}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu_main"),
        )
    finally:
        db.close()


async def handle_mix_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio file upload for mix."""
    if not context.user_data.get("awaiting_mix_upload"):
        return
    await handle_mix_upload(update, context)


def register(application):
    application.add_handler(CommandHandler("mixes", mixes))
    application.add_handler(CommandHandler("uploadmix", upload_mix))
    application.add_handler(CallbackQueryHandler(mixes_callback, pattern=r"^(menu_mixes|mixes_sort_|mix_upload_manual|mix_edit_|mix_)"))

    # Handle text messages for mix upload
    from telegram.ext import MessageHandler, filters
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_mix_upload,
        ),
        group=1,
    )

    # Handle audio files for mix upload
    application.add_handler(
        MessageHandler(
            filters.AUDIO,
            handle_mix_audio,
        ),
        group=1,
    )
