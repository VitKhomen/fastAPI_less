from pydantic import BaseModel, Field, ConfigDict, field_validator


class SUserAdd(BaseModel):
    name: str = Field(
        ..., min_length=2,
        max_length=50,
        title="Name of the user",
    )
    age: int = Field(
        ..., ge=0,
        title="Age of the user",
    )


class SUser(SUserAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SUserAgeCheck(BaseModel):
    name: str
    age: int


class SUserAgeCheckResponse(SUserAgeCheck):
    is_adult: bool


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
                raise ValueError("Использование недопустимых слов")
        return v
