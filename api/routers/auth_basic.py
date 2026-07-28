import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import SessionDep
from schemas.user import SUserCreate, SUser
from schemas.auth_basic import UserInDB, User
from services.auth_basic import AuthService
from services.users import UserRepository

router = APIRouter(prefix="/auth_basic", tags=["auth_basic"])

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    HTTPBasicCredentials автоматично розпаковує заголовок:
    Authorization: Basic base64(username:password)
    і дає credentials.username і credentials.password
    """

    user = AuthService.get_user_by_credentials(credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
            # ↑ цей заголовок змушує браузер знову показати вікно логіну
            # без нього браузер просто покаже 401 і не запропонує ввести знову
        )

    return credentials.username


@router.post("/register", status_code=201)
async def register(user_data: SUserCreate, session: SessionDep):
    return await UserRepository.create_user(session, user_data)


@router.post("/login")
async def login(username: str = Depends(verify_credentials)):
    return {"message": "You got my secret, welcome"}
