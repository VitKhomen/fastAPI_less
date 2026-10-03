
# exceptions/base.py
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ── Моделі відповідей на помилки ─────────────────────────────────

class ErrorResponse(BaseModel):
    """Єдиний формат помилок у всьому додатку"""
    error_code: str
    message: str
    detail: str | None = None


# ── Базовий клас ──────────────────────────────────────────────────

class AppException(Exception):
    """Базовий клас — всі кастомні помилки наслідують від нього"""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "Internal server error"

    def __init__(self, detail: str | None = None, code: int | None = None):
        self.detail = detail
        if code is not None:
            self.status_code = code
        super().__init__(self.message)


# ── Конкретні виключення ──────────────────────────────────────────

class UserNotFoundException(AppException):
    status_code = 404
    error_code = "USER_NOT_FOUND"
    message = "User not found"


class UserAlreadyExistsException(AppException):
    status_code = 409
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this email already exists"


class ProductNotFoundException(AppException):
    status_code = 404
    error_code = "PRODUCT_NOT_FOUND"
    message = "Product not found"


class InvalidCredentialsException(AppException):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"


class ForbiddenException(AppException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Access denied"


# ── Обробники ─────────────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Один обробник для всіх кастомних помилок"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail
        ).model_dump()
    )
