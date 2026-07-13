import os
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature
from dotenv import load_dotenv

from database.models import UserModel


load_dotenv()
secret_key = os.getenv("SECRET_KEY", "default_secret_key")
serializer = URLSafeSerializer(secret_key, salt="auth_salt")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
        # itsdangerous підписує session_id і повертає "session_id.signature"
        return serializer.dumps(session_id)

    @classmethod
    def verify_token(cls, token: str) -> str | None:
        try:
            # перевіряє підпис і повертає оригінальний session_id
            session_id = serializer.loads(token)
            return session_id
        except BadSignature:
            return None

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
        session_id = serializer.loads(token)
        active_sessions[session_id] = user.id
        return token

    @classmethod
    async def get_current_user(cls, session: AsyncSession, token: str) -> UserModel | None:
        session_id = cls.verify_token(token)  # перевіряє підпис
        if session_id is None:
            return None

        user_id = active_sessions.get(session_id)
        if user_id is None:
            return None

        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none
