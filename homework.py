import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import APIResponseError, APIStatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENVIRONMENT_VARIABLES = (
    'PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'
)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

CHECK_TOKENS_ERROR = ('Отсутствует обязательная переменная окружения: '
                      '{missing_tokens}. Программа принудительно остановлена.')

SEND_MESSAGE_TRUE = ('Бот отправил сообщение: "{message}"')
SEND_MESSAGE_FALSE = ('Сообщение "{message}" не отправлено: {error}')

GET_API_CONNECTION_ERROR = ('Ошибка при запросе к API: {error}, '
                            'Параметры запроса: '
                            'url = {url}, headers = {headers}, '
                            'params = {params}')
GET_API_HTTP_ERROR = (
    'Ошибка при вызове API. Код: {status_code} '
    'Параметры запроса: url = {url}, headers = {headers}, '
    'params = {params}'
)
GET_API_RESPONSE_ERROR = (
    'Ошибка при вызове API: {error_data}. '
    'Параметры запроса: url = {url}, headers = {headers}, params = {params}'
)

CHECK_RESPONSE_TYPE_ERROR_DICT = (
    'Ответ API не является словарем (Тип: {type})'
)
CHECK_RESPONSE_KEY_ERROR = ('В ответе API отсутствуе ключ "homeworks"')
CHECK_RESPONSETYPE_ERROR_LIST = (
    'Значение "homeworks" не является списком (Тип: {type})'
)

PARSE_STATUS_KEY_ERROR_HOMEWORK_NAME = ('Отсутствует ключ "homework_name"')
PARSE_STATUS_KEY_ERROR_STATUS = ('Отсутствует ключ "status"')
PARSE_STATUS_HOMEWORK_VERDICTS = ('API возвращает недокументированный статус '
                                  'домашней работы: {status}')
PARSE_STATUS_MESSAGE = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)

MAIN_HOMEWORK_VERDICTS = ('Домашку ещё не взяли в работу')
MAIN_ERROR = ('Сбой в работе программы: {error}')
MAIN_NOT_SEND = ('Сообщение не было отправлено (статус не изменился)')


def check_tokens():
    """Проверяет доступность переменных окружения.
    В случае отсутствия - принудительно останавливает программу.
    """
    missing_tokens = [name for name in ENVIRONMENT_VARIABLES
                      if not globals().get(name)]

    if missing_tokens:
        message = CHECK_TOKENS_ERROR.format(missing_tokens=missing_tokens)
        logging.critical(message)
        raise ValueError(message)


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(SEND_MESSAGE_TRUE.format(message=message))
        return True
    except Exception as error:
        logging.exception(
            SEND_MESSAGE_FALSE.format(message=message, error=error))
        return False


def get_api_answer(timestamp):
    """Делает запрос к API-сервиса.
    В случае успешного запроса должна вернуть ответ API, приведя его
    к типам данных Python.
    """
    requests_data = dict(url=ENDPOINT,
                         headers=HEADERS,
                         params={'from_date': timestamp})
    try:
        response = requests.get(**requests_data)
    except requests.RequestException as error:
        raise ConnectionError(
            GET_API_CONNECTION_ERROR.format(error=error, **requests_data))

    if response.status_code != HTTPStatus.OK:
        raise APIStatusError(GET_API_HTTP_ERROR.format(
            status_code=response.status_code, **requests_data))

    response = response.json()
    error_data = {
        key: response[key] for key in ('error', 'code')if key in response}
    if error_data:
        raise APIResponseError(
            GET_API_RESPONSE_ERROR.format(
                error_data=error_data,
                **requests_data
            )
        )
    return response


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            CHECK_RESPONSE_TYPE_ERROR_DICT.format(type=type(response)))
    if 'homeworks' not in response:
        raise KeyError(CHECK_RESPONSE_KEY_ERROR)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(CHECK_RESPONSETYPE_ERROR_LIST.format(
            type=type(homeworks)))
    return response


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ.
    """
    if 'homework_name' not in homework:
        raise KeyError(PARSE_STATUS_KEY_ERROR_HOMEWORK_NAME)
    if 'status' not in homework:
        raise KeyError(PARSE_STATUS_KEY_ERROR_STATUS)
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(PARSE_STATUS_HOMEWORK_VERDICTS.format(status=status))
    return PARSE_STATUS_MESSAGE.format(
        homework_name=homework['homework_name'],
        verdict=HOMEWORK_VERDICTS[status])


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)['homeworks']
            message = (parse_status(homeworks[0]) if homeworks
                       else MAIN_HOMEWORK_VERDICTS)
            is_homework_verdicts = True
        except Exception as error:
            message = MAIN_ERROR.format(error=error)
            logging.error(message)
            is_homework_verdicts = False
        if message == last_message:
            logging.debug(MAIN_NOT_SEND)
        else:
            if send_message(bot, message):
                last_message = message
                if message != MAIN_HOMEWORK_VERDICTS and is_homework_verdicts:
                    timestamp = response.get('current_date', timestamp)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s - %(levelname)s from %(funcName)s(%(lineno)d): '
                '%(message)s'),
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(f'{__file__}.log', encoding='utf-8')])
    main()
