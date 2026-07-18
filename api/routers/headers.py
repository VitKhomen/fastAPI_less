from fastapi import APIRouter, Header, HTTPException


router = APIRouter(prefix="/headers", tags=["headers"])


@router.get("/")
async def get_headers(
    user_agent: str | None = Header(default=None),
    accept_language: str | None = Header(default=None)
):
    if not user_agent or not accept_language:
        raise HTTPException(status_code=400, detail="Missing required headers")
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }
