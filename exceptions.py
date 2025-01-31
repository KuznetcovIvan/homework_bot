class TokenError(ValueError):
    """Исключение, вызываемое при отсутствии переменных окружения."""


class ConnectionError(Exception):
    """Исключение, вызываемое если статус-код ответа не 200."""
