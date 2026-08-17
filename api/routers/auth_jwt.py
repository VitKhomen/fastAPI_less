from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from database.engine import SessionDep
from services.auth_jwt import JWTService
from schemas.auth_jwt import SJWTLogin, SJWTRegister, SToken, SRefreshRequest
from dependencies.auth import get_current_user, require_role
from database.models import UserModel

router = APIRouter(prefix="/jwt", tags=["jwt-auth"])

# HTTPBearer читає заголовок: Authorization: Bearer <token>
bearer = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", status_code=201)
@limiter.limit("1/minute")
async def register(request: Request, credentials: SJWTLogin, session: SessionDep):
    if await JWTService.user_exists(session, credentials.username):
        raise HTTPException(status_code=409, detail="User already exists")
    await JWTService.register(session, credentials.username, credentials.password, credentials.role)
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
    current_user: UserModel = Depends(require_role("admin", "user"))
):
    return {
        "message": "Access granted",
        "user": current_user.email,
        "role": current_user.role
    }


# ← тільки admin
@router.delete("/admin/delete_user/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_role("admin"))
):
    return {"message": f"User {user_id} deleted by admin {current_user.email}"}


@router.put("/user/update_profile")
async def update_profile(
    current_user: UserModel = Depends(require_role("admin", "user"))
):
    return {"message": f"Profile updated for {current_user.email}"}


@router.get("/public/info")
async def public_info(
    current_user: UserModel = Depends(require_role("admin", "user", "guest"))
):
    return {"message": "Public info", "your_role": current_user.role}
