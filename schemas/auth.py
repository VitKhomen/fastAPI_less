from pydantic import BaseModel, EmailStr


class SLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SLoginResponse(BaseModel):
    message: str
