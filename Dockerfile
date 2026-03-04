FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY bot.py .

# Папка для базы
RUN mkdir -p /app/data

# Переменная окружения для БД
ENV DB_PATH=/app/data/media.db

# Запуск
CMD ["python", "bot.py"]