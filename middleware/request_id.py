# middleware/request_id.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware що:
    1. Читає X-Request-ID з заголовку або генерує новий
    2. Додає його в request.state щоб обробники могли читати
    3. Додає в заголовок відповіді
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id  # зберігаємо в state

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id  # прокидуємо в відповідь
        return response
