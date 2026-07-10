from pydantic import BaseModel, Field, ConfigDict, field_validator,  EmailStr


class SUserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=0)
    email: EmailStr
    password: str = Field(..., min_length=6)
    is_subscribed: bool = Field(default=False)


class SUserBase(BaseModel):
    name: str
    age: int
    email: EmailStr
    is_subscribed: bool


class SUser(SUserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SUserAgeCheck(BaseModel):
    name: str
    age: int


class SUserAgeCheckResponse(SUserAgeCheck):
    is_adult: bool


class SContact(BaseModel):
    email: EmailStr
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=15,
        pattern=r"^\d+$",
        title="Phone number",
    )


BANNED_WORDS = ["badword1", "badword2", "badword3"]


class SUserFeedback(BaseModel):
    user_id: int
    feedback: str = Field(
        ..., min_length=10,
        max_length=500,
        title="Feedback from the user",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("feedback")
    @classmethod
    def check_banned_words(cls, v: str) -> str:
        v_lower = v.lower()
        for word in BANNED_WORDS:
            if word in v_lower:
                raise ValueError(
                    "Using banned words in feedback is not allowed.")
        return v
