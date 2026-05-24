@echo off
chcp 65001 >nul
title Party Map Daugavpils Bot — @mapdaugavpilsbot

echo ============================================
echo  Party Map Daugavpils Bot
echo  Bot: @mapdaugavpilsbot
echo ============================================
echo.

:: Активация виртуального окружения
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Виртуальное окружение не найдено.
    echo Запусти сначала setup.bat
    pause
    exit /b 1
)

:: Проверка .env
findstr /B "BOT_TOKEN=your_bot_token_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Токен не настроен!
    echo Отредактируй файл .env и вставь токен от @BotFather
    pause
    exit /b 1
)

:: Запуск
echo Запуск бота...
echo Для остановки нажми Ctrl+C
echo.
python -m bot.main

pause
