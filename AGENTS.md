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
.\venv\Scripts\python.exe -m bot.main
```
**ВАЖНО**: Не используйте `start_bot.bat` — он создаёт несколько процессов через cmd, что вызывает 409 Conflict.
Фоновый запуск (PowerShell):
```powershell
Start-Process -WindowStyle Hidden -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m", "bot.main"
```

## Тестирование бота
Используйте агента `telegram-bot-tester`:
```powershell
task -prompt "Test all bot features and fixes" -subagent_type telegram-bot-tester
```
Тест-скрипт: `tests/test_bot_functionality.py`

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
- RU: Афиша, Бонусы, Специалисты, DJ Миксы, Профиль, **Пригласи друга**, **Знакомства**, **Стать DJ**, Помощь, смена языка
- LV: Afiša, Bonusi, Speciālisti, Miksi, Profils, **Uzaicini draugu**, **Iepazīšanās**, **Kļūt par DJ**, Palīdzība, valodas maiņa
- Для админа: дополнительно "⚙️ Admin"

### 💕 Знакомства (26.05.2026)
- Кнопка "💕 Знакомства / Iepazīšanās" в главном меню (между Сканировать QR и Администратору)
- В профиле знакомств: загрузка фото (file_id), редактирование bio
- Дата хранение: User.dating_photo, User.dating_bio (миграция через _migrate_db)
- Обработчик: `bot/handlers/dating.py`

### Админ — исправления (26.05.2026)
- **🗑 кнопка удаления**: добавлена в список мероприятий (`_admin_events`) — компактная кнопка рядом с каждым событием
- **🖼 фото мероприятия**: исправлено — сохраняется Telegram file_id вместо локального пути. При отображении:
  - `send_photo(photo=file_id)` — работает напрямую
  - В текстовом списке — показывает "🖼 Есть афиша" (без битой ссылки)
  - URL-ссылки (http/https) отображаются как `[Смотреть афишу](url)`
- **📢 Поделиться событием**: кнопка "📢 Поделиться / Dalīties" на странице редактирования события. Рассылает событие всем `is_blocked == False` пользователям на их языке

### Admin — пользователи
- Показывает всех пользователей (первые 20) с ролью, баллами, количеством рефералов
- Отображается общее количество пользователей

## Баг: 409 Conflict (исправлено 26.05.2026)
**Причина**: `venv\Scripts\python.exe` был Python Launcher (py.exe), который при запуске порождает дочерний процесс с реальным python.exe. Два процесса одновременно вызывают getUpdates → 409 Conflict.

**Решение**: Заменён `venv\Scripts\python.exe` на настоящий python.exe:
```
Copy-Item -Path "C:\Users\DEXTER\AppData\Local\Programs\Python\Python314\python.exe" -Destination "venv\Scripts\python.exe" -Force
```
Теперь запускается только один процесс Python, 409 Conflict не возникает.
