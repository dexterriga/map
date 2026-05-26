"""Inline and reply keyboards for the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_reply_keyboard(lang="ru", is_admin=False, is_bar_admin=False):
    if lang == "ru":
        buttons = [
            [KeyboardButton("📅 Афиша"), KeyboardButton("⭐ Бонусы")],
            [KeyboardButton("🎭 Специалисты"), KeyboardButton("🎧 DJ Миксы")],
            [KeyboardButton("👤 Профиль"), KeyboardButton("👥 Пригласи друга")],
            [KeyboardButton("🎤 Стать DJ"), KeyboardButton("📸 Сканировать QR")],
            [KeyboardButton("💕 Знакомства")],
            [KeyboardButton("📩 Администратору"), KeyboardButton("ℹ️ Помощь")],
            [KeyboardButton("🌐 LV / RU")],
        ]
    else:
        buttons = [
            [KeyboardButton("📅 Afiša"), KeyboardButton("⭐ Bonusi")],
            [KeyboardButton("🎭 Speciālisti"), KeyboardButton("🎧 Miksi")],
            [KeyboardButton("👤 Profils"), KeyboardButton("👥 Uzaicini draugu")],
            [KeyboardButton("🎤 Kļūt par DJ"), KeyboardButton("📸 Skenēt QR")],
            [KeyboardButton("💕 Iepazīšanās")],
            [KeyboardButton("📩 Administratoram"), KeyboardButton("ℹ️ Palīdzība")],
            [KeyboardButton("🌐 RU / LV")],
        ]
    if is_admin:
        buttons.append([KeyboardButton("⚙️ Admin")])
    elif is_bar_admin:
        buttons.append([KeyboardButton("🍸 Bar Admin")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, input_field_placeholder="Выбери / Izvēlies")


def main_menu_keyboard(lang="ru"):
    buttons = [
        [InlineKeyboardButton("📅 Афиша / Afiša", callback_data="menu_events")],
        [InlineKeyboardButton("⭐ Бонусы / Bonusi", callback_data="menu_bonuses")],
        [InlineKeyboardButton("🎭 Специалисты / Speciālisti", callback_data="menu_specialists")],
        [InlineKeyboardButton("🎧 DJ Миксы / Miksi", callback_data="menu_mixes")],
        [InlineKeyboardButton("👤 Профиль / Profils", callback_data="menu_profile")],
        [InlineKeyboardButton("👥 Пригласи друга / Uzaicini draugu", callback_data="menu_referrals")],
        [InlineKeyboardButton("ℹ️ Помощь / Palīdzība", callback_data="menu_help")],
    ]
    if lang == "ru":
        buttons.append([InlineKeyboardButton("🌐 Latviešu", callback_data="lang_lv")])
    else:
        buttons.append([InlineKeyboardButton("🌐 Русский", callback_data="lang_ru")])
    return InlineKeyboardMarkup(buttons)


def events_keyboard(events, page=0, lang="ru"):
    buttons = []
    for ev in events:
        title = ev.title_lv if lang == "lv" and ev.title_lv else ev.title
        date_str = ev.date.strftime("%d.%m %H:%M")
        label = f"{date_str} {title[:32]}"
        buttons.append([
            InlineKeyboardButton(f"{label}", callback_data=f"event_{ev.id}")
        ])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"events_page_{page-1}"))
    if len(events) >= 5:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"events_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def event_detail_keyboard(event_id, ticket_url=None, ticket_price_points=0, is_admin=False, is_featured=False):
    buttons = []
    row1 = []
    if ticket_url:
        row1.append(InlineKeyboardButton("🎫 Купить билет / Nopirkt biļeti", url=ticket_url))
    if ticket_price_points and ticket_price_points > 0:
        row1.append(InlineKeyboardButton(f"💰 Купи за {ticket_price_points} pts", callback_data=f"ticket_points_confirm_{event_id}"))
    if row1:
        buttons.append(row1)
    buttons.append([
        InlineKeyboardButton("🎁 Бонус / Bonuss", callback_data=f"event_bonus_{event_id}"),
        InlineKeyboardButton("💾 Сохранить / Saglabāt", callback_data=f"event_save_{event_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("📤 Поделиться / Dalīties", callback_data=f"event_share_{event_id}"),
    ])
    if is_admin:
        pin_label = "📌 Открепить" if is_featured else "📌 Закрепить"
        buttons.append([InlineKeyboardButton(pin_label, callback_data=f"event_toggle_featured_{event_id}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_events")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def profile_keyboard(lang="ru", is_admin=False, admin_mode=True, is_superadmin=False):
    buttons = [
        [InlineKeyboardButton("⭐ Мои награды", callback_data="profile_rewards")],
        [InlineKeyboardButton("💾 Сохранённые события", callback_data="profile_saved")],
        [InlineKeyboardButton("📋 Мои заявки", callback_data="profile_bookings")],
        [InlineKeyboardButton("👥 Пригласи друга", callback_data="menu_referrals")],
        [InlineKeyboardButton("🍸 Использовать бонусы в баре", callback_data="profile_use_bonus_bar")],
    ]
    if is_admin:
        if admin_mode:
            buttons.append([InlineKeyboardButton("🔴 Админ: ВКЛ — выкл", callback_data="profile_admin_toggle")])
            buttons.append([InlineKeyboardButton("━━━ 🔧 АДМИН ━━━", callback_data="admin_panel")])
            buttons.append([InlineKeyboardButton("📅 Создать событие", callback_data="admin_events_create")])
            buttons.append([InlineKeyboardButton("👥 Все пользователи", callback_data="admin_users")])
            buttons.append([InlineKeyboardButton("🎧 Модерация миксов", callback_data="admin_mixes")])
            buttons.append([InlineKeyboardButton("🍸 Начислить бонусы (бар)", callback_data="profile_bar_earn")])
            if is_superadmin:
                buttons.append([InlineKeyboardButton("💰 Начислить баллы пользователю", callback_data="admin_points_quick")])
                buttons.append([InlineKeyboardButton("📢 Сделать пост / Publicēt", callback_data="admin_broadcast")])
        else:
            buttons.append([InlineKeyboardButton("🟢 Админ: ВЫКЛ — вкл", callback_data="profile_admin_toggle")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def bonuses_keyboard(rewards, lang="ru"):
    buttons = []
    for r in rewards:
        title = r.title_lv if lang == "lv" else r.title_ru
        buttons.append([
            InlineKeyboardButton(
                f"{title} — {r.points_required} pts",
                callback_data=f"redeem_{r.id}"
            )
        ])
    buttons.append([InlineKeyboardButton("📊 История / Vēsture", callback_data="bonus_history")])
    buttons.append([InlineKeyboardButton("ℹ️ Как заработать / Kā nopelnīt", callback_data="bonus_howto")])
    buttons.append([InlineKeyboardButton("🍸 Использовать бонусы в баре", callback_data="profile_use_bonus_bar")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def specialists_keyboard(specialists, lang="ru"):
    buttons = []
    for s in specialists:
        name = s.stage_name or s.name
        buttons.append([
            InlineKeyboardButton(f"{name} — {s.category}", callback_data=f"spec_{s.id}")
        ])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def specialist_detail_keyboard(spec_id):
    buttons = [
        [
            InlineKeyboardButton("📅 Забронировать", callback_data=f"book_{spec_id}"),
            InlineKeyboardButton("📨 Заявка / Pieteikums", callback_data=f"request_{spec_id}"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_specialists")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def dj_mixes_keyboard(mixes, lang="ru", sort="new", show_sort_only=False):
    buttons = []
    # Sort tabs
    sort_row = []
    new_label = "🆕 Новые / Jaunie"
    pop_label = "🔥 Популярные / Populārie"
    if sort == "popular":
        sort_row.append(InlineKeyboardButton(new_label, callback_data="mixes_sort_new"))
        sort_row.append(InlineKeyboardButton(f"✅ {pop_label}", callback_data="mixes_sort_popular"))
    else:
        sort_row.append(InlineKeyboardButton(f"✅ {new_label}", callback_data="mixes_sort_new"))
        sort_row.append(InlineKeyboardButton(pop_label, callback_data="mixes_sort_popular"))
    buttons.append(sort_row)

    if not show_sort_only:
        for m in mixes:
            buttons.append([
                InlineKeyboardButton(f"{m.title[:30]} — {m.artist_name[:15]} 👁️{m.plays_count}", callback_data=f"mix_{m.id}")
            ])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def mix_detail_keyboard(mix_id, has_audio=False):
    buttons = []
    if has_audio:
        buttons.append([InlineKeyboardButton("▶️ Слушать / Klausīties", callback_data=f"mix_listen_{mix_id}")])
    else:
        buttons.append([InlineKeyboardButton("🎵 Ссылка / Saite", callback_data=f"mix_listen_{mix_id}")])
    buttons.append([
        InlineKeyboardButton("💾 Сохранить / Saglabāt", callback_data=f"mix_save_{mix_id}"),
        InlineKeyboardButton("📅 Забронировать DJ", callback_data=f"book_dj_{mix_id}"),
    ])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_mixes")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def specialist_categories_keyboard(lang="ru"):
    categories = [
        "DJ", "Ведущий / Vadītājs", "Фотограф / Fotogrāfs",
        "Видеограф / Videogrāfs", "Декоратор / Dekorators",
        "Организатор / Organizators", "Технический / Tehniskais"
    ]
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(cat, callback_data=f"spec_cat_{cat}")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def admin_keyboard():
    buttons = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📅 События", callback_data="admin_events")],
        [InlineKeyboardButton("🎭 Специалисты", callback_data="admin_specialists")],
        [InlineKeyboardButton("🎧 DJ Миксы", callback_data="admin_mixes")],
        [InlineKeyboardButton("📤 Загрузить микс / Augšupielādēt miksu", callback_data="admin_upload_mix")],
        [InlineKeyboardButton("⭐ Награды", callback_data="admin_rewards")],
        [InlineKeyboardButton("📰 RSS Источники", callback_data="admin_rss")],
        [InlineKeyboardButton("📋 Заявки", callback_data="admin_bookings")],
        [InlineKeyboardButton("📊 Аналитика", callback_data="admin_analytics")],
        [InlineKeyboardButton("📝 Журнал действий", callback_data="admin_log")],
        [InlineKeyboardButton("🍸 Начислить бонусы (бар)", callback_data="admin_bar_earn")],
        [InlineKeyboardButton("📢 Сделать пост / Publicēt", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_users_actions_keyboard(user_id):
    buttons = [
        [
            InlineKeyboardButton("➕ Начислить баллы", callback_data=f"admin_points_add_{user_id}"),
            InlineKeyboardButton("➖ Списать баллы", callback_data=f"admin_points_sub_{user_id}"),
        ],
        [
            InlineKeyboardButton("🔒 Блокировать", callback_data=f"admin_block_{user_id}"),
            InlineKeyboardButton("🔓 Разблокировать", callback_data=f"admin_unblock_{user_id}"),
        ],
        [
            InlineKeyboardButton("👑 Сменить роль", callback_data=f"admin_change_role_{user_id}"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_users")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def role_selection_keyboard(user_id):
    buttons = [
        [InlineKeyboardButton("User", callback_data=f"set_role_{user_id}_user")],
        [InlineKeyboardButton("DJ / Performer", callback_data=f"set_role_{user_id}_dj_performer")],
        [InlineKeyboardButton("Bar Admin", callback_data=f"set_role_{user_id}_bar_admin")],
        [InlineKeyboardButton("Moderator", callback_data=f"set_role_{user_id}_moderator")],
        [InlineKeyboardButton("Admin", callback_data=f"set_role_{user_id}_admin")],
        [InlineKeyboardButton("Super Admin", callback_data=f"set_role_{user_id}_super_admin")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_users")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(action, data):
    buttons = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{action}"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def language_keyboard():
    buttons = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇱🇻 Latviešu", callback_data="lang_lv")],
    ]
    return InlineKeyboardMarkup(buttons)


def back_keyboard(callback_data="menu_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад / Atpakaļ", callback_data=callback_data)]
    ])


def admin_event_edit_keyboard(event_id, is_featured=False):
    pin_label = "📌 Закреплено / Piesprausts" if is_featured else "📌 Закрепить / Piespraust"
    buttons = [
        [InlineKeyboardButton("✏️ Название / Nosaukums", callback_data=f"admin_event_setfield_{event_id}_title")],
        [InlineKeyboardButton("✏️ Описание / Apraksts", callback_data=f"admin_event_setfield_{event_id}_description")],
        [InlineKeyboardButton("✏️ Дата / Datums", callback_data=f"admin_event_setfield_{event_id}_date")],
        [InlineKeyboardButton("✏️ Место / Vieta", callback_data=f"admin_event_setfield_{event_id}_venue")],
        [InlineKeyboardButton("✏️ Адрес / Adrese", callback_data=f"admin_event_setfield_{event_id}_address")],
        [InlineKeyboardButton("✏️ Цена EUR / Cena EUR", callback_data=f"admin_event_setfield_{event_id}_price")],
        [InlineKeyboardButton("✏️ Цена в pts / Cena pts", callback_data=f"admin_event_setfield_{event_id}_ticket_price_points")],
        [InlineKeyboardButton("✏️ Ссылка на билет / Biļetes saite", callback_data=f"admin_event_setfield_{event_id}_ticket_url")],
        [InlineKeyboardButton("✏️ Изображение / Attēls", callback_data=f"admin_event_setfield_{event_id}_image_url")],
        [InlineKeyboardButton(pin_label, callback_data=f"admin_event_toggle_featured_{event_id}")],
        [InlineKeyboardButton("🗑 Удалить / Dzēst", callback_data=f"admin_event_delete_{event_id}")],
        [InlineKeyboardButton("📢 Поделиться / Dalīties", callback_data=f"admin_event_share_{event_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_events")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_specialist_edit_keyboard(spec_id):
    buttons = [
        [InlineKeyboardButton("✏️ Имя / Vārds", callback_data=f"admin_spec_setfield_{spec_id}_name")],
        [InlineKeyboardButton("✏️ Категория / Kategorija", callback_data=f"admin_spec_setfield_{spec_id}_category")],
        [InlineKeyboardButton("✏️ Описание / Apraksts", callback_data=f"admin_spec_setfield_{spec_id}_description")],
        [InlineKeyboardButton("✏️ Цена / Cena", callback_data=f"admin_spec_setfield_{spec_id}_price_from")],
        [InlineKeyboardButton("📸 Загрузить фото / Augšupielādēt foto", callback_data=f"admin_spec_setfield_{spec_id}_photo_url")],
        [InlineKeyboardButton("✏️ Instagram", callback_data=f"admin_spec_setfield_{spec_id}_instagram")],
        [InlineKeyboardButton("✏️ Сайт / Vietne", callback_data=f"admin_spec_setfield_{spec_id}_website")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_specialists")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_mix_edit_keyboard(mix_id):
    buttons = [
        [InlineKeyboardButton("✏️ Название / Nosaukums", callback_data=f"admin_mix_setfield_{mix_id}_title")],
        [InlineKeyboardButton("✏️ Жанр / Žanrs", callback_data=f"admin_mix_setfield_{mix_id}_genre")],
        [InlineKeyboardButton("✏️ DJ / Izpildītājs", callback_data=f"admin_mix_setfield_{mix_id}_artist_name")],
        [InlineKeyboardButton("✏️ Описание / Apraksts", callback_data=f"admin_mix_setfield_{mix_id}_description")],
        [InlineKeyboardButton("✅ Опубликовать / Publicēt", callback_data=f"admin_mix_publish_{mix_id}")],
        [InlineKeyboardButton("❌ Отклонить / Noraidīt", callback_data=f"admin_mix_reject_{mix_id}")],
        [InlineKeyboardButton("🗑 Удалить / Dzēst", callback_data=f"admin_mix_delete_{mix_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_mixes")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def mix_owner_edit_keyboard(mix_id):
    buttons = [
        [InlineKeyboardButton("✏️ Название / Nosaukums", callback_data=f"mix_edit_{mix_id}_title")],
        [InlineKeyboardButton("✏️ Жанр / Žanrs", callback_data=f"mix_edit_{mix_id}_genre")],
        [InlineKeyboardButton("✏️ Описание / Apraksts", callback_data=f"mix_edit_{mix_id}_description")],
        [InlineKeyboardButton("🗑 Удалить / Dzēst", callback_data=f"mix_delete_{mix_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"mix_{mix_id}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def share_keyboard(text):
    share_url = f"https://t.me/share/url?url={text}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Поделиться / Dalīties", url=share_url)],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_main")],
    ])


def bar_admin_keyboard(lang="ru"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Списать бонусы / Norakstīt bonusus", callback_data="bar_scan_deduct")],
        [InlineKeyboardButton("📤 Начислить бонусы / Pieskaitīt bonusus", callback_data="bar_earn")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")],
    ])


def bar_confirm_keyboard(code, action):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить / Apstiprināt", callback_data=f"bar_execute_{action}_{code}")],
        [InlineKeyboardButton("❌ Отмена / Atcelt", callback_data="menu_main")],
    ])
