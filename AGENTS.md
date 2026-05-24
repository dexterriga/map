# Party Map Daugavpils Bot — AGENTS.md

Это проект Telegram-бота для ночной жизни Даугавпилса. Пользователь — владелец бота @mapdaugavpilsbot.

## Быстрые ссылки
- Директория проекта: `C:\Users\DEXTER\Desktop\party_map_daugavpils_bot\`
- Точка входа: `bot/main.py`
- Конфиг: `bot/config.py`
- .env: `.env` (токен и OWNER_ID)

## Команды для запуска
```cmd
cd C:\Users\DEXTER\Desktop\party_map_daugavpils_bot
.\venv\Scripts\activate
python -m bot.main
```
Или просто `start_bot.bat`.

## Стек
Python + python-telegram-bot v20+ + SQLAlchemy + APScheduler + feedparser
База: SQLite (файл `data/party_map.db`), готов к PostgreSQL

## Архитектура
- `bot/handlers/` — обработчики команд (start, events, profile, bonuses, referrals, specialists, booking, dj_mixes, admin, rss)
- `bot/services/` — бизнес-логика
- `bot/keyboards/inline.py` — все клавиатуры
- `bot/models.py` — 19 SQLAlchemy моделей
- `texts/ru.py`, `texts/lv.py` — тексты по языкам

## Роли (RBAC)
User(0) → DJ/Performer(1) → Moderator(2) → Admin(3) → Super Admin(4)
Только Super Admin может назначать админов.

## Система баллов
- Регистрация: 50
- Посещение вечеринки: 30
- Покупка билета: 50
- Заказ в баре от 20 EUR: 20
- Реферал: 40
- День рождения ×2
Награды: 100 (free_entry) / 150 (cocktail_discount) / 250 (two_free_shots) / 400 (concert_ticket) / 600 (vip_bonus)

## Последние изменения (24.05.2026)
### Профиль
- Бонусные очки, дни в боте, дата регистрации
- **Список приглашённых друзей** — показывает usernames тех, кого пригласил
- Для админов — кнопка "⚙️ Админ-панель"

### Пригласи друга
- Кнопка "👥 Пригласи друга" внизу экрана
- При нажатии — ссылка для приглашения + кнопка "📤 Поделиться ссылкой"
- Через Telegram Share — друг открывает ссылку, бот даёт 40 pts за регистрацию

### Кнопки внизу (двуязычные)
- RU: Афиша, Бонусы, Специалисты, DJ Миксы, Профиль, **Пригласи друга**, **Стать DJ**, Помощь, смена языка
- LV: Afiša, Bonusi, Speciālisti, Miksi, Profils, **Uzaicini draugu**, **Kļūt par DJ**, Palīdzība, valodas maiņa
- Для админа: дополнительно "⚙️ Admin"

### Admin — пользователи
- Показывает всех пользователей (первые 20) с ролью, баллами, количеством рефералов
- Отображается общее количество пользователей
