from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import SessionDep
from services.users import UserRepository
from schemas.user import SUserAdd, SUser, SUserAdultCheck


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
async def add_user(user: SUserAdd, session: SessionDep) -> SUser:

    return await UserRepository.add_user(session, user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: SessionDep):
    success = await UserRepository.delete_user(session, user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )


@router.post("/user", status_code=204)
async def is_user_adult(user: SUser, session: SessionDep) -> SUserAdultCheck:
    # Implementation for checking if a user is an adult
    return await UserRepository.validate_user_adult(user)
