import os
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature

from database.models import UserModel


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
serializer = URLSafeSerializer(SECRET_KEY)

active_sessions: dict[str, int] = {}


class AuthService:

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    async def get_user_by_credentials(
            cls, credentials,
            session: AsyncSession,
            username: str,
            password: str) -> UserModel | None:
        """
        Повертає користувача з БД, якщо username і password правильні
        """
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        if user and cls.verify_password(password, user.hashed_password):
            return user
        return None

    @classmethod
    async def register_user(cls, session: AsyncSession, username: str, password: str) -> UserModel:
        hashed_password = cls.hash_password(password)
        new_user = UserModel(
            username=username, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @classmethod
    async def login_user(cls, session: AsyncSession, username: str, password: str) -> UserModel | None:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        if user and cls.verify_password(password, user.hashed_password):
            return user
        return None
