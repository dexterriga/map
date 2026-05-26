"""Russian language texts for Party Map Daugavpils Bot."""

WELCOME = (
    "🎉 *Добро пожаловать в Party Map Daugavpils!* 🎉\n"
    "🎉 *Laipni lūdzam Party Map Daugavpils!* 🎉\n\n"
    "Твой главный гид по ночной жизни Даугавпилса! 🍸\n"
    "Tava galvenā naktsdzīves ceļvede Daugavpilī! 🍸\n\n"
    "📅 *Афиша / Afiša* — вечеринки, концерты / ballītes, koncerti\n"
    "⭐ *Бонусы / Bonusi* — копи баллы и получай награды / krāj punktus un saņem balvas\n"
    "🎭 *Специалисты / Speciālisti* — DJ, фотографы, ведущие / fotogrāfi, vadītāji\n"
    "🎧 *DJ Миксы / Miksi* — слушай и открывай новых артистов / klausies un atklāj jaunus māksliniekus\n"
    "👤 *Профиль / Profils* — твои баллы и достижения / tavi punkti un sasniegumi\n"
    "👥 *Пригласи друга / Uzaicini draugu* — приглашай друзей и получай бонусы / uzaicini draugus un saņem bonusus\n\n"
    "📋 *Команды / Komandas:*\n"
    "/menu — Главное меню / Galvenā izvēlne\n"
    "/events — Афиша / Afiša\n"
    "/bonuses — Мои бонусы / Mani bonusi\n"
    "/profile — Профиль / Profils\n"
    "/specialists — Специалисты / Speciālisti\n"
    "/mixes — DJ Миксы / Miksi\n"
    "/djregister — Стать DJ / Kļūt par DJ\n"
    "/help — Помощь / Palīdzība\n"
    "/language — Сменить язык / Mainīt valodu\n\n"
    "👇 *Кнопки внизу экрана / Pogas ekrāna apakšā*"
)

MENU_TITLE = "🎯 *Главное меню*"
PROFILE_TITLE = "👤 *Твой профиль*"
EVENTS_TITLE = "📅 *Афиша событий*"
BONUSES_TITLE = "⭐ *Бонусы и награды*"
SPECIALISTS_TITLE = "🎭 *Специалисты*"
DJ_MIXES_TITLE = "🎧 *DJ Миксы*"
BOOKINGS_TITLE = "📋 *Мои заявки*"
REFERRALS_TITLE = "👥 *Реферальная программа*"
ADMIN_TITLE = "⚙️ *Админ-панель*"

BACK = "◀️ Назад"
MAIN_MENU = "🏠 Главное меню"
CLOSE = "❌ Закрыть"
CONFIRM = "✅ Подтвердить"
CANCEL = "❌ Отмена"
SHARE = "📤 Поделиться"
SAVE = "💾 Сохранить"
BOOK = "📅 Забронировать"
LISTEN = "🎵 Слушать"
GET_BONUS = "🎁 Получить бонус"
GET_TICKET = "🎫 Получить билет"
SUBMIT = "📨 Отправить"

NO_EVENTS = "😕 Пока нет предстоящих событий."
NO_SPECIALISTS = "😕 В этой категории пока нет специалистов."
NO_DJ_MIXES = "😕 Пока нет опубликованных миксов."
NO_BOOKINGS = "📭 У тебя пока нет заявок."
NO_SAVED = "📭 У тебя пока нет сохранённых событий."
NO_NOTIFICATIONS = "🔔 Нет новых уведомлений."
NO_REFERRALS = "👥 У тебя пока нет приглашённых друзей."

POINTS_BALANCE = "💰 *Баланс:* {points} баллов"
POINTS_EARNED = "📈 *Всего заработано:* {points}"
POINTS_SPENT = "📉 *Всего потрачено:* {points}"

REGISTRATION_SUCCESS = (
    "✅ *Регистрация завершена!*\n\n"
    "🎁 Ты получил 50 баллов за регистрацию!\n"
    "💰 Твой баланс: 50 баллов\n\n"
    "Используй /menu для навигации."
)

PROFILE_INFO = (
    "👤 *Профиль*\n\n"
    "Имя: {name}\n"
    "Username: @{username}\n"
    "Город: {city}\n"
    "Роль: {role}\n"
    "Язык: {language}\n\n"
    "💰 Баланс: {points} баллов\n"
    "📈 Заработано: {earned}\n"
    "📉 Потрачено: {spent}\n"
    "👥 Рефералов: {referrals}\n"
    "📅 Зарегистрирован: {reg_date}"
)

REFERRAL_INFO = (
    "👥 *Реферальная программа*\n\n"
    "Приглашай друзей и получай бонусы!\n\n"
    "🎁 За каждого друга — 40 баллов\n"
    "🎁 За первый визит друга — ещё 30 баллов\n\n"
    "Твоя реферальная ссылка:\n"
    "`{link}`\n\n"
    "Приглашено друзей: {count}"
)

EVENT_DETAIL = (
    "📅 *{title}*\n\n"
    "📆 {date}\n"
    "🕒 {time}\n"
    "📍 {venue}\n"
    "🏷️ {price}\n\n"
    "{description}\n\n"
    "{bonus_info}"
)

