import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

# Cache settings
CACHE_TTL_HOT_ARTICLES = 600  # 10 minutes
CACHE_TTL_HOT_KEYWORDS = 600  # 10 minutes
CACHE_TTL_SEARCH = 300  # 5 minutes

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100