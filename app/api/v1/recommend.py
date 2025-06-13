from typing import List
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

@router.get("/by-keywords")
async def get_articles_by_keywords(
    keywords: List[str] = Query(
        ..., 
        min_items=1, 
        max_items=25,       # was 10 → now 25
        description="List of keyword names (1–25 items)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size")
):
    """Recommend articles by keywords, sorted from newest to oldest"""
    try:
        result = await recommend_service.get_articles_by_keywords(
            keywords=keywords,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related-keywords-by-name")
async def related_keywords_by_name(
    name: str = Query(..., description="Keyword name to find relations for"),
    limit: int = Query(20, ge=1, le=100, description="Max number of related keywords")
):
    try:
        return await recommend_service.get_related_keywords_by_keyword_name(name, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related-keywords/{article_id}")
async def get_related_keywords_by_article(article_id: int):
    """Get keywords related to a specific article"""
    try:
        result = await recommend_service.get_related_keywords_by_article(article_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related-articles/{article_id}")
async def get_related_articles_by_article(
    article_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size")
):
    """Get related articles by shared keywords, excluding the given article"""
    try:
        result = await recommend_service.get_related_articles_by_article(
            article_id=article_id,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
