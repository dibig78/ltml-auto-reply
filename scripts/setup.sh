#!/bin/bash
set -e
echo "🔧 초기 설정..."
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
[ ! -f .env ] && cp .env.example .env && echo "⚠️ .env 파일을 수정하세요"
mkdir -p data/knowledge_base data/chroma_db data/downloads
echo "✅ 완료. 다음: .env 수정 → data/knowledge_base/에 PDF 추가 → python -m src.knowledge.ingest_tds"
