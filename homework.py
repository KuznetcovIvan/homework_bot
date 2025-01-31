import logging
import os
import time
import sys

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import TokenError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    encoding='utf-8'
)


def check_tokens():
    """Проверяет доступность переменных окружения.
    В случае отсутствия - принудительно останавливает программу.
    """
    missing_tokens = [name for name, token in {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID}.items() if not token]
    if missing_tokens:
        message = 'Отсутствует обязательная переменная окружения: '
        f'{", ".join(missing_tokens)}. Программа принудительно остановлена.'
        logging.critical(message)
        raise TokenError(message)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение: "{message}"')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к API-сервиса.
    В случае успешного запроса должна вернуть ответ API, приведя его
    к типам данных Python.
    """
    try:
        response = requests.get(
            url='https://practicum.yandex.ru/api/user_api/homework_statuses/',
            headers={'Authorization': f'OAuth {PRACTICUM_TOKEN}'},
            params={'from_date': timestamp})
        if response.status_code != 200:
            message = f'Ошибка при вызове API. Код: {response.status_code}'
            logging.error(message)
            raise ConnectionError(message)
    except requests.RequestException as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        return {"homeworks": [], "current_date": timestamp}
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        message = 'Ответ API не является словарем'
        logging.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'В ответе API отсутствуе ключ "homeworks"'
        logging.error(message)
        raise KeyError(message)
    elif not isinstance(response['homeworks'], list):
        message = 'Значение "homeworks" не является списком'
        logging.error(message)
        raise TypeError(message)

    if 'current_date' not in response:
        message = 'В ответе API отсутствуе ключ "current_date"'
        logging.error(message)
        raise KeyError(message)
    elif not isinstance(response['current_date'], int):
        message = 'Значение "current_date" не является числом'
        logging.error(message)
        raise ValueError(message)
    return response


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ.
    """
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.exception('Отсутствует ключ "homework_name"')
    try:
        status = homework['status']
    except KeyError:
        logging.exception('Отсутствует ключ "status"')
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        logging.exception('API возвращает недокументированный статус '
                          'домашней работы либо статус отсутствует')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None

    while True:
        try:
            homeworks = check_response(get_api_answer(timestamp))['homeworks']
            message = (parse_status(homeworks[0]) if homeworks
                       else 'Домашку ещё не взяли в работу')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)

        if message == last_message:
            logging.debug('Сообщение не было отправлено (статус не изменился)')
        else:
            send_message(bot, message)
            last_message = message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
