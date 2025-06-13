#!/usr/bin/env python3
import requests
import hashlib
from supabase import create_client, Client
import feedparser
from bs4 import BeautifulSoup
from html import unescape
import sys
import re

# Supabase connection
supabase_url = "https://gykrrtrxzocmjusucnmj.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5a3JydHJ4em9jbWp1c3Vjbm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0MzA1ODMsImV4cCI6MjA2MDAwNjU4M30.d5Q8Qzm9yeBaTSM9vOjK-7jGMznnbGUD7HfIzJTdJAE"
supabase: Client = create_client(supabase_url, supabase_key)

def clean_html_entities(text):
    if not text:
        return ""
    return unescape(unescape(BeautifulSoup(text, "html.parser").text.strip()))

def extract_image_url(entry, description_html):
    # 1. media:content (chuẩn quốc tế)
    media_content = entry.get("media_content", [])
    if isinstance(media_content, list) and media_content:
        url = media_content[0].get("url")
        if url:
            return url

    # 2. media:thumbnail
    media_thumb = entry.get("media_thumbnail", [])
    if isinstance(media_thumb, list) and media_thumb:
        url = media_thumb[0].get("url")
        if url:
            return url

    # 3. enclosure (hay gặp ở nhiều báo)
    enclosure = entry.get("enclosures", [])
    if isinstance(enclosure, list) and enclosure:
        url = enclosure[0].get("href") or enclosure[0].get("url")
        if url and any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
            return url

    # 4. Browse các trường có chứa "url"
    for k, v in entry.items():
        if isinstance(v, list):
            for sub in v:
                if isinstance(sub, dict) and "url" in sub:
                    sub_url = sub["url"]
                    if sub_url and any(sub_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                        return sub_url
        elif isinstance(v, dict) and "url" in v:
            sub_url = v["url"]
            if sub_url and any(sub_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                return sub_url

    # 5. Tìm tất cả <img> trong description_html
    soup = BeautifulSoup(description_html, "html.parser")
    img_tags = soup.find_all("img")
    for img in img_tags:
        src = img.get("src")
        if src and any(src.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
            return src

    # 6. Regex: bắt ảnh nếu mô tả lỗi hoặc HTML không hợp lệ
    img_urls = re.findall(r'(https?://[^\s"\'<>]+?\.(?:jpg|jpeg|png|webp|gif))', description_html, re.IGNORECASE)
    if img_urls:
        return img_urls[0]

    return None

def calculate_md5(text):
    """Calculate MD5 hash of a given text."""
    if not text:
        return None
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_feed(url, timeout=30):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"⚠️ Could not load RSS ({url}) in {timeout} seconds: {e}")
        return None

def fetch_and_insert_articles():
    success_count = 0
    error_count = 0
    
    try:
        response = supabase.table("rss").select("id, rss_link").execute()
        rss_sources = response.data

        for source in rss_sources:
            rss_id = source["id"]
            url = source["rss_link"]

            feed = fetch_feed(url, timeout=30)
            if not feed or not feed.entries:
                print(f"⚠️ RSS unavailable or has no entries: {url}")
                continue

            try:
                for entry in feed.entries[:20]:  # Get max 20 first entries (adjustable)
                    title_raw = entry.get("title", "")
                    link = entry.get("link", "")
                    pubdate = entry.get("published", "")
                    description_html = entry.get("description", "")

                    if not link or not description_html:
                        print(f"⚠️ Skipped (missing link/description): {title_raw}")
                        continue

                    # Calculate MD5 hash for the link
                    link_md5 = calculate_md5(link)
                    if not link_md5:
                        print(f"⚠️ Skipped (could not generate MD5): {title_raw}")
                        continue

                    # Get image from RSS
                    image_url = extract_image_url(entry, description_html)
                    if not image_url:
                        print(f"⚠️ Skipped (no image): {title_raw}")
                        continue

                    # Clean description and title
                    soup = BeautifulSoup(description_html, "html.parser")
                    if soup.find("img"):
                        soup.find("img").decompose()
                    description_text = clean_html_entities(soup.get_text())
                    title = clean_html_entities(title_raw)

                    # Check if article exists using MD5
                    exists = supabase.table("article").select("article_id").eq("link_article_md5", link_md5).execute()
                    if exists.data:
                        print(f"⏭️ Already exists: {title}")
                        continue

                    # Insert article into database
                    supabase.table("article").insert({
                        "title": title,
                        "link": link,
                        "image_url": image_url,
                        "description": description_text,
                        "pub_date": pubdate,
                        "rss_id": rss_id,
                        "link_article_md5": link_md5
                    }).execute()

                    success_count += 1
                    print(f"✅ Inserted article: {title} | Image: {image_url}")

            except Exception as e:
                error_count += 1
                print(f"❌ Error processing RSS {url}: {e}")

    except Exception as e:
        print(f"❌ Critical error in processing: {e}")
        return 1  # Return non-zero exit code for systemd
    
    print(f"Summary: {success_count} articles added, {error_count} errors")
    return 0 if error_count == 0 else 1  # Return status for systemd

if __name__ == "__main__":
    print("🔄 Fetching and inserting new articles...")
    sys.exit(fetch_and_insert_articles())