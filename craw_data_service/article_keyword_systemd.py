import re
import time
import hashlib
from collections import Counter
from supabase import create_client
from underthesea import pos_tag as pos_tag_vi
from deep_translator import GoogleTranslator

# Kết nối Supabase
supabase_url = "https://gykrrtrxzocmjusucnmj.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5a3JydHJ4em9jbWp1c3Vjbm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0MzA1ODMsImV4cCI6MjA2MDAwNjU4M30.d5Q8Qzm9yeBaTSM9vOjK-7jGMznnbGUD7HfIzJTdJAE"
supabase = create_client(supabase_url, supabase_key)
translator = GoogleTranslator(source='auto', target='vi')

# Load stopwords tiếng Việt
with open('/article_service/vietnamese-stopwords.txt', 'r', encoding='utf-8') as f:
    stopwords_vi = set(line.strip().lower() for line in f if line.strip())

def is_valid_keyword(word):
    word = word.strip()
    tokens = word.split()
    if len(word) <= 1:
        return False
    if re.search(r"[^a-zA-Z0-9\sàáảãạâầấẩẫậăằắẳẵặđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]", word):
        return False
    if "'" in word or '"' in word:
        return False
    if any(len(token) <= 2 for token in tokens):
        return False
    return len(tokens) >= 2

def is_stopword(word):
    return any(token in stopwords_vi for token in word.lower().split())

def translate_text(text, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"⚠️ Lỗi dịch: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return text

def generate_md5(text):
    """Tạo mã băm MD5 cho từ khóa"""
    return hashlib.md5(text.lower().encode('utf-8')).hexdigest()

def upsert_keyword_get_id(keyword):
    # Tạo MD5 hash từ keyword
    keyword_md5 = generate_md5(keyword)
    
    # Tìm kiếm theo MD5 hash (hiệu quả hơn vì đã đánh chỉ mục)
    existing = supabase.table("keyword").select("keyword_id").eq("keyword_md5", keyword_md5).execute()
    
    if existing.data:
        return existing.data[0]["keyword_id"]
    
    # Nếu không tồn tại, thêm mới cả keyword và MD5 hash
    insert_resp = supabase.table("keyword").insert({
        "keyword_name": keyword,
        "keyword_md5": keyword_md5
    }).execute()
    
    return insert_resp.data[0]["keyword_id"]

def insert_article_keyword(article_id, keyword_id):
    existing = supabase.table("article_keyword")\
        .select("*").eq("article_id", article_id).eq("keyword_id", keyword_id).execute()
    if existing.data:
        return
    supabase.table("article_keyword").insert({
        "article_id": article_id,
        "keyword_id": keyword_id
    }).execute()

def extract_keywords_from_articles():
    response = supabase.table("article").select("title,article_id,rss_id").execute()
    articles = response.data

    for article in articles:
        title = article.get("title", "")
        article_id = article.get("article_id", "")
        rss_id = article.get("rss_id", "")

        if not title or not rss_id:
            continue

        try:
            rss_resp = supabase.table("rss").select("newspaper_id").eq("id", rss_id).execute()
            if not rss_resp.data:
                continue
            newspaper_id = rss_resp.data[0].get("newspaper_id", "")

            is_vn = True
            if newspaper_id:
                news_resp = supabase.table("newspaper").select("is_vn").eq("newspaper_id", newspaper_id).execute()
                is_vn = news_resp.data[0].get("is_vn", True) if news_resp.data else True

            if not is_vn:
                title = translate_text(title)

            pos = pos_tag_vi(title)
            keywords = [word for word, tag in pos if tag.startswith("N")]

            filtered = [
                word.lower() for word in keywords
                if is_valid_keyword(word) and not is_stopword(word)
            ]

            for kw in set(filtered):
                keyword_id = upsert_keyword_get_id(kw)
                insert_article_keyword(article_id, keyword_id)

        except Exception as e:
            print(f"❌ Lỗi xử lý bài viết: {title} | {e}")

# Lặp lại sau mỗi 24 giờ
if __name__ == "__main__":
    while True:
        print("🔄 Đang trích xuất và ghi từ khóa...")
        extract_keywords_from_articles()
        print("✅ Hoàn tất. Chờ 24 giờ để chạy lại...\n")
        time.sleep(2000)  # 24 giờ
