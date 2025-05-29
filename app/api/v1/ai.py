import os
import uuid

from fastapi import APIRouter, Query, HTTPException, File, UploadFile

from app.services.ai_service import GeminiService
from app.services.extract_service import ArticleService

router = APIRouter(prefix="/gemini", tags=["gemini"])

@router.post("/generate")
def generate_text(
        prompt: str = Query(..., description="Prompt for text generation"),
        max_tokens: int = Query(1000, description="Maximum number of tokens to generate"),
        temperature: float = Query(0.7, description="Temperature for text generation")
):
    """Generate text using Gemini API"""
    try:
        response = GeminiService.generate_text(prompt, max_tokens, temperature)
        return {"generated_text": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


@router.post("/analyze-image")
async def analyze_image(
        prompt: str = Query(..., description="Prompt for image analysis"),
        image: UploadFile = File(...)
):
    """Analyze an image using Gemini Vision API"""
    try:
        # Save uploaded image temporarily
        temp_image_path = f"/tmp/{uuid.uuid4()}.jpg"
        with open(temp_image_path, "wb") as buffer:
            buffer.write(await image.read())

        # Analyze the image
        result = GeminiService.analyze_image(temp_image_path, prompt)

        # Clean up
        os.remove(temp_image_path)

        return {"analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")

@router.post("/translate-article")
def translate_article(
    url: str = Query(..., description="URL of the article to translate"),
    target_lang: str = Query("vi", description="Target language code")
):
    """Extract and translate an article from a URL"""
    try:
        # Extract article content
        article_data = ArticleService.extract_article(url)
        if not article_data:
            raise HTTPException(status_code=404, detail="Could not extract article from URL")
            
        # Get the text content
        text = article_data["text"]
        
        # Check if the article is too long (about 1200 words)
        if len(text.split()) > 1500:
            raise HTTPException(status_code=400, detail="Article is too long (max 1500 words)")
            
        # Translate the text
        translated_text = GeminiService.translate_text(text, "auto", target_lang, max_tokens=2500)
        
        # Return results
        return {
            "original_title": article_data["title"],
            "original_text": text,
            "translated_text": translated_text,
            "metadata": {
                "author": article_data["author"],
                "pubDate": article_data["pubDate"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating article: {str(e)}")