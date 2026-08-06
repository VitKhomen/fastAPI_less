import os
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserModel
from services.auth import AuthService
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTService:
    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: timedelta | None = None) -> str:
        """
        data — що кладемо в токен, наприклад {"sub": "user@mail.com"}
        exp — час коли токен перестане бути валідним
        jwt.encode — підписує і кодує в рядок
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def decode_token(token: str) -> dict | None:
        """
        jwt.decode — перевіряє підпис і повертає payload
        якщо токен змінений або прострочений — кидає InvalidTokenError
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except InvalidTokenError:
            return None

    @classmethod
    async def login(cls, session: AsyncSession, username: str, password: str) -> str | None:
        # шукаємо юзера по email (username в твоєму випадку = email)
        result = await session.execute(
            select(UserModel).where(UserModel.email == username)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None

        if not AuthService.verify_password(password, user.hashed_password or ""):
            return None

        # кладемо email в "sub" — стандартне поле JWT для ідентифікатора
        token = cls.create_access_token(data={"sub": user.email})
        return token

    @classmethod
    async def get_current_user(cls, session: AsyncSession, token: str) -> UserModel | None:
        payload = cls.decode_token(token)
        if payload is None:
            return None

        email = payload.get("sub")
        if email is None:
            return None

        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()
