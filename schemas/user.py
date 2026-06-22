from pydantic import BaseModel, Field, ConfigDict


class SUserAdd(BaseModel):
    name: str = Field(
        ..., min_length=2,
        max_length=100,
        title="Name of the user",
    )


class SUser(SUserAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)
