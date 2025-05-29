from fastapi import APIRouter, HTTPException, Query
from app.services.recommend_service import recommend_service
from app.core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.get("/hot-articles")
async def get_hot_articles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size")
):
    """Get hot articles with pagination"""
    try:
        result = await recommend_service.get_hot_articles(page=page, page_size=page_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hot-keywords")
async def get_hot_keywords(
    limit: int = Query(50, ge=1, le=200, description="Number of keywords to return")
):
    """Get hot keywords"""
    try:
        result = await recommend_service.get_hot_keywords(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-cache")
async def reset_cache():
    """Reset recommendation cache"""
    try:
        result = await recommend_service.reset_recommendation_cache()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))