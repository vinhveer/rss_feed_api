from typing import List
from app.core.database import supabase
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RecommendService:
    @staticmethod
    async def get_hot_articles(page: int = 1, page_size: int = 20) -> dict:
        """Get hot articles without caching"""
        try:
            # Calculate offset
            offset = (page - 1) * page_size

            # Get current date for filtering
            today = datetime.now().strftime('%Y-%m-%d')

            # Query hot articles from database
            query = supabase.table("article").select(
                """
                article_id,
                title,
                link,
                image_url,
                description,
                pub_date,
                rss_id
            """
            ).lte("pub_date", today).order("pub_date", desc=True).range(offset, offset + page_size - 1)

            result = query.execute()

            # Get total count with date filter
            count_result = supabase.table("article").select("article_id", count="exact").lte("pub_date", today).execute()
            total = count_result.count

            response_data = {
                "articles": result.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }

            logger.info(f"Hot articles retrieved from database for page {page}")
            return response_data

        except Exception as e:
            logger.error(f"Error getting hot articles: {str(e)}")
            raise Exception(f"Failed to get hot articles: {str(e)}")

    @staticmethod
    async def get_hot_keywords(limit: int = 50) -> dict:
        """Get hot keywords without caching"""
        try:
            # Query hot keywords from database using RPC
            query = supabase.rpc("get_hot_keywords", {"limit_count": limit})
            result = query.execute()

            # Nếu function không tồn tại, dùng query thông thường
            if not result.data:
                # Fallback query
                query = supabase.table("keyword").select(
                    """
                    keyword_id,
                    keyword_name,
                    article_keyword!inner(article_id)
                """
                ).limit(limit)
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

            logger.info("Hot keywords retrieved from database")
            return response_data

        except Exception as e:
            logger.error(f"Error getting hot keywords: {str(e)}")
            raise Exception(f"Failed to get hot keywords: {str(e)}")

    @staticmethod
    async def reset_recommendation_cache() -> dict:
        """Stub method (no cache used)"""
        logger.info("No cache to reset in this version.")
        return {
            "success": True,
            "message": "No cache used; nothing to reset."
        }

    @staticmethod
    async def get_articles_by_keywords(keywords: List[str],
                                       page: int = 1,
                                       page_size: int = 20) -> dict:
        """
        Recommend articles by a list of keyword names, sorted by pub_date desc.
        - keywords: list of keyword_name (1–10 items)
        - page, page_size: pagination
        """
        try:
            # 1) Lấy keyword_id
            kw_res = supabase.table("keyword") \
                              .select("keyword_id") \
                              .in_("keyword_name", keywords) \
                              .execute()
            kw_ids = [row["keyword_id"] for row in kw_res.data]
            if not kw_ids:
                return {"articles": [], "total": 0, "page": page, "page_size": page_size}

            # 2) Lấy danh sách article_id chứa ít nhất 1 trong kw_ids
            ak_res = supabase.table("article_keyword") \
                             .select("article_id") \
                             .in_("keyword_id", kw_ids) \
                             .execute()
            article_ids = list({row["article_id"] for row in ak_res.data})
            total = len(article_ids)

            if total == 0:
                return {"articles": [], "total": 0, "page": page, "page_size": page_size}

            # 3) Phân trang
            start = (page - 1) * page_size
            end = start + page_size
            page_ids = article_ids[start:end]
            if not page_ids:
                return {"articles": [], "total": total, "page": page, "page_size": page_size}

            # 4) Lấy chi tiết bài viết, sắp xếp theo pub_date desc
            art_res = supabase.table("article") \
                              .select(
                                  """
                                      article_id,
                                      title,
                                      link,
                                      image_url,
                                      description,
                                      pub_date,
                                      rss_id
                                  """
                              ) \
                              .in_("article_id", page_ids) \
                              .order("pub_date", desc=True) \
                              .execute()

            response = {
                "articles": art_res.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            logger.info(f"Retrieved {len(art_res.data)} articles by keywords {keywords}, sorted by date")
            return response

        except Exception as e:
            logger.error(f"Error in get_articles_by_keywords: {e}")
            raise Exception(f"Failed to recommend by keywords: {e}")

    @staticmethod
    async def get_related_keywords_by_keyword_name(keyword_name: str, limit: int = 20) -> dict:
        """
        Lấy danh sách các keyword liên quan đến 1 keyword cho trước (theo tên):
        - Tìm keyword_id từ keyword_name
        - Lấy tất cả article chứa keyword đó
        - Lấy tất cả các keyword khác xuất hiện trong những article đó
        - Loại bỏ chính keyword đầu vào, đếm tần suất và trả về top `limit`
        """
        try:
            # 1) Lấy keyword_id tương ứng với keyword_name
            kw_lookup = supabase.table("keyword") \
                                .select("keyword_id") \
                                .eq("keyword_name", keyword_name) \
                                .single() \
                                .execute()
            if not kw_lookup.data:
                return {"keywords": []}
            keyword_id = kw_lookup.data["keyword_id"]

            # 2) Lấy tất cả article_id có chứa keyword_id này
            ak_res = supabase.table("article_keyword") \
                             .select("article_id") \
                             .eq("keyword_id", keyword_id) \
                             .execute()
            article_ids = [row["article_id"] for row in ak_res.data]
            if not article_ids:
                return {"keywords": []}

            # 3) Lấy các keyword_id khác trong những article đó
            co_ak_res = supabase.table("article_keyword") \
                                .select("keyword_id") \
                                .in_("article_id", article_ids) \
                                .execute()

            # Đếm tần suất
            freq: dict[int, int] = {}
            for row in co_ak_res.data:
                kid = row["keyword_id"]
                if kid == keyword_id:
                    continue
                freq[kid] = freq.get(kid, 0) + 1

            if not freq:
                return {"keywords": []}

            # 4) Lấy top limit keyword_ids
            top_kids = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
            top_ids = [kid for kid, _ in top_kids]

            # 5) Lấy chi tiết tên keyword
            kw_res = supabase.table("keyword") \
                             .select("keyword_id, keyword_name") \
                             .in_("keyword_id", top_ids) \
                             .execute()

            # Build result với count
            related = []
            for kw in kw_res.data:
                related.append({
                    "keyword_id": kw["keyword_id"],
                    "keyword_name": kw["keyword_name"],
                    "count": freq.get(kw["keyword_id"], 0)
                })

            return {"keywords": related}

        except Exception as e:
            logger.error(f"Error in get_related_keywords_by_keyword_name: {e}")
            raise Exception(f"Failed to get related keywords by name: {e}")

    @staticmethod
    async def get_related_articles_by_article(article_id: int,
                                              page: int = 1,
                                              page_size: int = 20) -> dict:
        """
        Lấy danh sách bài viết liên quan đến 1 bài viết (cùng keyword), trừ chính nó.
        """
        try:
            # 1) Lấy keyword_id của bài viết gốc
            ak_res = supabase.table("article_keyword") \
                             .select("keyword_id") \
                             .eq("article_id", article_id) \
                             .execute()

            keyword_ids = [row["keyword_id"] for row in ak_res.data]
            if not keyword_ids:
                return {"articles": [], "total": 0, "page": page, "page_size": page_size}

            # 2) Tìm các bài viết có ít nhất 1 keyword giống, loại trừ chính nó
            related_ak_res = supabase.table("article_keyword") \
                                     .select("article_id") \
                                     .in_("keyword_id", keyword_ids) \
                                     .neq("article_id", article_id) \
                                     .execute()

            article_ids = list({row["article_id"] for row in related_ak_res.data})
            total = len(article_ids)

            if total == 0:
                return {"articles": [], "total": 0, "page": page, "page_size": page_size}

            # 3) Phân trang
            start = (page - 1) * page_size
            end = start + page_size
            page_ids = article_ids[start:end]

            # 4) Lấy chi tiết bài viết và sắp xếp theo pub_date giảm dần
            articles_res = supabase.table("article") \
                                   .select(
                                       """
                                           article_id,
                                           title,
                                           link,
                                           image_url,
                                           description,
                                           pub_date,
                                           rss_id
                                       """
                                   ) \
                                   .in_("article_id", page_ids) \
                                   .order("pub_date", desc=True) \
                                   .execute()

            return {
                "articles": articles_res.data,
                "total": total,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            logger.error(f"Error in get_related_articles_by_article: {e}")
            raise Exception(f"Failed to get related articles: {e}")

# Global service instance
recommend_service = RecommendService()