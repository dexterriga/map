@echo off
chcp 65001 >nul
title Party Map Daugavpils Bot — Setup

echo ============================================
echo  Party Map Daugavpils Bot — Установка
echo  Bot: @mapdaugavpilsbot
echo ============================================
echo.

:: Проверка Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден! Установи Python 3.10+ с python.org
    pause
    exit /b 1
)

echo [1/5] Python найден: 
python --version

:: Создание виртуального окружения
echo.
echo [2/5] Создание виртуального окружения...
if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo Виртуальное окружение создано
) else (
    echo Виртуальное окружение уже существует
)

:: Активация и установка зависимостей
echo.
echo [3/5] Установка зависимостей...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка установки зависимостей
    pause
    exit /b 1
)
echo Зависимости установлены

:: Проверка .env
echo.
echo [4/5] Проверка конфигурации...
if not exist .env (
    echo [WARN] Файл .env не найден. Копирую из .env.example...
    copy .env.example .env
)
echo.
echo ============================================
echo  ВАЖНО! Отредактируй файл .env:
echo  1. BOT_TOKEN — токен от @BotFather
echo  2. OWNER_ID — твой Telegram ID
echo ============================================
echo.

:: Инициализация БД
echo [5/5] Инициализация базы данных...
python migrations\init_db.py
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка инициализации БД
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Установка завершена!
echo.
echo  Для запуска бота:
echo  1. Отредактируй .env (BOT_TOKEN, OWNER_ID)
echo  2. Запусти start_bot.bat
echo ============================================
echo.

pause
