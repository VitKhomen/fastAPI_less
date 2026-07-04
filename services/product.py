from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ProductModel
from schemas.product import SProduct, SProductResponse


class ProductRepository:

    @classmethod
    async def get_product(
        cls,
        session: AsyncSession,
        product_id: int
    ) -> SProductResponse:
        result = await session.execute(select(ProductModel).where(ProductModel.id == product_id))
        product = result.scalar_one_or_none()

        if product is None:
            return None

        return SProductResponse.model_validate(product)

    @classmethod
    async def search_product(
            cls,
            session: AsyncSession,
            limit: int = 10,
            offset: int = 0,
            keyword: str | None = None,
            category: str | None = None
    ) -> list[SProductResponse]:
        query = select(ProductModel)

        if keyword:
            query = query.where(ProductModel.name.ilike(f"%{keyword}%"))

        if category:
            query = query.where(ProductModel.category == category)

        result = await session.execute(query.limit(limit).offset(offset))
        products = result.scalars().all()

        return [SProductResponse.model_validate(product) for product in products]
