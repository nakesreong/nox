FROM python:3.11-slim

WORKDIR /app

# Копируем только те зависимости, что нужны боту
# Это ускорит сборку
COPY requirements.txt .
RUN pip install --no-cache-dir python-telegram-bot==22.2 httpx==0.28.1

# Копируем только папку с интерфейсами
COPY ./interfaces /app/interfaces

# Запускаем скрипт бота
CMD ["python", "interfaces/telegram_bot.py"]