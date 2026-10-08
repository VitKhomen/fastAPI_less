# logger/context.py
import time
import traceback
from fastapi import Request
from loguru import logger
from logger.setup import mask_headers, MAX_BODY_SIZE, SENSITIVE_HEADERS


async def extract_body(request: Request) -> str:
    """
    Безпечно читає тіло запиту.
    Для multipart — тільки метадані файлів.
    Для великих тіл — обрізає до MAX_BODY_SIZE.
    """
    content_type = request.headers.get("content-type", "")

    try:
        if "multipart/form-data" in content_type:
            # для файлів — тільки метадані, не вміст
            form = await request.form()
            files_meta = []
            for key, value in form.items():
                if hasattr(value, "filename"):  # це файл
                    files_meta.append({
                        "field": key,
                        "filename": value.filename,
                        "size": len(await value.read()),
                        "content_type": value.content_type
                    })
                else:
                    files_meta.append({"field": key, "value": str(value)})
            return f"[multipart] {files_meta}"

        body_bytes = await request.body()

        if len(body_bytes) > MAX_BODY_SIZE:
            # обрізаємо і позначаємо
            return body_bytes[:MAX_BODY_SIZE].decode("utf-8", errors="replace") + \
                f" ... [TRUNCATED: original size={len(body_bytes)} bytes]"

        return body_bytes.decode("utf-8", errors="replace")

    except Exception as e:
        return f"[error reading body: {e}]"


def mask_body(body: str) -> str:
    """Маскує чутливі поля в тілі (простий варіант)"""
    for field in ["password", "token", "secret"]:
        if field in body.lower():
            import re
            body = re.sub(
                rf'"{field}"\s*:\s*"[^"]*"',
                f'"{field}": "***MASKED***"',
                body,
                flags=re.IGNORECASE
            )
    return body


async def log_error(
    request: Request,
    exc: Exception,
    *,
    status_code: int,
    request_id: str
) -> None:
    """
    Головна функція логування — викликається з будь-якого обробника.
    Збирає весь контекст запиту і логує структуровано.
    """
    try:
        # збираємо контекст
        body = await extract_body(request)
        body = mask_body(body)

        context = {
            "event": "request_error",
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params),
            "headers": mask_headers(dict(request.headers)),
            # всі cookies маскуємо
            "cookies": {k: "***MASKED***" for k in request.cookies},
            "body": body,
            "content_type": request.headers.get("content-type", ""),
            "client_host": request.client.host if request.client else None,
            "client_port": request.client.port if request.client else None,
            "status_code": status_code,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }

        # logger.opt(exception=exc) — додає traceback автоматично
        logger.bind(**context).opt(exception=exc).error(
            f"{type(exc).__name__}: {exc}"
        )

    except Exception as log_exc:
        # фолбек — якщо логування само впало
        logger.error(
            f"LOGGING FAILED: {log_exc} | original: {type(exc).__name__}: {exc}")
