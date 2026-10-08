import os
import sys
import uuid
import traceback
import secrets
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

from loguru import logger
from logger.setup import setup_logger
from logger.context import log_error
from middleware.request_id import RequestIDMiddleware
from exceptions.base import AppException
from api.routers import users, product, auth_jwt

os.makedirs("logs", exist_ok=True)
setup_logger()  # ← спочатку логер

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "admin")

security = HTTPBasic()

app = FastAPI(
    title="FastAPI lessons",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None if MODE == "PROD" else "/openapi.json",
)

# Middleware — порядок важливий: RequestID першим
app.add_middleware(RequestIDMiddleware)

app.include_router(users.router)
app.include_router(product.router)
app.include_router(auth_jwt.router)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Обробники помилок ─────────────────────────────────────────────

@app.exception_handler(AppException)
async def custom_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    await log_error(request, exc, status_code=exc.status_code, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": request_id},
        content={
            "request_id": request_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    await log_error(request, exc, status_code=exc.status_code, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": request_id},
        content={
            "request_id": request_id,
            "status_code": exc.status_code,
            "message": exc.detail,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    await log_error(request, exc, status_code=500, request_id=request_id)
    return JSONResponse(
        status_code=500,
        headers={"X-Request-ID": request_id},
        content={
            "request_id": request_id,
            "status_code": 500,
            "message": "Internal Server Error",
        }
    )


# ── Middleware для логування всіх запитів ─────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"→ [{request_id}] {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"← [{request_id}] {request.method} {request.url.path} | {response.status_code}")
    return response


# ── DEV/PROD docs ─────────────────────────────────────────────────

def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    username_ok = secrets.compare_digest(
        credentials.username.encode(), DOCS_USER.encode())
    password_ok = secrets.compare_digest(
        credentials.password.encode(), DOCS_PASSWORD.encode())
    if not username_ok or not password_ok:
        raise HTTPException(status_code=401, headers={
                            "WWW-Authenticate": "Basic"})


if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    async def get_docs(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Docs")

elif MODE == "PROD":
    @app.get("/docs", include_in_schema=False)
    async def docs_disabled():
        raise HTTPException(status_code=404)


# ── Тестові ендпоінти ─────────────────────────────────────────────

class SubmitBody(BaseModel):
    name: str
    data: dict


@app.get("/ok")
async def ok():
    return {"status": "ok"}


@app.get("/error")
async def error():
    raise AppException(detail="Демонстраційна помилка")


@app.get("/boom")
async def boom():
    import random
    choices = [
        lambda: 1 / 0,
        lambda: {}["missing"],
        lambda: int("not-an-int"),
        lambda: (_ for _ in ()).throw(RuntimeError("Випадкова помилка"))
    ]
    random.choice(choices)()


@app.get("/echo")
async def echo(request: Request, q: str = ""):
    # перевір що в логах Authorization замаскований
    return {
        "query": q,
        "user_agent": request.headers.get("user-agent"),
        "request_id": getattr(request.state, "request_id", None)
    }


@app.post("/submit")
async def submit(body: SubmitBody):
    if not body.name:
        raise AppException(detail="Name is required")
    return {"received": body.model_dump()}


@app.post("/upload")
async def upload(request: Request):
    # навмисна помилка щоб побачити що логуються тільки метадані файлів
    raise AppException(detail="Upload processing failed")


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
