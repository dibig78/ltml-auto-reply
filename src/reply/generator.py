"""RAG + Claude API 답변 생성."""
import json, anthropic
from pathlib import Path
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.knowledge.retriever import search_docs
from src.files.file_searcher import find_files

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(category: str) -> str:
    f = PROMPTS_DIR / f"{category}.txt"
    return f.read_text() if f.exists() else (PROMPTS_DIR / "general.txt").read_text()

def generate(title: str, content: str, category: str, author: str = "", email: str = None) -> dict:
    # RAG 검색
    rag_docs = search_docs(f"{title} {content}")
    context = "\n---\n".join([d["text"] for d in rag_docs])
    sources = [d["source"] for d in rag_docs if d.get("source")]

    # TDS 요청이면 파일 검색
    file_result = None
    if category == "tds_request":
        file_result = find_files(title, content)

    system = load_prompt(category)
    user_msg = f"""## 고객 문의
제목: {title}
작성자: {author}
이메일: {email or '없음'}
내용: {content}

## RAG 참고 자료
{context or '(없음)'}

## 매칭 파일 정보
{json.dumps(file_result, ensure_ascii=False) if file_result else '(없음)'}

답변을 200~500자로 작성하세요. JSON: {{"reply_text":"", "confidence":0.0~1.0, "needs_review":true/false}}"""

    resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=1000, system=system,
        messages=[{"role":"user","content":user_msg}])
    text = resp.content[0].text.strip()
    if text.startswith("```"): text = text.split("\n",1)[1].rsplit("```",1)[0]
    try: result = json.loads(text)
    except: result = {"reply_text": text, "confidence": 0.5, "needs_review": True}
    result["sources"] = sources
    result["matched_files"] = file_result.get("files",[]) if file_result else []
    result["customer_email"] = file_result.get("customer_email") if file_result else email
    if category == "pricing": result["needs_review"] = True
    return result
