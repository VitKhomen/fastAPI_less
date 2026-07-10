import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from database.models import UserModel


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
    async def login(cls, session: AsyncSession, email: str, password: str) -> str | None:
        result = await session.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()

        if user is None or not cls.verify_password(password, user.hashed_password):
            return None

        token = str(uuid.uuid4())
        active_sessions[token] = user.id
        return token

    @classmethod
    async def get_current_user(cls, session: AsyncSession, token: str) -> UserModel | None:
        user_id = active_sessions.get(token)
        if user_id is None:
            return None

        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()
