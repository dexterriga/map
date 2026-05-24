# ============================================
# Party Map Daugavpils Bot — Setup Script
# Bot: @mapdaugavpilsbot
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Party Map Daugavpils Bot — Установка" -ForegroundColor Cyan
Write-Host " Bot: @mapdaugavpilsbot" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/5] Проверка Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version
    Write-Host "  $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python не найден! Установи Python 3.10+ с python.org" -ForegroundColor Red
    pause
    exit 1
}

# Step 2: Create virtual environment
Write-Host "[2/5] Создание виртуального окружения..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    if (-not $?) {
        Write-Host "  [ERROR] Не удалось создать виртуальное окружение" -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "  Виртуальное окружение создано" -ForegroundColor Green
} else {
    Write-Host "  Виртуальное окружение уже существует" -ForegroundColor Green
}

# Step 3: Install dependencies
Write-Host "[3/5] Установка зависимостей..." -ForegroundColor Yellow
& .\venv\Scripts\pip install -r requirements.txt
if (-not $?) {
    Write-Host "  [ERROR] Ошибка установки зависимостей" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  Зависимости установлены" -ForegroundColor Green

# Step 4: Check .env
Write-Host "[4/5] Проверка конфигурации..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  [WARN] Файл .env не найден. Копирую из .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ВАЖНО! Отредактируй файл .env:" -ForegroundColor White
Write-Host "  1. BOT_TOKEN — токен от @BotFather" -ForegroundColor White
Write-Host "  2. OWNER_ID — твой Telegram ID (узнать: @userinfobot)" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 5: Init DB
Write-Host "[5/5] Инициализация базы данных..." -ForegroundColor Yellow
& .\venv\Scripts\python migrations\init_db.py
if (-not $?) {
    Write-Host "  [ERROR] Ошибка инициализации БД" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Установка завершена!" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "  Для запуска бота:" -ForegroundColor White
Write-Host "  1. Отредактируй .env (BOT_TOKEN, OWNER_ID)" -ForegroundColor White
Write-Host "  2. Запусти start_bot.bat" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
pause
