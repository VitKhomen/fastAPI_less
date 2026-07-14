import os
import time
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature

from database.models import UserModel


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
serializer = URLSafeSerializer(SECRET_KEY)

SESSION_LIFETIME = 300      # 5 хвилин
SESSION_REFRESH_AFTER = 180  # 3 хвилини

active_sessions: dict[str, int] = {}


class AuthService:

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    def create_token(cls, user_id: int) -> str:
        session_id = str(uuid.uuid4())  # унікальний UUID
        timestamp = int(time.time())
        # підписуємо обидва значення разом
        payload = f"{session_id}.{timestamp}"
        signature = serializer.dumps(payload)
        return f"{session_id}.{timestamp}.{signature}"

    @classmethod
    def verify_token(cls, token: str) -> str | None:
        """
        Повертає (session_id, timestamp) або None якщо підпис невалідний.
        """
        try:
            parts = token.split(".", 2)
            if len(parts) != 3:
                return None

            session_id, timestamp_str, signature = parts
            # перевіряємо підпис
            expected_payload = serializer.loads(signature)
            actual_payload = f"{session_id}.{timestamp_str}"

            if expected_payload != actual_payload:
                return None  # дані підроблені

            return session_id, int(timestamp_str)

        except (BadSignature, ValueError):
            return None

    @classmethod
    def check_session_status(cls, timestamp: int) -> str:
        """
        Повертає: 'active' | 'refresh' | 'expired'
        """
        elapsed = int(time.time()) - timestamp

        if elapsed >= SESSION_LIFETIME:
            return "expired"
        elif elapsed >= SESSION_REFRESH_AFTER:
            return "refresh"
        else:
            return "active"

    @classmethod
    def refresh_token(cls, session_id: str) -> str:
        """Створює новий токен з тим самим session_id але новим timestamp."""
        timestamp = int(time.time())
        payload = f"{session_id}.{timestamp}"
        signature = serializer.dumps(payload)
        return f"{session_id}.{timestamp}.{signature}"

    @classmethod
    async def login(cls, session: AsyncSession, email: str, password: str) -> str | None:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None or not cls.verify_password(password, user.hashed_password):
            return None

        token = cls.create_token(user.id)
        # зберігаємо session_id -> user_id
        session_id = token.split(".")[0]
        active_sessions[session_id] = user.id
        return token

    @classmethod
    async def get_current_user(
        cls,
        session: AsyncSession,
        token: str
    ) -> tuple[UserModel, str] | None:
        """
        Повертає (user, new_token_or_none).
        new_token — якщо треба оновити cookie, інакше None.
        """
        verified = cls.verify_token(token)
        if verified is None:
            return None, "invalid"

        session_id, timestamp = verified
        status = cls.check_session_status(timestamp)

        if status == "expired":
            active_sessions.pop(session_id, None)
            return None, "expired"

        user_id = active_sessions.get(session_id)
        if user_id is None:
            return None, "invalid"

        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None, "invalid"

        # якщо треба оновити — генеруємо новий токен
        new_token = cls.refresh_token(
            session_id) if status == "refresh" else None
        if new_token:
            # оновлюємо session_id якщо він змінився (в нашому випадку не змінюється)
            active_sessions[session_id] = user_id

        return user, new_token
