import os
import secrets
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from api.routers import users, product, auth, auth_basic, auth_jwt


# читаємо змінні оточення
MODE = os.getenv("MODE", "DEV")          # DEV або PROD
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "admin")

security = HTTPBasic()


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
