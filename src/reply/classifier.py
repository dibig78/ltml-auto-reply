"""문의 유형 자동 분류 (6종)."""
import json
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client = None

def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            return None
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client

PROMPT = """LT소재(솔더 페이스트 제조사) 고객 문의를 분류하세요.
카테고리: tds_request, product_recommend, pricing, technical, delivery, general
JSON만 응답: {{"category":"", "confidence":0.0~1.0, "reason":""}}

제목: {title}
내용: {content}"""


# 키워드 기반 폴백 분류
KEYWORD_RULES = [
    (["TDS", "MSDS", "SDS", "CoA", "ICP", "자료 요청", "자료요청", "Data Sheet", "데이터시트", "성적서"], "tds_request"),
    (["가격", "견적", "단가", "샘플", "price", "quotation", "quote"], "pricing"),
    (["추천", "recommend", "어떤 제품", "적합한", "공정"], "product_recommend"),
    (["납기", "배송", "재고", "delivery", "출하"], "delivery"),
    (["보이드", "void", "인쇄", "젖음", "wetting", "reflow", "리플로우", "프로파일", "온도"], "technical"),
]


def classify(title: str, content: str) -> dict:
    client = _get_client()
    combined = f"{title} {content}".upper()

    # API 사용 가능하면 Claude로 분류
    if client:
        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=200,
                messages=[{"role": "user", "content": PROMPT.format(title=title, content=content)}],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as e:
            print(f"[WARN] Claude 분류 실패, 키워드 폴백: {e}")

    # 키워드 기반 폴백
    for keywords, category in KEYWORD_RULES:
        if any(kw.upper() in combined for kw in keywords):
            return {"category": category, "confidence": 0.7, "reason": "키워드 매칭 (API 미사용)"}

    return {"category": "general", "confidence": 0.5, "reason": "분류 불가 (API 미사용)"}