SPECIALIST_DETAIL = (
    "🎭 *{name}*\n\n"
    "Категория: {category}\n"
    "📍 {city}\n"
    "⭐ Опыт: {experience} лет\n"
    "🔧 Специализация: {specialization}\n\n"
    "{description}\n\n"
    "💰 Цена от: {price} EUR\n"
    "📞 {contacts}"
)

DJ_MIX_DETAIL = (
    "🎧 *{title}*\n\n"
    "DJ: {artist}\n"
    "🎵 Жанр: {genre}\n"
    "📅 {date}\n"
    "👁️ Прослушиваний: {plays}\n\n"
    "{description}"
)

BOOKING_FORM = (
    "📝 *Заявка на бронирование*\n\n"
    "Заполни форму, и мы свяжемся с тобой:"
)

BOOKING_CONFIRMED = (
    "✅ *Заявка отправлена!*\n\n"
    "Номер заявки: #{id}\n"
    "Мы свяжемся с тобой в ближайшее время."
)

BONUS_REDEEMED = "✅ *Награда активирована!*"
POINTS_ADDED = "🎉 *+{amount} баллов*\n{reason}"
ADMIN_ACCESS_DENIED = "🚫 Доступ запрещён. Только для администраторов."
USER_BLOCKED = "🚫 Твой аккаунт заблокирован. Обратись к администратору."
UNKNOWN_COMMAND = "🤷 Неизвестная команда. Используй /menu"
LANGUAGE_CHANGED = "✅ Язык изменён на русский."
HELP_TEXT = (
    "ℹ️ *Помощь*\n\n"
    "/start — Перезапустить бота\n"
    "/menu — Главное меню\n"
    "/events — Афиша событий\n"
    "/profile — Мой профиль\n"
    "/bonuses — Бонусы\n"
    "/referral — Реферальная ссылка\n"
    "/specialists — Специалисты\n"
    "/mixes — DJ Миксы\n"
    "/bookings — Мои заявки\n"
    "/language — Сменить язык\n"
    "/about — О боте\n"
    "/help — Помощь"
)

DESCRIPTION = (
    "🤖 *Party Map Daugavpils*\n\n"
    "🎉 *О боте:*\n"
    "Party Map Daugavpils — это главный гид по ночной жизни Даугавпилса. "
    "Находи события, бронируй специалистов, слушай миксы местных DJ, "
    "копай бонусные баллы и обменивай их на награды!\n\n"
    "📅 *Афиша* — все предстоящие вечеринки и концерты\n"
    "🎭 *Специалисты* — DJ, фотографы, организаторы, ведущие\n"
    "🎧 *DJ Миксы* — треки и миксы местных исполнителей\n"
    "⭐ *Бонусы* — программа лояльности с наградами\n"
    "👥 *Пригласи друга* — получай бонусы за друзей\n"
    "🎤 *Стать DJ* — регистрация для артистов\n\n"
    "👑 *Для администраторов:*\n"
    "Создание мероприятий, модерация миксов, управление пользователями\n\n"
    "🔗 *Контакты:* @mapdaugavpilsbot"
)

# ---- Dating module texts ----
DATING_MENU = "💕 *Знакомства*"
DATING_CREATE = "📝 *Создание анкеты*"
DATING_EDIT = "✏️ *Редактировать анкету*"
DATING_MY_PROFILE = "📋 *Моя анкета*"
DATING_BROWSE = "👀 *Просмотр анкет*"
DATING_BUY = "⭐ *Купить просмотры*"
DATING_PURCHASES = "📦 *Мои покупки*"
DATING_RULES = (
    "📋 *Правила раздела Знакомства*\n\n"
    "1. Запрещены оскорбления и непристойное поведение\n"
    "2. Запрещена реклама и спам\n"
    "3. Фото должны быть реальными\n"
    "4. Нельзя выдавать себя за другого человека\n"
    "5. Администрация вправе заблокировать анкету без объяснения причин\n\n"
    "Нарушение правил ведёт к блокировке анкеты."
)
DATING_NO_PROFILE = "У тебя ещё нет анкеты. Создай её, чтобы начать знакомиться!"
DATING_PENDING = "⏳ Твоя анкета на модерации. Ожидай проверки администратором."
DATING_REJECTED = "❌ Твоя анкета отклонена. Свяжись с администратором для уточнения причин."
DATING_BLOCKED = "🚫 Твоя анкета заблокирована. Свяжись с администратором."
DATING_ACTIVE = "✅ Анкета активна"
DATING_VIEWS_LEFT = "📸 Осталось просмотров: {count}"
DATING_NO_VIEWS = "😕 У тебя нет активных просмотров. Купи пакет просмотров, чтобы увидеть анкеты!"
DATING_NO_CANDIDATES = "😕 Пока нет новых анкет. Загляни позже!"
DATING_ALL_VIEWED = "🎉 Ты просмотрел(а) все доступные анкеты! Купи ещё просмотров, чтобы продолжить!"
DATING_PHOTO_PROMPT = "📤 Отправь фото (до 3 штук). После отправки всех фото нажми /done."
DATING_RULES_ACCEPT = "Подтверждаешь согласие с правилами?"
DATING_SUPPORT = "📩 По всем вопросам обращайся к администратору через кнопку «📩 Администратору» в главном меню."
