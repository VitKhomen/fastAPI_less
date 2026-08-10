from pydantic import BaseModel, EmailStr


class SJWTLogin(BaseModel):
    username: str  # або email — як хочеш
    password: str


class SToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SRefreshRequest(BaseModel):
    refresh_token: str
