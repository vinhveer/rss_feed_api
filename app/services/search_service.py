from typing import List, Optional
from app.core.database import supabase
from app.core.redis import redis_client
from app.core.config import CACHE_TTL_SEARCH
import logging

logger = logging.getLogger(__name__)


class SearchService:
    @staticmethod
    async def search_articles(query: str, page: int = 1, page_size: int = 20) -> dict:
        """Search articles with caching"""
        if not query or not query.strip():
            return {
                "articles": [],
                "total": 0,
                "query": query,
                "page": page,
                "page_size": page_size
            }

        cache_key = f"search:{query.lower().strip()}:{page}:{page_size}"

        # Try to get from cache
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Search results retrieved from cache for query: {query}")
            return cached_data

        try:
            # Calculate offset
            offset = (page - 1) * page_size

            # Search in title and description
            search_query = f"%{query.strip()}%"

            # Query articles from database
            query_builder = supabase.table("article").select("""
                article_id,
                title,
                link,
                image_url,
                description,
                pub_date,
                rss_id
            """).or_(f"title.ilike.{search_query},description.ilike.{search_query}")

            # Get total count first
            count_result = query_builder.execute()
            total = len(count_result.data)

            # Get paginated results
            result = query_builder.order("pub_date", desc=True).range(offset, offset + page_size - 1).execute()

            response_data = {
                "articles": result.data,
                "total": total,
                "query": query,
                "page": page,
                "page_size": page_size
            }

            # Cache the result
            await redis_client.set(cache_key, response_data, CACHE_TTL_SEARCH)

            logger.info(f"Search results retrieved from database and cached for query: {query}")
            return response_data

        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            raise Exception(f"Failed to search articles: {str(e)}")


# Global service instance
search_service = SearchService()