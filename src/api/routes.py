"""API 라우트 — 문의 목록, 답변 생성, 승인, 발송."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter()

# TODO: Supabase 연동 시 DB 쿼리로 교체. 현재는 in-memory 데모.
inquiries_db = []

class InquiryCreate(BaseModel):
    board_id: int
    title: str
    author: str
    email: Optional[str] = None
    content: str

class ReplyAction(BaseModel):
    action: str  # approve, send_email, post_board, escalate, save_edit
    edited_reply: Optional[str] = None

@router.get("/inquiries")
def list_inquiries(status: str = None):
    if status:
        return [i for i in inquiries_db if i.get("status") == status]
    return inquiries_db

@router.get("/inquiries/{board_id}")
def get_inquiry(board_id: int):
    for i in inquiries_db:
        if i["board_id"] == board_id:
            return i
    raise HTTPException(404, "문의를 찾을 수 없습니다")

@router.post("/inquiries/scan")
async def scan_new():
    """게시판 스캔 → 분류 → 답변 생성."""
    from src.monitor.board_scraper import check_new_posts
    from src.reply.classifier import classify
    from src.reply.generator import generate
    posts = await check_new_posts()
    results = []
    for p in posts:
        cl = classify(p["title"], p.get("content",""))
        rp = generate(p["title"], p.get("content",""), cl["category"], p["author"], p.get("email"))
        entry = {
            "board_id": p["id"], "title": p["title"], "author": p["author"],
            "email": p.get("email"), "content": p.get("content",""), "date": p["date"],
            "category": cl["category"], "confidence": rp["confidence"],
            "ai_reply": rp["reply_text"], "edited_reply": None,
            "matched_files": rp.get("matched_files",[]),
            "needs_review": rp.get("needs_review", True),
            "status": "pending", "email_sent": False, "board_posted": False,
        }
        inquiries_db.append(entry)
        results.append(entry)
    return {"scanned": len(results), "inquiries": results}

@router.post("/inquiries/{board_id}/action")
def perform_action(board_id: int, body: ReplyAction):
    for i in inquiries_db:
        if i["board_id"] == board_id:
            if body.action == "approve":
                i["status"] = "approved"
                if body.edited_reply: i["edited_reply"] = body.edited_reply
            elif body.action == "send_email":
                # TODO: email_sender 호출
                i["email_sent"] = True; i["board_posted"] = True; i["status"] = "sent"
            elif body.action == "post_board":
                # TODO: Playwright 자동 게시 호출
                i["board_posted"] = True; i["status"] = "sent"
            elif body.action == "escalate":
                i["status"] = "escalated"
            elif body.action == "save_edit":
                i["edited_reply"] = body.edited_reply; i["status"] = "reviewed"
            return i
    raise HTTPException(404, "문의를 찾을 수 없습니다")

@router.get("/stats")
def get_stats():
    return {
        "total": len(inquiries_db),
        "pending": sum(1 for i in inquiries_db if i["status"]=="pending"),
        "reviewed": sum(1 for i in inquiries_db if i["status"]=="reviewed"),
        "sent": sum(1 for i in inquiries_db if i["status"]=="sent"),
        "escalated": sum(1 for i in inquiries_db if i["status"]=="escalated"),
    }
