from pydantic import BaseModel, Field, ConfigDict


class SUserAdd(BaseModel):
    name: str = Field(
        ..., min_length=2,
        max_length=100,
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


class SUserFeedback(BaseModel):
    user_id: int
    feedback: str = Field(
        ..., min_length=1,
        max_length=256,
        title="Feedback from the user",
    )

    model_config = ConfigDict(from_attributes=True)
