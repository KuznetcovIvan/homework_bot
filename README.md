# Homework Bot
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![pyTelegramBotAPI](https://img.shields.io/badge/pyTelegramBotAPI-v4.x-blue?logo=telegram)

Python-бот для Telegram, который проверяет статус домашних заданий через API образовательного сервиса и отправляет уведомления в Telegram-чат.

---

## Возможности
- Опрашивает [эндпоинт](https://practicum.yandex.ru/api/user_api/homework_statuses/) API Яндекс Практикума каждые 10 минут для проверки статуса домашних заданий.
- Отправляет уведомления в Telegram с вердиктами ревью.
- Логирует события (ошибки, успешные сообщения и т.д.) в stdout и файл логов.
- Обрабатывает ошибки API и Telegram.

---

### Установка и запуск проекта

1. Клонируйте проект с [репозитория](https://github.com/KuznetcovIvan/homework_bot):
   `git clone https://github.com/KuznetcovIvan/homework_bot.git`

2. Перейдите в директорию с проектом:
   `cd homework_bot`

3. Создайте виртуальное окружение в директории проекта:
   `python -m venv venv`,
   и активируйте его:
   `venv\Scripts\activate` (для Linux/macOS: `source venv/bin/activate`)

4. Установите зависимости:
   `pip install -r requirements.txt`

5. Создайте файл `.env` в корне проекта и задайте переменные окружения.
   
```
   PRACTICUM_TOKEN=токен_практикума
   TELEGRAM_TOKEN=токен_бота_telegram
   TELEGRAM_CHAT_ID=ваш_id_чата
```
6. Запустите бота `python homework.py`

---

## Логирование
Бот логирует события с указанием:
- **Даты и времени** события.
- **Уровня важности** (DEBUG, ERROR, CRITICAL).
- **Описания события**.

Логируемые события:
- Отсутствие обязательных переменных окружения (CRITICAL).
- Успешная отправка сообщений в Telegram (DEBUG).
- Ошибки отправки сообщений в Telegram (ERROR).
- Недоступность эндпоинта API или ошибки (ERROR).
- Отсутствие ожидаемых ключей в ответе API или неожиданный статус задания (ERROR).
- Отсутствие новых статусов заданий (DEBUG).

Логи выводятся в `sys.stdout` и сохраняются в `homework.py.log`.

---

## Технологический стек
- Python
- pyTelegramBotAPI
- requests
- python-dotenv

---

### Автор: [Иван Кузнецов](https://github.com/KuznetcovIvan)