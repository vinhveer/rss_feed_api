from fastapi import APIRouter, HTTPException, Query
from app.services.search_service import search_service
from app.core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/articles")
async def search_articles(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size")
):
    """Search articles by title and description"""
    try:
        result = await search_service.search_articles(query=q, page=page, page_size=page_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))