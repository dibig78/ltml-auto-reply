"""API 라우트 — Supabase 실DB 연동."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from src.db.supabase_client import (
    get_inquiries, get_inquiry_by_board_id, get_inquiry_by_id,
    insert_inquiry, update_inquiry, insert_email_log,
    link_inquiry_document, get_stats, query_documents, create_signed_url,
)

router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class ReplyAction(BaseModel):
    action: str  # approve, send_email, post_board, escalate, save_edit
    edited_reply: Optional[str] = None


# ── 문의 관련 엔드포인트 ─────────────────────────────────

@router.get("/inquiries")
def list_inquiries(status: Optional[str] = None, limit: int = 50):
    """문의 목록 조회 (status 필터 가능)."""
    return get_inquiries(status=status, limit=limit)


@router.get("/inquiries/{inquiry_id}")
def get_inquiry(inquiry_id: int):
    """단건 문의 조회."""
    row = get_inquiry_by_id(inquiry_id)
    if not row:
        raise HTTPException(404, "문의를 찾을 수 없습니다")
    return row


@router.post("/inquiries/scan")
async def scan_new():
    """게시판 스캔 → 분류 → 답변 생성 → DB 저장."""
    from src.monitor.board_scraper import check_new_posts
    from src.reply.classifier import classify
    from src.reply.generator import generate

    posts = await check_new_posts()
    results = []

    for p in posts:
        # 중복 체크
        existing = get_inquiry_by_board_id(p["id"])
        if existing:
            continue

        cl = classify(p["title"], p.get("content", ""))
        rp = generate(p["title"], p.get("content", ""), cl["category"], p["author"], p.get("email"))

        entry = {
            "board_id": p["id"],
            "title": p["title"],
            "author": p["author"],
            "email": p.get("email"),
            "content": p.get("content", ""),
            "date": p["date"],
            "category": cl["category"],
            "confidence": rp["confidence"],
            "ai_reply": rp["reply_text"],
            "matched_files": rp.get("matched_files", []),
            "portal_files": [f for f in rp.get("matched_files", []) if f.get("document_id")],
            "needs_review": rp.get("needs_review", True),
            "status": "pending",
        }

        saved = insert_inquiry(entry)
        if saved:
            # 포털 문서 연결 기록
            for f in entry.get("portal_files", []):
                if f.get("document_id"):
                    link_inquiry_document(
                        inquiry_id=saved["id"],
                        document_id=f["document_id"],
                        link_type="auto_matched",
                        signed_url=f.get("download_url"),
                    )
            results.append(saved)

    return {"scanned": len(results), "inquiries": results}


@router.post("/inquiries/{inquiry_id}/action")
def perform_action(inquiry_id: int, body: ReplyAction):
    """문의에 대한 관리자 액션 수행."""
    row = get_inquiry_by_id(inquiry_id)
    if not row:
        raise HTTPException(404, "문의를 찾을 수 없습니다")

    update_data = {}

    if body.action == "approve":
        update_data["status"] = "approved"
        if body.edited_reply:
            update_data["edited_reply"] = body.edited_reply

    elif body.action == "send_email":
        if not row.get("email"):
            raise HTTPException(400, "고객 이메일이 없습니다")

        from src.notify.email_sender import send_tds_email
        portal_files = row.get("portal_files", [])

        success = send_tds_email(
            to_email=row["email"],
            to_name=row.get("author", "고객"),
            product=row.get("title", ""),
            doc_type=row.get("doc_type", "TDS"),
            portal_files=portal_files if portal_files else None,
        )

        update_data["email_sent"] = success
        update_data["status"] = "sent" if success else "approved"

        insert_email_log({
            "inquiry_id": inquiry_id,
            "to_email": row["email"],
            "to_name": row.get("author"),
            "success": success,
            "portal_document_ids": [f["document_id"] for f in portal_files if f.get("document_id")],
        })

    elif body.action == "post_board":
        import asyncio
        from src.publish.board_writer import post_reply
        reply_text = body.edited_reply or row.get("edited_reply") or row.get("ai_reply", "")
        success = asyncio.run(post_reply(row["board_id"], reply_text))
        update_data["board_posted"] = success
        update_data["status"] = "sent" if success else "approved"

    elif body.action == "escalate":
        update_data["status"] = "escalated"
        update_data["assignee"] = "dwkim@ltml.co.kr"

    elif body.action == "save_edit":
        update_data["edited_reply"] = body.edited_reply
        update_data["status"] = "reviewed"

    else:
        raise HTTPException(400, f"알 수 없는 액션: {body.action}")

    updated = update_inquiry(inquiry_id, update_data)
    return updated or row


# ── 문서 검색 엔드포인트 ─────────────────────────────────

@router.get("/documents/search")
def search_documents(
    q: str = Query(default="", description="검색어 (제품코드, 제품명)"),
    doc_type: Optional[str] = Query(default=None, description="문서 유형: TDS, MSDS, ICP"),
    limit: int = Query(default=20, le=100),
):
    """포털 documents 테이블 검색."""
    if not q and not doc_type:
        return query_documents(limit=limit)
    return query_documents(search_term=q if q else None, doc_type=doc_type, limit=limit)


@router.get("/documents/{document_id}/signed-url")
def get_document_signed_url(document_id: str, expires_in: int = Query(default=604800, le=604800)):
    """문서의 signed URL 생성."""
    from src.db.supabase_client import get_client
    sb = get_client()
    resp = sb.table("documents").select("file_path, file_name").eq("id", document_id).maybe_single().execute()
    if not resp.data:
        raise HTTPException(404, "문서를 찾을 수 없습니다")

    url = create_signed_url(resp.data["file_path"], expires_in)
    if not url:
        raise HTTPException(500, "signed URL 생성 실패")

    return {"document_id": document_id, "file_name": resp.data["file_name"], "signed_url": url, "expires_in": expires_in}


# ── 통계 엔드포인트 ──────────────────────────────────────

@router.get("/stats")
def dashboard_stats():
    """대시보드 통합 통계."""
    return get_stats()
