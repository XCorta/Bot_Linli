# 🕵️ Detective Telegram Bot

Бот для интерактивных детективных расследований.

## 🚀 Запуск локально

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Создайте `.env` файл на основе `.env.example` и вставьте токен
4. Запустите: `python bot.py`

## 🌐 Деплой на Railway (бесплатно)

1. Зарегистрируйтесь на https://railway.app
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите этот репозиторий
4. В настройках проекта добавьте переменную окружения:
   - `TELEGRAM_BOT_TOKEN` = ваш токен от @BotFather
5. Railway автоматически запустит бота!

## 📱 Создание бота в Telegram

1. Напишите @BotFather
2. Отправьте /newbot
3. Придумайте имя и username
4. Скопируйте токен в `.env` файл