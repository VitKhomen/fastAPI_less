from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import SessionDep
from services.auth_jwt import JWTService
from database.models import UserModel

bearer = HTTPBearer()

ROLE_RATE_LIMITS = {
    "admin": "1000/minute",
    "user": "20/minute",
    "guest": "5/minute",
}


async def get_current_user(
    session: SessionDep,
    auth: HTTPAuthorizationCredentials = Depends(bearer)
) -> UserModel:
    """Базова залежність — просто перевіряє токен"""
    user = await JWTService.get_current_user(session, auth.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def get_rate_limit_by_role(
    current_user: UserModel = Depends(get_current_user)
) -> str:
    """
    Повертає рядок ліміту залежно від ролі.
    slowapi викличе цю функцію і використає результат як ліміт.
    """
    return ROLE_RATE_LIMITS.get(current_user.role, "5/minute")


def require_role(*roles: str):
    """
    Фабрика залежностей — повертає функцію яка перевіряє роль.
    Використання: Depends(require_role("admin", "user"))
    """
    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}"
            )
        return current_user
    return role_checker
