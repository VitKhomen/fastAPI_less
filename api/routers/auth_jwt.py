from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.engine import SessionDep
from services.auyh_jwt import JWTAuthService
from schemas.auth_jwt import SJWTLogin, SToken

router = APIRouter(prefix="/jwt", tags=["jwt-auth"])

# HTTPBearer читає заголовок: Authorization: Bearer <token>
bearer = HTTPBearer()


@router.post("/login", response_model=SToken)
async def login(credentials: SJWTLogin, session: SessionDep):
    token = await JWTAuthService.login(session, credentials.username, credentials.password)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return SToken(access_token=token)


@router.get("/protected_resource")
async def protected_resource(
    session: SessionDep,
    auth: HTTPAuthorizationCredentials = Depends(bearer)
    # auth.credentials — це сам токен рядок після "Bearer "
):
    user = await JWTAuthService.get_current_user(session, auth.credentials)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "message": "Access granted",
        "user": user.email
    }
