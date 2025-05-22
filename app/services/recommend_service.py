from typing import List, Optional
from app.core.database import supabase
from app.core.redis import redis_client
from app.core.config import CACHE_TTL_HOT_ARTICLES, CACHE_TTL_HOT_KEYWORDS
import logging

logger = logging.getLogger(__name__)


class RecommendService:
    @staticmethod
    async def get_hot_articles(page: int = 1, page_size: int = 20) -> dict:
        """Get hot articles with caching"""
        cache_key = f"hot_articles:{page}:{page_size}"

        # Try to get from cache
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Hot articles retrieved from cache for page {page}")
            return cached_data

        try:
            # Calculate offset
            offset = (page - 1) * page_size

            # Query hot articles from database
            # Sắp xếp theo pub_date mới nhất và có thể thêm logic phức tạp hơn
            query = supabase.table("article").select("""
                article_id,
                title,
                link,
                image_url,
                description,
                pub_date,
                rss_id
            """).order("pub_date", desc=True).range(offset, offset + page_size - 1)

            result = query.execute()

            # Get total count
            count_result = supabase.table("article").select("article_id", count="exact").execute()
            total = count_result.count

            response_data = {
                "articles": result.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }

            # Cache the result
            await redis_client.set(cache_key, response_data, CACHE_TTL_HOT_ARTICLES)

            logger.info(f"Hot articles retrieved from database and cached for page {page}")
            return response_data

        except Exception as e:
            logger.error(f"Error getting hot articles: {str(e)}")
            raise Exception(f"Failed to get hot articles: {str(e)}")

    @staticmethod
    async def get_hot_keywords(limit: int = 50) -> dict:
        """Get hot keywords with caching"""
        cache_key = f"hot_keywords:{limit}"

        # Try to get from cache
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.info("Hot keywords retrieved from cache")
            return cached_data

        try:
            # Query hot keywords from database
            # Join article_keyword và keyword để đếm số lượng bài viết cho mỗi keyword
            query = supabase.rpc("get_hot_keywords", {"limit_count": limit})
            result = query.execute()

            # Nếu function không tồn tại, dùng query thông thường
            if not result.data:
                # Fallback query
                query = supabase.table("keyword").select("""
                    keyword_id,
                    keyword_name,
                    article_keyword!inner(article_id)
                """).limit(limit)
                result = query.execute()

                # Process data to count articles per keyword
                keyword_counts = {}
                for item in result.data:
                    keyword_id = item['keyword_id']
                    if keyword_id not in keyword_counts:
                        keyword_counts[keyword_id] = {
                            'keyword_id': keyword_id,
                            'keyword_name': item['keyword_name'],
                            'count': 0
                        }
                    keyword_counts[keyword_id]['count'] += 1

                # Sort by count and take top keywords
                sorted_keywords = sorted(keyword_counts.values(),
                                         key=lambda x: x['count'], reverse=True)[:limit]
                keywords_data = [{'keyword_id': k['keyword_id'],
                                  'keyword_name': k['keyword_name']} for k in sorted_keywords]
            else:
                keywords_data = result.data

            response_data = {
                "keywords": keywords_data,
                "total": len(keywords_data)
            }

            # Cache the result
            await redis_client.set(cache_key, response_data, CACHE_TTL_HOT_KEYWORDS)

            logger.info("Hot keywords retrieved from database and cached")
            return response_data

        except Exception as e:
            logger.error(f"Error getting hot keywords: {str(e)}")
            raise Exception(f"Failed to get hot keywords: {str(e)}")

    @staticmethod
    async def reset_recommendation_cache() -> dict:
        """Reset all recommendation caches"""
        try:
            # Delete cache keys pattern
            # Since we can't easily delete pattern in Redis, we'll delete common keys
            keys_to_delete = []

            # Common cache keys
            for page in range(1, 6):  # Delete first 5 pages cache
                for page_size in [10, 20, 50]:
                    keys_to_delete.append(f"hot_articles:{page}:{page_size}")

            for limit in [20, 50, 100]:
                keys_to_delete.append(f"hot_keywords:{limit}")

            # Delete the keys
            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)

            logger.info("Recommendation cache reset successfully")
            return {
                "success": True,
                "message": "Cache reset successfully"
            }

        except Exception as e:
            logger.error(f"Error resetting cache: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to reset cache: {str(e)}"
            }


# Global service instance
recommend_service = RecommendService()