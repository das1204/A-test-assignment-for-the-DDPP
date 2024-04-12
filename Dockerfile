# Используем базовый образ Python
FROM python:3.9

# Устанавливаем переменную окружения для обеспечения вывода Python в буферизированный режим
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app/

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Определяем порт, который будет прослушивать наше приложение
EXPOSE 5000

# Запускаем сервер Flask
CMD ["python", "app.py"]
