import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_base"
CHROMA_DIR = DATA_DIR / "chroma_db"

LTML_BASE_URL = os.getenv("LTML_BASE_URL", "https://www.ltml.co.kr")
LTML_BOARD_URL = f"{LTML_BASE_URL}/customer/02/"
LTML_ADMIN_ID = os.getenv("LTML_ADMIN_ID", "")
LTML_ADMIN_PW = os.getenv("LTML_ADMIN_PW", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6-20250514"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "dwkim@ltml.co.kr")
SMTP_PASS = os.getenv("SMTP_PASS", "")

INQUIRY_TYPES = {
    "tds_request": "TDS/MSDS/CoA 요청",
    "product_recommend": "제품 추천",
    "pricing": "가격/견적/샘플",
    "technical": "기술 문의",
    "delivery": "납기/배송",
    "general": "기타",
}
