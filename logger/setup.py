# logger/setup.py
import os
import sys
from loguru import logger

SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie",
    "x-api-key", "password", "token"
}

MAX_BODY_SIZE = 2048  # байт


def mask_headers(headers: dict) -> dict:
    """Маскує чутливі заголовки"""
    return {
        k: "***MASKED***" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }


def setup_logger():
    logger.remove()

    # Sink 1 — stdout (читабельний)
    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True
    )

    # Sink 2 — файл JSON
    logger.add(
        "logs/app.log",
        level="INFO",
        serialize=True,
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
