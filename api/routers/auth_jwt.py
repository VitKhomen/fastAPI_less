from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from database.engine import SessionDep
from services.auyh_jwt import JWTService
from schemas.auth_jwt import SJWTLogin, SToken, SRefreshRequest

router = APIRouter(prefix="/jwt", tags=["jwt-auth"])

# HTTPBearer читає заголовок: Authorization: Bearer <token>
bearer = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", status_code=201)
@limiter.limit("1/minute")
async def register(request: Request, credentials: SJWTLogin, session: SessionDep):
    if await JWTService.user_exists(session, credentials.username):
        raise HTTPException(status_code=409, detail="User already exists")
    await JWTService.register(session, credentials.username, credentials.password)
    return {"message": "New user created"}


@router.post("/login", response_model=SToken)
@limiter.limit("5/minute")
async def login(request: Request, credentials: SJWTLogin, session: SessionDep):
    if not await JWTService.user_exists(session, credentials.username):
        raise HTTPException(status_code=404, detail="User not found")

    tokens = await JWTService.login(session, credentials.username, credentials.password)

    if tokens is None:
        raise HTTPException(status_code=401, detail="Authorization failed")

    return SToken(**tokens)


@router.post("/refresh", response_model=SToken)
@limiter.limit("5/minute")
async def refresh(request: Request, body: SRefreshRequest):
    tokens = JWTService.refresh(body.refresh_token)

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token. Please login again."
        )

    return SToken(**tokens)


@router.get("/protected_resource")
async def protected_resource(
    session: SessionDep,
    auth: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = await JWTService.get_current_user(session, auth.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token"
        )

    return {"message": "Access granted", "user": user.email}
