from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from database.engine import SessionDep
from services.auyh_jwt import JWTService
from schemas.auth_jwt import SJWTLogin, SToken

router = APIRouter(prefix="/jwt", tags=["jwt-auth"])

# HTTPBearer читає заголовок: Authorization: Bearer <token>
bearer = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=SToken)
@limiter.limit("5/minute")
async def login(credentials: SJWTLogin, session: SessionDep):
    # спочатку перевіряємо чи існує юзер
    if not await JWTService.user_exists(session, credentials.username):
        raise HTTPException(status_code=404, detail="User not found")

    token = await JWTService.login(session, credentials.username, credentials.password)

    if token is None:
        raise HTTPException(status_code=401, detail="Authorization failed")

    return SToken(access_token=token)


@router.get("/protected_resource")
async def protected_resource(
    session: SessionDep,
    auth: HTTPAuthorizationCredentials = Depends(bearer)
    # auth.credentials — це сам токен рядок після "Bearer "
):
    user = await JWTService.get_current_user(session, auth.credentials)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": "Access granted",
        "user": user.email
    }


@router.post("/register", response_model=SToken)
@limiter.limit("1/minute")
async def register(credentials: SJWTLogin, session: SessionDep):
    if await JWTService.user_exists(session, credentials.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    user = await JWTService.register(session, credentials.username, credentials.password)
    token = JWTService.create_access_token(data={"sub": user.email})

    return {"message": "New user created"}
