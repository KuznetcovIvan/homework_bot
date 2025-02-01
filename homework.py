import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from http import HTTPStatus
from telebot import TeleBot

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

STATUS_MESSAGE = (
    'Изменился статус проверки работы "{homework_name}". {verdict}')


def check_tokens():
    """Проверяет доступность переменных окружения.
    В случае отсутствия - принудительно останавливает программу.
    """
    missing_tokens = [name for name in ('PRACTICUM_TOKEN',
                                        'TELEGRAM_TOKEN',
                                        'TELEGRAM_CHAT_ID')
                      if not globals().get(name)]

    if missing_tokens:
        message = ('Отсутствует обязательная переменная окружения: '
                   f'{missing_tokens}. Программа принудительно остановлена.')
        logging.critical(message)
        raise ValueError(message)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение: "{message}"')
        return True
    except Exception as error:
        logging.exception(f'Сообщение "{message}" не отправлено: {error}')
        return False


def get_api_answer(timestamp):
    """Делает запрос к API-сервиса.
    В случае успешного запроса должна вернуть ответ API, приведя его
    к типам данных Python.
    """
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise ValueError(
                f'Ошибка при вызове API. Код: {response.status_code} '
                f'Параметры запроса: url = {ENDPOINT}, headers = {HEADERS}, '
                f'from_date = {timestamp}')
    except requests.RequestException as error:
        raise RuntimeError(f'Ошибка при запросе к API: {error}')
    response = response.json()
    if 'error' in response or 'code' in response:
        message = 'Отсутствует'
        raise ValueError(
            f'Ошибка при вызове API: {response.get("code", message)}. '
            f'Описание ошибки: {response.get("error", message)}. '
            f'Сообщение от API: {response.get("message", message)}.')
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Ответ API не является словарем (Тип: {type(response)})')

    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствуе ключ "homeworks"')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Значение "homeworks" не является списком '
                        f'(Тип: {type(response["homeworks"])})')
    return response


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ.
    """
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name"')

    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status"')

    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('API возвращает недокументированный статус '
                       'домашней работы либо статус отсутствует')

    return STATUS_MESSAGE.format(homework_name=homework['homework_name'],
                                 verdict=HOMEWORK_VERDICTS[homework['status']])


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s - %(levelname)s from %(funcName)s(%(lineno)d): '
                '%(message)s'),
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(f"{__file__}.log", encoding='utf-8')],
    )
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)['homeworks']
            message = (parse_status(homeworks[0]) if homeworks
                       else 'Домашку ещё не взяли в работу')
            timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)

        if message == last_message:
            logging.debug('Сообщение не было отправлено (статус не изменился)')
        else:
            result = send_message(bot, message)
            if result:
                last_message = message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
