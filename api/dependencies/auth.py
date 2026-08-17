from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import SessionDep
from services.auth_jwt import JWTService
from database.models import UserModel

bearer = HTTPBearer()


async def get_current_user(
    session: SessionDep,
    auth: HTTPAuthorizationCredentials = Depends(bearer)
) -> UserModel:
    """Базова залежність — просто перевіряє токен"""
    user = await JWTService.get_current_user(session, auth.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


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
