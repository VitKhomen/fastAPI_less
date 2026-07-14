from fastapi import APIRouter, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import SessionDep
from services.auth import AuthService
from schemas.auth import SLoginRequest, SLoginResponse
from schemas.user import SUserCreate, SUser
from services.users import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(user_data: SUserCreate, session: SessionDep):
    return await UserRepository.create_user(session, user_data)


@router.post("/login", response_model=SLoginResponse)
async def login(credentials: SLoginRequest, response: Response, session: SessionDep):
    token = await AuthService.login(session, credentials.email, credentials.password)

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600  # ← 1 година
    )

    return {"message": "Login successful"}


@router.get("/user")
async def get_current_user(
    session: SessionDep,
    session_token: str | None = Cookie(default=None)
):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = await AuthService.get_current_user(session, session_token)

    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.get("/profile")
async def get_profile(
    response: Response,
    session: SessionDep,
    session_token: str | None = Cookie(default=None)
):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user, new_token = await AuthService.get_current_user(session, session_token)

    if user is None:
        if new_token == "expired":
            raise HTTPException(status_code=401, detail="Session expired")
        raise HTTPException(status_code=401, detail="Invalid session")

    # оновлюємо cookie якщо треба
    if new_token:
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=300
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }
