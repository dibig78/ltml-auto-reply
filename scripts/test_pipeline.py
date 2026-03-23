"""E2E 파이프라인 테스트 — 각 모듈을 단계별로 검증."""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from rich.console import Console
from rich.table import Table

console = Console()


def test_config():
    """환경 변수 로드 확인."""
    from src.config import (
        LTML_BASE_URL, ANTHROPIC_API_KEY, SUPABASE_URL,
        SUPABASE_SERVICE_KEY, SMTP_USER,
    )
    checks = {
        "LTML_BASE_URL": bool(LTML_BASE_URL),
        "ANTHROPIC_API_KEY": bool(ANTHROPIC_API_KEY),
        "SUPABASE_URL": bool(SUPABASE_URL),
        "SUPABASE_SERVICE_KEY": bool(SUPABASE_SERVICE_KEY),
        "SMTP_USER": bool(SMTP_USER),
    }
    return checks


def test_supabase_connection():
    """Supabase 연결 테스트."""
    try:
        from src.db.supabase_client import get_client
        sb = get_client()
        # 간단한 쿼리
        resp = sb.table("inquiries").select("id").limit(1).execute()
        return {"connected": True, "sample_count": len(resp.data)}
    except Exception as e:
        return {"connected": False, "error": str(e)}


def test_portal_documents():
    """포털 documents 테이블 검색 테스트."""
    try:
        from src.db.supabase_client import query_documents
        docs = query_documents(limit=5)
        return {"found": len(docs), "sample": docs[0]["product_code"] if docs else "없음"}
    except Exception as e:
        return {"found": 0, "error": str(e)}


def test_classifier():
    """문의 분류기 테스트."""
    try:
        from src.reply.classifier import classify
        result = classify("SAC305 TDS 요청", "SAC305 크림솔더의 TDS 자료를 보내주실 수 있나요?")
        return result
    except Exception as e:
        return {"error": str(e)}


def test_file_searcher():
    """파일 검색 테스트 (포털 + legacy 폴백)."""
    try:
        from src.files.file_searcher import find_files
        result = find_files("SAC305 TDS 요청", "SAC305 크림솔더의 TDS를 요청합니다.")
        return {
            "found": result.get("found"),
            "source": result.get("source", "unknown"),
            "file_count": len(result.get("files", [])),
        }
    except Exception as e:
        return {"error": str(e)}


def test_generator():
    """답변 생성 테스트."""
    try:
        from src.reply.generator import generate
        result = generate(
            title="SAC305 TDS 요청",
            content="SAC305 크림솔더의 TDS 자료를 보내주세요.",
            category="tds_request",
            author="테스트",
            email="test@example.com",
        )
        return {
            "reply_length": len(result.get("reply_text", "")),
            "confidence": result.get("confidence"),
            "needs_review": result.get("needs_review"),
            "file_source": result.get("file_source"),
            "matched_files": len(result.get("matched_files", [])),
        }
    except Exception as e:
        return {"error": str(e)}


def test_api_server():
    """FastAPI 서버 응답 테스트."""
    try:
        import httpx
        r = httpx.get("http://localhost:8000/api/stats", timeout=5)
        return {"status": r.status_code, "data": r.json()}
    except Exception as e:
        return {"error": str(e)}


def main():
    console.print("\n[bold blue]== LT소재 자동 답변 시스템 E2E 테스트 ==[/bold blue]\n")

    tests = [
        ("1. 환경 변수", test_config),
        ("2. Supabase 연결", test_supabase_connection),
        ("3. 포털 문서 검색", test_portal_documents),
        ("4. 문의 분류기", test_classifier),
        ("5. 파일 검색 (포털 연계)", test_file_searcher),
        ("6. 답변 생성", test_generator),
        ("7. API 서버", test_api_server),
    ]

    table = Table(title="테스트 결과")
    table.add_column("단계", style="cyan")
    table.add_column("결과", style="green")

    for name, fn in tests:
        console.print(f"\n[yellow]>> {name}[/yellow]")
        try:
            result = fn()
            result_str = json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result)
            console.print(result_str)
            has_error = isinstance(result, dict) and "error" in result
            table.add_row(name, "[red]FAIL[/red]" if has_error else "[green]PASS[/green]")
        except Exception as e:
            console.print(f"[red]ERROR: {e}[/red]")
            table.add_row(name, "[red]ERROR[/red]")

    console.print("\n")
    console.print(table)


if __name__ == "__main__":
    main()
