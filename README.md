# 🎉 Party Map Daugavpils — Telegram Bot

**Telegram-бот для ночной жизни Даугавпилса / Telegram bots Daugavpils naktsdzīvei**

Бот объединяет афишу вечеринок, бонусную систему, каталог специалистов,
DJ-миксы, бронирование и админ-панель в одном месте.

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Структура проекта](#-структура-проекта)
- [Установка и запуск (Windows)](#-установка-и-запуск-windows)
- [Команды бота](#-команды-бота)
- [Ролевая модель](#-ролевая-модель)
- [Бонусная система](#-бонусная-система)
- [MVP Roadmap](#-mvp-roadmap)
- [Монетизация](#-монетизация)
- [API и внешние интеграции](#-api-и-внешние-интеграции)
- [Тексты для BotFather](#-тексты-для-botfather)

---

## 🚀 Возможности

### Для пользователей
- 📅 **Афиша событий** — вечеринки, концерты, фестивали, afterparty
- ⭐ **Бонусная система** — накопление и трата баллов
- 👥 **Реферальная программа** — приглашай друзей и получай бонусы
- 🎭 **Каталог специалистов** — DJ, фотографы, ведущие, декораторы
- 📝 **Бронирование** — заявки специалистам
- 🎧 **DJ Миксы** — прослушивание и публикация миксов

### Для администраторов
- 👥 Управление пользователями и ролями
- 📅 Управление событиями
- 🎭 Модерация специалистов
- 🎧 Модерация DJ-миксов
- ⭐ Управление наградами
- 📰 RSS-импорт новостей и афиш
- 📊 Аналитика и журнал действий

---

## 📁 Структура проекта

```
party_map_daugavpils_bot/
├── .env.example              # Пример конфигурации
├── requirements.txt          # Зависимости Python
├── README.md                 # Этот файл
│
├── bot/
│   ├── __init__.py
│   ├── main.py               # Точка входа
│   ├── config.py             # Конфигурация
│   ├── database.py           # Подключение к БД
│   ├── models.py             # Модели SQLAlchemy
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py          # /start, /menu, /help, /language
│   │   ├── events.py         # Афиша и события
│   │   ├── profile.py        # Профиль пользователя
│   │   ├── bonuses.py        # Бонусы и награды
│   │   ├── referrals.py      # Реферальная система
│   │   ├── specialists.py    # Каталог специалистов
│   │   ├── booking.py        # Заявки на бронирование (ConversationHandler)
│   │   ├── dj_mixes.py       # DJ-миксы
│   │   ├── admin.py          # Админ-панель
│   │   └── rss.py            # RSS-менеджмент
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bonus_service.py  # Логика баллов и наград
│   │   ├── referral_service.py
│   │   ├── event_service.py
│   │   ├── booking_service.py
│   │   ├── rss_service.py    # Парсинг RSS
│   │   └── analytics_service.py
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py         # Все Inline-клавиатуры
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── role_middleware.py # RBAC декораторы
│   │
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py        # Вспомогательные функции
│       └── validators.py     # Валидация форм
│
├── texts/
│   ├── ru.py                 # Русские тексты
│   └── lv.py                 # Латышские тексты
│
├── migrations/
│   └── init_db.py            # Инициализация БД + seed
│
└── data/                     # Локальные данные (SQLite, логи)
```

---

## ⚙️ Установка и запуск (Windows)

### Быстрый старт (рекомендуется)

Просто запусти `setup.bat` — скрипт сделает всё сам:

```cmd
C:\Users\DEXTER\Desktop\party_map_daugavpils_bot> setup.bat
```

После этого **обязательно отредактируй файл `.env`**:
1. **BOT_TOKEN** — токен от [@BotFather](https://t.me/BotFather) для бота `@mapdaugavpilsbot`
2. **OWNER_ID** — твой Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot))

Затем запусти бота:

```cmd
C:\Users\DEXTER\Desktop\party_map_daugavpils_bot> start_bot.bat
```

### Ручная установка

#### 1. Открой PowerShell в папке проекта
```powershell
cd C:\Users\DEXTER\Desktop\party_map_daugavpils_bot
```

#### 2. Создай виртуальное окружение
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

#### 3. Установи зависимости
```powershell
pip install -r requirements.txt
```

#### 4. Настрой .env (ОБЯЗАТЕЛЬНО)
```powershell
# Отредактируй .env в Блокноте:
notepad .env
```
Вставь:
- `BOT_TOKEN` — токен, полученный у [@BotFather](https://t.me/BotFather) для бота `@mapdaugavpilsbot`
- `OWNER_ID` — твой Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot))

#### 5. Инициализируй базу данных
```powershell
python migrations\init_db.py
```

#### 6. Запусти бота
```powershell
python -m bot.main
```

Бот запущен! Открой Telegram и пиши [@mapdaugavpilsbot](https://t.me/mapdaugavpilsbot).

### Docker (опционально)
```powershell
docker build -t party-map-bot .
docker run -d --env-file .env party-map-bot
```

---

## 🤖 Команды бота

| Команда | Русский | Latviešu |
|---------|---------|----------|
| `/start` | Запустить бота | Sākt botu |
| `/menu` | Главное меню | Galvenā izvēlne |
| `/events` | Афиша событий | Pasākumu afiša |
| `/profile` | Мой профиль | Mans profils |
| `/bonuses` | Бонусы и награды | Bonusi un balvas |
| `/referral` | Реферальная ссылка | Referāla saite |
| `/specialists` | Каталог специалистов | Speciālistu katalogs |
| `/mixes` | DJ Миксы | DJ Miksi |
| `/uploadmix` | Загрузить микс (DJ) | Augšupielādēt miks |
| `/bookings` | Мои заявки | Mani pieteikumi |
| `/language` | Сменить язык | Mainīt valodu |
| `/help` | Помощь | Palīdzība |

### Команды администратора
| Команда | Описание |
|---------|----------|
| `/admin` или `/panel` | Открыть админ-панель |
| `/addrss <url> [cat] [auto]` | Добавить RSS-источник |
| `/listrss` | Список RSS-источников |
| `/fetchrss` | Принудительный импорт RSS |
| `/removerss <id>` | Отключить RSS-источник |

---

## 👑 Ролевая модель

| Роль | Уровень | Права |
|------|---------|-------|
| **User** | 0 | Пользование ботом: афиша, бонусы, профиль |
| **DJ / Performer** | 1 | User + публикация своих миксов |
| **Moderator** | 2 | Модерация контента и заявок |
| **Admin** | 3 | Управление контентом, пользователями, бонусами |
| **Super Admin** | 4 | Полный доступ, назначение ролей |

**Важно:**
- Назначать администраторов может только Super Admin
- Публикация афиши и новостей — только Admin / Super Admin
- Super Admin задаётся через `OWNER_ID` в `.env`

---

## ⭐ Бонусная система

### Начисление баллов
| Действие | Баллы |
|----------|-------|
| Регистрация в боте | 50 |
| Посещение вечеринки | 30 |
| Покупка билета | 50 |
| Заказ от 20 EUR | 20 |
| Пригласил друга | 40 |
| День рождения (x2) | x2 |

### Обмен баллов
| Награда | Баллы |
|---------|-------|
| Бесплатный вход | 100 |
| Коктейль со скидкой | 150 |
| 2 Free Shots | 250 |
| Билет на концерт | 400 |
| VIP-бонус / депозит | 600 |

---

## 🗺 MVP Roadmap

### Этап 1 — Запуск (текущий)
- [x] Базовая архитектура бота
- [x] Регистрация и профиль
- [x] Афиша событий
- [x] Бонусная система
- [x] Главное меню (RU/LV)

### Этап 2 — Расширение
- [ ] Реферальная система (реализована логика)
- [ ] Каталог специалистов (реализован)
- [ ] Бронирование (реализовано)
- [ ] DJ-миксы (реализованы)
- [ ] RSS-импорт (реализован)
- [ ] Админ-панель (реализована)

### Этап 3 — Городской хаб
- [ ] Партнёрские заведения
- [ ] Продажа билетов
- [ ] Платные размещения
- [ ] Монетизация
- [ ] Масштабирование на весь Даугавпилс

---

## 💰 Монетизация

Архитектура поддерживает будущее добавление:
- Платное продвижение событий в афише
- Платное продвижение специалистов в каталоге
- VIP-размещение DJ
- Спонсорские публикации
- Комиссия с продажи билетов
- Премиум-аккаунты для артистов

---

## 🔌 API и внешние интеграции

Бот спроектирован для подключения:
- **POS-системы** — через CSV-импорт или API
- **Внешние кассы** — стандартный REST API
- **CRM-системы** — экспорт пользователей и заказов
- **Сайт / Instagram** — автоматическая публикация афиши
- **Google Calendar** — синхронизация событий

---

## 🌐 Тексты для BotFather

### Name
`Party Map Daugavpils`

### Short Description (max 120 chars)
```
🎉 Ночная жизнь Даугавпилса: афиша, бонусы, DJ, бронирование
🎉 Daugavpils naktsdzīve: afiša, bonusi, DJ, rezervācija
```

### About (max 512 chars)
```
🎉 Party Map Daugavpils — твой гид по ночной жизни города!

🍸 Вечеринки и концерты
⭐ Бонусы и скидки
🎭 Специалисты для мероприятий
🎧 DJ-миксы
👥 Реферальная программа

Работает на русском и латышском.
```

### Welcome Message (sent at /start)
```
🎉 Добро пожаловать в Party Map Daugavpils!

Твой главный гид по ночной жизни Даугавпилса!
- Вечеринки и концерты
- Бонусы и скидки
- Каталог специалистов
- DJ-миксы

Используй /menu для навигации.
```

### Commands for BotFather
```
start - Запустить бота / Sākt botu
menu - Главное меню / Galvenā izvēlne
events - Афиша событий / Pasākumu afiša
profile - Мой профиль / Mans profils
bonuses - Бонусы и награды / Bonusi un balvas
referral - Реферальная ссылка / Referāla saite
specialists - Специалисты / Speciālisti
mixes - DJ Миксы / Miksi
bookings - Мои заявки / Mani pieteikumi
language - Сменить язык / Mainīt valodu
help - Помощь / Palīdzība
admin - Админ-панель / Admin panelis
```

---

## 📝 Лицензия

MIT License — проект с открытым исходным кодом.

---

*Сделано с ❤️ для ночной жизни Даугавпилса*
