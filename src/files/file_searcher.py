"""문의에서 키워드 추출 → file_index.json에서 파일 매칭."""
import json, re
from difflib import SequenceMatcher
from src.config import DATA_DIR, ANTHROPIC_API_KEY, CLAUDE_MODEL

INDEX_FILE = DATA_DIR / "file_index.json"

_client = None


def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            return None
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def extract_keywords(title: str, content: str) -> dict:
    """제품/문서 키워드 추출 — Claude API 또는 정규식 폴백."""
    client = _get_client()

    if client:
        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=300,
                messages=[{"role": "user", "content": f"""고객 문의에서 기술 문서 관련 정보를 JSON으로 추출하세요.
제목: {title}
내용: {content}
응답 형식: {{"product_names":[], "alloy":null, "type":null, "doc_type":"TDS", "customer_email":null}}"""}],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as e:
            print(f"[WARN] Claude 키워드 추출 실패, 정규식 폴백: {e}")

    # 정규식 기반 폴백
    return _extract_keywords_regex(title, content)


def _extract_keywords_regex(title: str, content: str) -> dict:
    """정규식으로 제품명, 합금, 문서 유형 추출."""
    combined = f"{title} {content}"

    # 제품명 패턴: RS60-1.2-A, HSE-HGF 10, LFM-48W, KR19 등
    product_patterns = [
        r'[A-Z]{2,5}[\-\s]?\d{1,3}[\-\s]?[\w\.\-]+',  # RS60-1.2-A
        r'[A-Z]{2,5}\-[\w]+(?:\s+[\w]+)?',  # HSE-HGF 10
        r'Sn\d+Pb\d+',  # Sn63Pb37
        r'SAC\d+',  # SAC305
    ]
    product_names = []
    for pat in product_patterns:
        matches = re.findall(pat, combined)
        product_names.extend(matches)
    # 중복 제거, 짧은 것 제외
    product_names = list(dict.fromkeys(n for n in product_names if len(n) >= 3))

    # 문서 유형
    doc_type = "TDS"
    doc_map = {"MSDS": "MSDS", "SDS": "MSDS", "TDS": "TDS", "COA": "ICP", "ICP": "ICP",
               "DATA SHEET": "TDS", "데이터시트": "TDS", "성적서": "ICP"}
    upper = combined.upper()
    for kw, dt in doc_map.items():
        if kw in upper:
            doc_type = dt
            break

    # 이메일 추출
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", combined)
    site_emails = {"dwkim@ltml.co.kr", "admin@ltml.co.kr"}
    customer_email = next((e for e in emails if e not in site_emails), None)

    # 합금 추출
    alloy = None
    alloy_match = re.search(r'(SAC\d+|Sn\d+Pb\d+|Pb[\-\s]?free|무연|유연)', combined, re.I)
    if alloy_match:
        alloy = alloy_match.group(1)

    return {
        "product_names": product_names[:5],
        "alloy": alloy,
        "type": None,
        "doc_type": doc_type,
        "customer_email": customer_email,
    }


def search_files(keywords: dict) -> list[dict]:
    """file_index.json에서 매칭 파일 검색."""
    if not INDEX_FILE.exists():
        return []
    index = json.loads(INDEX_FILE.read_text())
    doc_key = {"TDS": "tds", "MSDS": "msds", "SDS": "msds", "COA": "coa", "ICP": "icp"}.get(
        (keywords.get("doc_type") or "TDS").upper(), "tds"
    )
    candidates = index.get(doc_key, [])
    if not candidates:
        for v in index.values():
            candidates.extend(v)
    terms = [n for n in keywords.get("product_names", []) if n]
    if keywords.get("alloy"):
        terms.append(keywords["alloy"])
    if keywords.get("type"):
        terms.append(keywords["type"])
    if not terms:
        return []
    results = []
    for f in candidates:
        score, reasons = 0.0, []
        text = f"{f['product_name']} {f['file_name']} {' '.join(f.get('keywords', []))}".lower()
        for t in terms:
            if t.lower() in text:
                score += 0.4
                reasons.append(f"매칭:{t}")
            else:
                for kw in f.get("keywords", []):
                    sim = SequenceMatcher(None, t.lower(), kw.lower()).ratio()
                    if sim > 0.7:
                        score += sim * 0.3
                        reasons.append(f"유사:{t}≈{kw}")
                        break
        if score > 0:
            results.append({"file_info": f, "score": min(score, 1.0), "reason": ", ".join(reasons)})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]


def find_files(title: str, content: str) -> dict:
    """포털 DB 우선 검색 → 실패 시 legacy file_index.json 폴백."""
    kw = extract_keywords(title, content)

    # 1차: lt-docs-portal Supabase DB 검색
    try:
        from src.files.portal_searcher import search_portal_documents
        portal_results = search_portal_documents(kw)
        if portal_results:
            return {
                "found": True,
                "source": "portal",
                "files": [
                    {
                        "product_name": r["product_name"] or r["product_code"],
                        "file_name": r["file_name"],
                        "download_url": r["signed_url"] or "",
                        "portal_url": r["portal_url"],
                        "document_id": r["document_id"],
                        "doc_type": r["doc_type"],
                        "score": r["score"],
                    }
                    for r in portal_results
                ],
                "doc_type": kw.get("doc_type", "TDS"),
                "customer_email": kw.get("customer_email"),
            }
    except Exception as e:
        print(f"[WARN] 포털 검색 실패, legacy 폴백: {e}")

    # 2차: legacy file_index.json 폴백
    matches = search_files(kw)
    return {
        "found": len(matches) > 0,
        "source": "legacy",
        "files": [
            {
                "product_name": m["file_info"]["product_name"],
                "file_name": m["file_info"]["file_name"],
                "download_url": m["file_info"].get("download_url", ""),
                "score": m["score"],
            }
            for m in matches
        ],
        "doc_type": kw.get("doc_type", "TDS"),
        "customer_email": kw.get("customer_email"),
    }
