from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import SessionDep
from services.users import UserRepository
from schemas.user import SUserCreate, SUser, SUserAgeCheck, SUserAgeCheckResponse, SUserFeedback


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_users(
    session: SessionDep,
    limit: int = 10,
    offset: int = 0,
    keyword: str | None = None
):
    return await UserRepository.get_users(session, limit, offset, keyword)


@router.get("/{user_id}")
async def get_user(user_id: int, session: SessionDep):
    result = await UserRepository.get_user(session, user_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return result


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: SUserCreate, session: SessionDep) -> SUser:

    return await UserRepository.create_user(session, user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: SessionDep):
    success = await UserRepository.delete_user(session, user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )


@router.post("/user", status_code=200)
async def is_user_adult(user: SUserAgeCheck) -> SUserAgeCheckResponse:
    return SUserAgeCheckResponse(
        name=user.name,
        age=user.age,
        is_adult=user.age >= 18
    )


@router.post("/feedback", status_code=200)
async def add_user_feedback(
    feedback: SUserFeedback,
    session: SessionDep,
    is_premium: bool = False  # ← query param: /feedback?is_premium=true
):
    user = await UserRepository.get_user(session, feedback.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await UserRepository.add_user_feedback(session, feedback)

    msg = f"Спасибо, {user.name}! Ваш отзыв сохранён."
    if is_premium:
        msg += " Ваш отзыв будет рассмотрен в приоритетном порядке."
    return {"message": msg}
