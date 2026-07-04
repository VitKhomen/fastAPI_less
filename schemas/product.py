from pydantic import BaseModel, Field, ConfigDict, field_validator,  EmailStr


class SProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    category: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., ge=0.0)


class SProductResponse(SProduct):
    product_id: int

    model_config = ConfigDict(from_attributes=True)
