from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    guest = "guest"


class SJWTRegister(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user  # за замовчуванням — user


class SJWTLogin(BaseModel):
    username: str
    password: str


class SToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SRefreshRequest(BaseModel):
    refresh_token: str
