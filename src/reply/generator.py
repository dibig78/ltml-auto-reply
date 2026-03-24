"""RAG + Claude API 답변 생성."""
import json
from pathlib import Path
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.knowledge.retriever import search_docs
from src.files.file_searcher import find_files

_client = None
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            return None
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def load_prompt(category: str) -> str:
    f = PROMPTS_DIR / f"{category}.txt"
    return f.read_text(encoding="utf-8") if f.exists() else "LT소재 고객문의에 대해 친절하고 전문적인 답변을 작성하세요."


# 카테고리별 템플릿 기반 폴백 답변
FALLBACK_TEMPLATES = {
    "tds_request": (
        "안녕하세요, LT소재입니다.\n\n"
        "요청하신 {product} 관련 자료를 확인 중입니다.\n"
        "{file_info}\n"
        "추가 문의 사항이 있으시면 언제든 연락 부탁드립니다.\n\n"
        "TEL: 031-330-1000 | E-mail: dwkim@ltml.co.kr\n"
        "감사합니다."
    ),
    "pricing": (
        "안녕하세요, LT소재입니다.\n\n"
        "문의해주신 {product} 관련 가격/견적 건은 영업 담당자가 직접 안내드리겠습니다.\n\n"
        "영업 담당: 031-330-1000 | dwkim@ltml.co.kr\n"
        "감사합니다."
    ),
    "general": (
        "안녕하세요, LT소재입니다.\n\n"
        "문의해주신 내용 확인 후 빠른 시일 내 답변드리겠습니다.\n\n"
        "TEL: 031-330-1000 | E-mail: dwkim@ltml.co.kr\n"
        "감사합니다."
    ),
}


def generate(title: str, content: str, category: str, author: str = "", email: str = None) -> dict:
    # RAG 검색
    rag_docs = search_docs(f"{title} {content}")
    context = "\n---\n".join([d["text"] for d in rag_docs])
    sources = [d["source"] for d in rag_docs if d.get("source")]

    # TDS 요청이면 파일 검색
    file_result = None
    if category == "tds_request":
        file_result = find_files(title, content)

    # 파일 정보 포맷팅
    file_info_text = "(없음)"
    if file_result and file_result.get("found"):
        source_label = "포털 DB" if file_result.get("source") == "portal" else "기술자료실"
        file_lines = [f"검색 소스: {source_label}"]
        for f in file_result.get("files", []):
            line = f"- {f['product_name']} / {f['file_name']} (score: {f['score']:.2f})"
            if f.get("portal_url"):
                line += f" | 다운로드: {f['portal_url']}"
            elif f.get("download_url"):
                line += f" | URL: {f['download_url']}"
            file_lines.append(line)
        file_info_text = "\n".join(file_lines)

    # Claude API 사용 가능하면 AI 답변
    client = _get_client()
    if client:
        try:
            system = load_prompt(category)
            user_msg = f"""## 고객 문의
제목: {title}
작성자: {author}
이메일: {email or '없음'}
내용: {content}

## RAG 참고 자료
{context or '(없음)'}

## 매칭 파일 정보
{file_info_text}

답변을 200~500자로 작성하세요. JSON: {{"reply_text":"", "confidence":0.0~1.0, "needs_review":true/false}}"""

            resp = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=1000, system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            try:
                result = json.loads(text)
            except Exception:
                result = {"reply_text": text, "confidence": 0.5, "needs_review": True}

            result["sources"] = sources
            result["matched_files"] = file_result.get("files", []) if file_result else []
            result["file_source"] = file_result.get("source", "none") if file_result else "none"
            result["customer_email"] = file_result.get("customer_email") if file_result else email
            if category == "pricing":
                result["needs_review"] = True
            return result
        except Exception as e:
            print(f"[WARN] Claude 답변 생성 실패, 템플릿 폴백: {e}")

    # 템플릿 기반 폴백
    template = FALLBACK_TEMPLATES.get(category, FALLBACK_TEMPLATES["general"])
    product = title.replace("자료 요청건", "").replace("요청", "").strip()
    reply_text = template.format(product=product, file_info=file_info_text)

    return {
        "reply_text": reply_text,
        "confidence": 0.3,
        "needs_review": True,
        "sources": sources,
        "matched_files": file_result.get("files", []) if file_result else [],
        "file_source": file_result.get("source", "none") if file_result else "none",
        "customer_email": file_result.get("customer_email") if file_result else email,
        "fallback": True,
    }
