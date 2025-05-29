import trafilatura
import json
from typing import Dict, List, Optional

def extract_article(url: str) -> Optional[Dict]:
    """
    Trích xuất nội dung bài báo từ URL

    Returns:
        Dictionary chứa các thông tin:
        - title: Tiêu đề bài viết
        - text: Nội dung chính
        - images: Danh sách URL ảnh
        - pubDate: Ngày đăng bài
        - author: Tác giả
        Hoặc None nếu trích xuất thất bại
    """
    # Tải nội dung từ URL
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print(f"Không tải được URL: {url}")
        return None

    # Trích xuất nội dung Markdown và metadata riêng biệt
    markdown_content = trafilatura.extract(
        downloaded,
        url=url,
        output_format="markdown",
        include_images=True,
        include_links=True
    )

    # Trích xuất metadata dưới dạng JSON
    metadata_json = trafilatura.extract(
        downloaded,
        url=url,
        output_format="json",
        with_metadata=True,
        include_images=True
    )

    if not markdown_content or not metadata_json:
        print(f"Không trích xuất được nội dung từ: {url}")
        return None

    # Chuyển JSON metadata thành dictionary
    metadata = json.loads(metadata_json)

    # Trả về thông tin bài viết với nội dung dạng markdown
    return {
        "title": metadata.get("title") or "Không rõ",
        "text": markdown_content,  # Nội dung dạng markdown có chứa link ảnh
        "images": metadata.get("images") or [],
        "pubDate": metadata.get("date") or "Không rõ",
        "author": metadata.get("author") or "Không rõ"
    }


class ArticleService:
    """Xử lý và trích xuất thông tin bài báo"""

    @staticmethod
    def extract_article(url: str) -> Optional[Dict]:
        """Trích xuất toàn bộ thông tin bài báo từ URL"""
        return extract_article(url)

    @staticmethod
    def get_article_summary(url: str, max_length: int = 200) -> Optional[str]:
        """Tạo bản tóm tắt ngắn của bài báo"""
        article_data = extract_article(url)
        if not article_data or not article_data["text"]:
            return None

        # Tạo tóm tắt từ phần đầu nội dung
        summary = article_data["text"][:max_length]
        if len(article_data["text"]) > max_length:
            summary += "..."

        return summary

    @staticmethod
    def get_article_metadata(url: str) -> Optional[Dict]:
        """Trích xuất metadata của bài báo"""
        article_data = extract_article(url)
        if not article_data:
            return None

        return {
            "title": article_data["title"],
            "author": article_data["author"],
            "pubDate": article_data["pubDate"]
        }

    @staticmethod
    def get_article_images(url: str) -> Optional[List[str]]:
        """Trích xuất danh sách hình ảnh từ bài báo"""
        article_data = extract_article(url)
        if not article_data:
            return None

        return article_data["images"]