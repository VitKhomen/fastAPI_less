import os
import sys
import traceback
import secrets
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from exceptions.base import AppException

from loguru import logger
import random

from api.routers import users, product, auth, auth_basic, auth_jwt


# читаємо змінні оточення
MODE = os.getenv("MODE", "DEV")          # DEV або PROD
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "admin")

security = HTTPBasic()

# ── Налаштування loguru ───────────────────────────────────────────

# Прибираємо стандартний sink (щоб не дублювати виводи)
os.makedirs("logs", exist_ok=True)

logger.remove()

# Sink 1 — термінал (stdout)
# serialize=False — читабельний текст для розробника
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    colorize=True
)

# Sink 2 — файл з JSON (для систем моніторингу типу Grafana, ELK)
# serialize=True — кожен лог це JSON рядок
# rotation — новий файл кожні 10MB
# retention — зберігати логи 7 днів
logger.add(
    "logs/app.log",
    level="INFO",
    serialize=True,       # ← JSON формат в файлі
    rotation="10 MB",     # ← новий файл коли досяг 10MB
    retention="7 days",   # ← видаляти файли старші 7 днів
    compression="zip"     # ← стискати старі файли
)


# ── Додаток ───────────────────────────────────────────────────────


def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Перевірка логін/пароль для доступу до документації"""
    username_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        DOCS_USER.encode("utf-8")
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        DOCS_PASSWORD.encode("utf-8")
    )

    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


# В PROD — вимикаємо все при ініціалізації
# В DEV — теж вимикаємо стандартні, але додамо свої захищені нижче
app = FastAPI(
    title="FastAPI lessons",
    version="1.0.0",
    docs_url=None,      # вимикаємо стандартний /docs
    redoc_url=None,     # вимикаємо /redoc завжди
    openapi_url=None if MODE == "PROD" else "/openapi.json",
    # в PROD схема взагалі не генерується
    # в DEV схема є але /docs захистимо самі
)

app.include_router(users.router)
app.include_router(product.router)
# app.include_router(auth.router)
# app.include_router(auth_basic.router)
app.include_router(auth_jwt.router)


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# Додаємо кастомні захищені маршрути тільки в DEV
if MODE == "DEV":

    @app.get("/docs", include_in_schema=False)
    async def get_docs(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        # include_in_schema=False — цей ендпоінт не з'явиться в самій документації
        # після перевірки авторизації — повертаємо HTML swagger UI
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="FastAPI lessons — Docs"
        )

elif MODE == "PROD":

    @app.get("/docs", include_in_schema=False)
    async def docs_disabled():
        raise HTTPException(status_code=404, detail="Not found")

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_disabled():
        raise HTTPException(status_code=404, detail="Not found")

    @app.get("/redoc", include_in_schema=False)
    async def redoc_disabled():
        raise HTTPException(status_code=404, detail="Not found")


# ── Глобальний обробник всіх виключень ───────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Перехоплює ВСІ виключення включно з необробленими.

    logger.bind() — додає контекст до лога, щоб кожен запис
    містив інформацію про запит який спричинив помилку.
    """
    # bind() прикріплює додаткові поля до логу
    bound_logger = logger.bind(
        method=request.method,      # GET, POST, etc.
        path=str(request.url.path),  # /error, /boom, etc.
    )

    if isinstance(exc, AppException):
        # Кастомна помилка — логуємо як WARNING (це очікувана ситуація)
        bound_logger.warning(
            f"CustomAppError: {exc.message} | status_code={exc.code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status_code": exc.status_code,
                "message": exc.message,
                "type": "custom_error"
            }
        )

    else:
        # Необроблена помилка — логуємо як ERROR з повним traceback
        # traceback.format_exc() — повний стек помилки як рядок
        bound_logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}\n"
            f"{traceback.format_exc()}"
        )
        # Повертаємо безпечне повідомлення — без деталей помилки
        # щоб не витікала внутрішня інформація клієнту
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "message": "Internal server error",
                "type": "server_error"
            }
        )


# ── Middleware для логування всіх запитів ─────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware виконується для КОЖНОГО запиту.
    call_next — викликає наступний обробник і повертає відповідь.
    """
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"← {request.method} {request.url.path} | status={response.status_code}")
    return response


# ── Ендпоінти ─────────────────────────────────────────────────────

@app.get("/ok")
async def ok():
    logger.debug("OK endpoint called")
    return {"status": "ok"}


@app.get("/error")
async def error():
    raise AppException("Демонстраційна помилка", code=418)


@app.get("/boom")
async def boom():
    def div_by_zero():
        return 1 / 0

    def key_err():
        return {}["missing"]

    def value_err():
        return int("not-an-int")

    def runtime_err():
        raise RuntimeError("Випадкова помилка")

    random.choice([div_by_zero, key_err, value_err, runtime_err])()
    return {"status": "unreachable"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
