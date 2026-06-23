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


class SUserAdultCheck(SUserAdd):
    is_adult: bool = Field(
        ..., title="Indicates if the user is an adult"
    )
