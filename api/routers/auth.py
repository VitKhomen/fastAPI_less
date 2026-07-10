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
        httponly=True,   # недоступний з JS
        secure=False,    # True в продакшені (тільки HTTPS)
        samesite="lax"
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
