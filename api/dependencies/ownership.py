from fastapi import Depends, HTTPException, status
from database.models import UserModel
from dependencies.auth import get_current_user

# in-memory сховище ресурсів
resources: dict[str, dict] = {
    "alice": {"content": "Секретні дані Аліси", "is_public": False},
    "bob": {"content": "Публічні нотатки Боба", "is_public": True},
    "admin": {"content": "Адмінський ресурс", "is_public": False},
}


def check_ownership(allowed_roles: list[str], require_owner: bool = True):
    """
    Фабрика залежностей для перевірки власності ресурсу.

    Логіка:
    - admin → доступ завжди
    - власник → доступ завжди (якщо require_owner=True)
    - інші → тільки якщо is_public=True (тільки GET)
    """
    async def ownership_checker(
        username: str,  # з path параметра {username}
        current_user: UserModel = Depends(get_current_user)
    ) -> dict:
        resource = resources.get(username)

        # POST — створення нового ресурсу
        if resource is None and not require_owner:
            if current_user.role == "admin" or current_user.email == username:
                return {}  # дозволяємо створити
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create resource under your own username"
            )

        if resource is None:
            raise HTTPException(status_code=404, detail="Resource not found")

        # admin має доступ до всього
        if current_user.role == "admin":
            return resource

        # власник має доступ до свого ресурсу
        if current_user.email == username:
            return resource

        # інші — тільки до публічних і тільки якщо не потрібне власництво
        if not require_owner and resource.get("is_public"):
            return resource

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not owner or resource is private"
        )

    return ownership_checker
