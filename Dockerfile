# Dockerfile

# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями в контейнер
COPY requirements.txt .

# Устанавливаем зависимости. Этот слой будет кэшироваться.
RUN pip install --no-cache-dir -r requirements.txt

# УБИРАЕМ ШАГ 'COPY . .'

# Команда, которая будет выполняться при запуске контейнера
CMD ["python", "main.py"]