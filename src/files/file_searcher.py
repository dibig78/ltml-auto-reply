"""문의에서 키워드 추출 → file_index.json에서 파일 매칭."""
import json, re
from difflib import SequenceMatcher
from src.config import DATA_DIR, ANTHROPIC_API_KEY, CLAUDE_MODEL
import anthropic

INDEX_FILE = DATA_DIR / "file_index.json"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def extract_keywords(title: str, content: str) -> dict:
    """Claude API로 제품/문서 키워드 추출."""
    resp = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=300,
        messages=[{"role": "user", "content": f"""고객 문의에서 기술 문서 관련 정보를 JSON으로 추출하세요.
제목: {title}
내용: {content}
응답 형식: {{"product_names":[], "alloy":null, "type":null, "doc_type":"TDS", "customer_email":null}}"""}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"): text = text.split("\n",1)[1].rsplit("```",1)[0]
    try: return json.loads(text)
    except: return {"product_names":[], "alloy":None, "type":None, "doc_type":"TDS", "customer_email":None}

def search_files(keywords: dict) -> list[dict]:
    """file_index.json에서 매칭 파일 검색."""
    if not INDEX_FILE.exists(): return []
    index = json.loads(INDEX_FILE.read_text())
    doc_key = {"TDS":"tds","MSDS":"msds","SDS":"msds","COA":"coa"}.get((keywords.get("doc_type") or "TDS").upper(), "tds")
    candidates = index.get(doc_key, [])
    if not candidates:
        for v in index.values(): candidates.extend(v)
    terms = [n for n in keywords.get("product_names",[]) if n]
    if keywords.get("alloy"): terms.append(keywords["alloy"])
    if keywords.get("type"): terms.append(keywords["type"])
    if not terms: return []
    results = []
    for f in candidates:
        score, reasons = 0.0, []
        text = f"{f['product_name']} {f['file_name']} {' '.join(f.get('keywords',[]))}".lower()
        for t in terms:
            if t.lower() in text:
                score += 0.4; reasons.append(f"매칭:{t}")
            else:
                for kw in f.get("keywords",[]):
                    sim = SequenceMatcher(None, t.lower(), kw.lower()).ratio()
                    if sim > 0.7: score += sim*0.3; reasons.append(f"유사:{t}≈{kw}"); break
        if score > 0:
            results.append({"file_info": f, "score": min(score,1.0), "reason": ", ".join(reasons)})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]

def find_files(title: str, content: str) -> dict:
    kw = extract_keywords(title, content)
    matches = search_files(kw)
    return {
        "found": len(matches)>0,
        "files": [{"product_name":m["file_info"]["product_name"], "file_name":m["file_info"]["file_name"],
                    "download_url":m["file_info"].get("download_url",""), "score":m["score"]} for m in matches],
        "doc_type": kw.get("doc_type","TDS"),
        "customer_email": kw.get("customer_email"),
    }
