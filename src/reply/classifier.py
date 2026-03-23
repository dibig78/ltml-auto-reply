"""문의 유형 자동 분류 (6종)."""
import json, anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PROMPT = """LT소재(솔더 페이스트 제조사) 고객 문의를 분류하세요.
카테고리: tds_request, product_recommend, pricing, technical, delivery, general
JSON만 응답: {{"category":"", "confidence":0.0~1.0, "reason":""}}

제목: {title}
내용: {content}"""

def classify(title: str, content: str) -> dict:
    resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=200,
        messages=[{"role":"user","content":PROMPT.format(title=title, content=content)}])
    text = resp.content[0].text.strip()
    if text.startswith("```"): text = text.split("\n",1)[1].rsplit("```",1)[0]
    try: return json.loads(text)
    except: return {"category":"general","confidence":0.5,"reason":"분류 실패"}
