from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserModel, UserFeedbackModel
from schemas.user import SUserCreate, SUser, SUserFeedback
from services.auth import AuthService


class UserRepository:

    @classmethod
    async def get_users(
        cls,
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        keyword: str | None = None
    ) -> list[SUser]:
        query = select(UserModel)

        if keyword:
            query = query.where(UserModel.name.ilike(f"%{keyword}%"))

        result = await session.execute(query.limit(limit).offset(offset))
        users = result.scalars().all()

        return [SUser.model_validate(user) for user in users]

    @classmethod
    async def get_user(cls, session: AsyncSession, user_id: int) -> SUser | None:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            return None

        return SUser.model_validate(user)

    @classmethod
    async def create_user(cls, session: AsyncSession, user: SUserCreate) -> SUser:
        new_user = UserModel(
            name=user.name,
            age=user.age,
            email=user.email,
            is_subscribed=user.is_subscribed,
            hashed_password=AuthService.hash_password(user.password)
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return SUser.model_validate(new_user)

    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: int) -> bool:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            return False

        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def add_user_feedback(cls, session: AsyncSession, feedback: SUserFeedback) -> SUserFeedback:
        new_feedback = UserFeedbackModel(
            user_id=feedback.user_id,
            feedback=feedback.feedback
        )

        session.add(new_feedback)
        await session.commit()
        await session.refresh(new_feedback)

        return SUserFeedback.model_validate(new_feedback)
