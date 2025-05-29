from fastapi import APIRouter, Query, HTTPException

from app.services.extract_service import ArticleService

router = APIRouter(prefix="/extract", tags=["articles"])

@router.get("/extract")
def extract_article(
    url: str = Query(..., description="URL of the article to extract")
):
    """
    Extract full article content and information from a URL
    """
    result = ArticleService.extract_article(url)
    if not result:
        raise HTTPException(status_code=404, detail="Could not extract article from URL")
    return result

@router.get("/summary")
def get_article_summary(
    url: str = Query(..., description="URL of the article to summarize"),
    max_length: int = Query(200, description="Maximum length of the summary")
):
    """
    Get a short summary of the article
    """
    summary = ArticleService.get_article_summary(url, max_length)
    if not summary:
        raise HTTPException(status_code=404, detail="Could not extract article summary")
    return {"summary": summary}

@router.get("/metadata")
def get_article_metadata(
    url: str = Query(..., description="URL of the article to extract metadata from")
):
    """
    Get article metadata (title, author, publication date)
    """
    metadata = ArticleService.get_article_metadata(url)
    if not metadata:
        raise HTTPException(status_code=404, detail="Could not extract article metadata")
    return metadata

@router.get("/images")
def get_article_images(
    url: str = Query(..., description="URL of the article to extract images from")
):
    """
    Get a list of images from an article
    """
    images = ArticleService.get_article_images(url)
    if images is None:
        raise HTTPException(status_code=404, detail="Could not extract article images")
    return {"images": images}