"""lt-docs-portal Supabase DB에서 문서 검색 + signed URL 생성."""
from difflib import SequenceMatcher
from src.db.supabase_client import query_documents, create_signed_url
from src.config import PORTAL_BASE_URL

# 문의에서 추출된 doc_type 키워드 → DB doc_type 매핑
DOC_TYPE_MAP = {
    "TDS": "TDS",
    "MSDS": "MSDS",
    "SDS": "MSDS",
    "ICP": "ICP",
    "COA": "ICP",  # CoA는 ICP 카테고리에 포함
    "OTHER": "OTHER",
}


def search_portal_documents(keywords: dict) -> list[dict]:
    """포털 documents 테이블에서 제품 문서 검색.

    Args:
        keywords: extract_keywords()의 반환값
            {"product_names": [], "alloy": None, "type": None, "doc_type": "TDS"}

    Returns:
        [{"document_id", "product_code", "product_name", "doc_type",
          "file_name", "file_path", "signed_url", "portal_url", "score"}]
    """
    raw_doc_type = (keywords.get("doc_type") or "TDS").upper()
    doc_type = DOC_TYPE_MAP.get(raw_doc_type, "TDS")

    # 검색어 조합
    search_terms = [n for n in keywords.get("product_names", []) if n]
    if keywords.get("alloy"):
        search_terms.append(keywords["alloy"])
    if keywords.get("type"):
        search_terms.append(keywords["type"])

    if not search_terms:
        return []

    # 각 검색어로 DB 쿼리 후 결과 합산
    seen_ids = set()
    all_docs = []

    for term in search_terms:
        docs = query_documents(product_code=term, doc_type=doc_type, limit=10)
        for d in docs:
            if d["id"] not in seen_ids:
                seen_ids.add(d["id"])
                all_docs.append(d)

        # product_code로 못 찾으면 전체 검색어로 시도
        if not docs:
            docs = query_documents(search_term=term, doc_type=doc_type, limit=10)
            for d in docs:
                if d["id"] not in seen_ids:
                    seen_ids.add(d["id"])
                    all_docs.append(d)

    if not all_docs:
        # doc_type 없이 재시도
        for term in search_terms:
            docs = query_documents(search_term=term, limit=10)
            for d in docs:
                if d["id"] not in seen_ids:
                    seen_ids.add(d["id"])
                    all_docs.append(d)

    # 점수 계산
    results = []
    for doc in all_docs:
        score = _calc_score(doc, search_terms, doc_type)
        if score > 0:
            signed_url = create_signed_url(doc["file_path"], expires_in=604800)  # 7일
            results.append({
                "document_id": doc["id"],
                "product_code": doc.get("product_code", ""),
                "product_name": doc.get("product_name", ""),
                "doc_type": doc.get("doc_type", ""),
                "language": doc.get("language", "ko"),
                "file_name": doc.get("file_name", ""),
                "file_path": doc.get("file_path", ""),
                "signed_url": signed_url,
                "portal_url": f"{PORTAL_BASE_URL}?product_code={doc.get('product_code', '')}",
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]


def _calc_score(doc: dict, terms: list[str], target_doc_type: str) -> float:
    """검색 결과 유사도 점수 계산."""
    score = 0.0
    text = f"{doc.get('product_code', '')} {doc.get('product_name', '')} {doc.get('file_name', '')}".lower()

    for t in terms:
        t_lower = t.lower()
        if t_lower in text:
            score += 0.4
        else:
            # 부분 매칭
            for field in ["product_code", "product_name"]:
                val = (doc.get(field) or "").lower()
                if val:
                    sim = SequenceMatcher(None, t_lower, val).ratio()
                    if sim > 0.6:
                        score += sim * 0.3
                        break

    # doc_type 일치 보너스
    if doc.get("doc_type", "").upper() == target_doc_type:
        score += 0.2

    return min(score, 1.0)
