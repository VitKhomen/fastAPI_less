import os
import secrets
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
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # короткий
REFRESH_TOKEN_EXPIRE_DAYS = 7      # довгий

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

refresh_tokens: dict[str, str] = {}


class JWTService:
    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
        """
        data — що кладемо в токен, наприклад {"sub": "user@mail.com"}
        exp — час коли токен перестане бути валідним
        jwt.encode — підписує і кодує в рядок
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "type": token_type})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def create_access_token(cls, username: str) -> str:
        return cls.create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            token_type="access"
        )

    @classmethod
    def create_refresh_token(cls, username: str) -> str:
        return cls.create_token(
            data={"sub": username},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            token_type="refresh"
        )

    @classmethod
    def decode_token(cls, token: str) -> dict | None:
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

        access = cls.create_access_token(user.email)
        refresh = cls.create_refresh_token(user.email)

        # зберігаємо refresh на сервері
        refresh_tokens[user.email] = refresh

        return {"access_token": access, "refresh_token": refresh}

    @classmethod
    def refresh(cls, refresh_token: str) -> dict | None:
        """
        1. Декодуємо і перевіряємо підпис/термін
        2. Перевіряємо type == "refresh"
        3. Шукаємо в сховищі
        4. Видаляємо старий, створюємо нові
        """
        payload = cls.decode_token(refresh_token)

        if payload is None:
            return None  # прострочений або невалідний

        if payload.get("type") != "refresh":
            return None  # це не refresh токен

        username = payload.get("sub")
        if username is None:
            return None

        # перевіряємо що токен є в нашому сховищі
        stored_token = refresh_tokens.get(username)
        if stored_token is None:
            return None  # юзер розлогінився або токен не існує

        # secrets.compare_digest — захист від timing attack
        if not secrets.compare_digest(stored_token, refresh_token):
            return None  # токен підроблений

        # видаляємо старий — один refresh токен на юзера
        del refresh_tokens[username]

        # створюємо нові
        new_access = cls.create_access_token(username)
        new_refresh = cls.create_refresh_token(username)

        # зберігаємо новий refresh
        refresh_tokens[username] = new_refresh

        return {"access_token": new_access, "refresh_token": new_refresh}

    @classmethod
    async def get_current_user(cls, session: AsyncSession, token: str) -> UserModel | None:
        payload = cls.decode_token(token)
        if payload is None:
            return None

        if payload.get("type") != "access":
            return None

        email = payload.get("sub")
        if email is None:
            return None

        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def user_exists(cls, session: AsyncSession, username: str) -> bool:
        result = await session.execute(
            select(UserModel).where(UserModel.email == username)
        )
        return result.scalar_one_or_none() is not None

    @classmethod
    async def register(cls, session: AsyncSession, username: str, password: str) -> UserModel:
        hashed_password = cls.hash_password(password)
        new_user = UserModel(email=username, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
