from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import SessionDep
from services.product import ProductRepository
from schemas.product import SProduct, SProductResponse


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search")
async def search_products(
    session: SessionDep,
    limit: int = 10,
    offset: int = 0,
    keyword: str | None = None,
    category: str | None = None
):
    result = await ProductRepository.search_product(
        session,
        limit=limit,
        offset=offset,
        keyword=keyword,
        category=category
    )
    return result


@router.get("/{product_id}")
async def get_product(product_id: int, session: SessionDep):
    result = await ProductRepository.get_product(session, product_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return result
