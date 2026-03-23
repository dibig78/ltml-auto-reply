"""FastAPI 관리자 API — 대시보드 백엔드."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LT소재 고객문의 관리 API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Supabase 연동 시 아래 import 활성화:
# from supabase import create_client
# from src.config import SUPABASE_URL, SUPABASE_KEY
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

from src.api.routes import router
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
