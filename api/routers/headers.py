from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field, field_validator


router = APIRouter(prefix="/headers", tags=["headers"])
MINIMUM_APP_VERSION = "0.0.2"


def parse_version(version: str) -> tuple[int, int, int]:
    """Перетворює "1.2.3" → (1, 2, 3)"""
    return (*map(int, version.split(".")),)  # розпаковуємо список у кортеж


class CommonHeaders(BaseModel):
    user_agent: str | None = Field(default=None, alias="user-agent")
    accept_language: str | None = Field(default=None, alias="accept-language")
    x_current_version: str = Field(
        alias="x-current-version",
        pattern=r"^\d+\.\d+\.\d+$",  # показується в OpenAPI документації
        description="Версія додатку у форматі X.Y.Z",
        examples=["1.0.0", "0.2.1"]
    )

    model_config = {"populate_by_name": True}

    @field_validator("x_current_version")
    @classmethod
    def check_version(cls, v: str) -> str:
        # pattern вже перевірив формат, тут тільки порівнюємо
        current = parse_version(v)
        minimum = parse_version(MINIMUM_APP_VERSION)

        if current < minimum:
            raise ValueError("Требуется обновить приложение")
        return v


@router.get("/")
async def get_headers(
    user_agent: str | None = Header(default=None),
    accept_language: str | None = Header(default=None)
):
    if not user_agent or not accept_language:
        raise HTTPException(status_code=400, detail="Missing required headers")
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


@router.get("/info")
async def get_info(
    response_obj: Response,  # щоб встановити заголовок відповіді
    user_agent: str | None = Header(default=None),
    accept_language: str | None = Header(default=None),
    x_current_version: str = Header(pattern=r"^\d+\.\d+\.\d+$")
):
    # та ж валідація через модель
    headers = CommonHeaders(**{
        "user-agent": user_agent,
        "accept-language": accept_language,
        "x-current-version": x_current_version
    })

    # встановлюємо серверний час в заголовок відповіді
    server_time = datetime.now(timezone.utc).isoformat()
    response_obj.headers["X-Server-Time"] = server_time

    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language,
            "X-Current-Version": headers.x_current_version,
        }
    }
