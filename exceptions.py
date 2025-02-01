class APIResponseError(Exception):
    """Ошибка, возникающая при недопустимом ответе от API."""


class APIStatusError(Exception):
    """Ошибка при получении некорректного ответа от API."""
