"""공유 Supabase 클라이언트 — service_role key로 RLS bypass."""
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

_client: Client | None = None


def get_client() -> Client:
    """싱글톤 Supabase 클라이언트 반환."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY 환경변수를 설정하세요")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def query_documents(
    product_code: str | None = None,
    doc_type: str | None = None,
    search_term: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """documents 테이블 검색 — portal DB에서 파일 조회."""
    sb = get_client()
    q = sb.table("documents").select("*").eq("is_active", True)

    if doc_type:
        q = q.eq("doc_type", doc_type.upper())
    if product_code:
        q = q.ilike("product_code", f"%{product_code}%")
    if search_term:
        q = q.or_(
            f"product_code.ilike.%{search_term}%,"
            f"product_name.ilike.%{search_term}%,"
            f"file_name.ilike.%{search_term}%"
        )

    resp = q.limit(limit).execute()
    return resp.data or []


def create_signed_url(file_path: str, expires_in: int = 604800) -> str | None:
    """Supabase Storage signed URL 생성 (기본 7일)."""
    sb = get_client()
    try:
        result = sb.storage.from_("documents").create_signed_url(file_path, expires_in)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as e:
        print(f"[ERROR] signed URL 생성 실패: {e}")
        return None


def insert_inquiry(data: dict) -> dict | None:
    """inquiries 테이블에 새 문의 삽입."""
    sb = get_client()
    resp = sb.table("inquiries").insert(data).execute()
    return resp.data[0] if resp.data else None


def update_inquiry(inquiry_id: int, data: dict) -> dict | None:
    """inquiries 테이블 업데이트."""
    sb = get_client()
    resp = sb.table("inquiries").update(data).eq("id", inquiry_id).execute()
    return resp.data[0] if resp.data else None


def get_inquiries(status: str | None = None, limit: int = 50) -> list[dict]:
    """inquiries 목록 조회."""
    sb = get_client()
    q = sb.table("inquiries").select("*").order("created_at", desc=True).limit(limit)
    if status:
        q = q.eq("status", status)
    resp = q.execute()
    return resp.data or []


def get_inquiry_by_id(inquiry_id: int) -> dict | None:
    """단건 문의 조회."""
    sb = get_client()
    resp = sb.table("inquiries").select("*").eq("id", inquiry_id).maybe_single().execute()
    return resp.data


def get_inquiry_by_board_id(board_id: int) -> dict | None:
    """board_id로 문의 조회."""
    sb = get_client()
    resp = sb.table("inquiries").select("*").eq("board_id", board_id).maybe_single().execute()
    return resp.data


def link_inquiry_document(inquiry_id: int, document_id: str, link_type: str = "auto_matched",
                          signed_url: str | None = None, url_expires_at: str | None = None) -> dict | None:
    """inquiry_document_links junction 테이블에 연결 기록."""
    sb = get_client()
    data = {
        "inquiry_id": inquiry_id,
        "document_id": document_id,
        "link_type": link_type,
    }
    if signed_url:
        data["signed_url"] = signed_url
    if url_expires_at:
        data["url_expires_at"] = url_expires_at
    resp = sb.table("inquiry_document_links").upsert(data, on_conflict="inquiry_id,document_id,link_type").execute()
    return resp.data[0] if resp.data else None


def insert_email_log(data: dict) -> dict | None:
    """email_logs 테이블에 발송 기록."""
    sb = get_client()
    resp = sb.table("email_logs").insert(data).execute()
    return resp.data[0] if resp.data else None


def get_stats() -> dict:
    """대시보드 통계."""
    sb = get_client()
    all_inq = sb.table("inquiries").select("status", count="exact").execute()
    rows = all_inq.data or []
    stats = {"total": len(rows), "pending": 0, "reviewed": 0, "approved": 0, "sent": 0, "escalated": 0}
    for r in rows:
        s = r.get("status", "pending")
        if s in stats:
            stats[s] += 1
    # 문서 수
    docs = sb.table("documents").select("id", count="exact").eq("is_active", True).execute()
    stats["total_documents"] = len(docs.data) if docs.data else 0
    return stats
