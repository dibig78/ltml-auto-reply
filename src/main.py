"""메인 파이프라인: 게시판 스캔 → 분류 → 답변 생성."""
import asyncio, json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from src.monitor.board_scraper import check_new_posts
from src.reply.classifier import classify
from src.reply.generator import generate
from src.config import DATA_DIR

console = Console()

async def run():
    console.print("\n[bold blue]🔍 게시판 모니터링...[/]")
    posts = await check_new_posts()
    if not posts:
        console.print("[dim]새 문의 없음[/]"); return
    console.print(f"[bold green]📬 {len(posts)}건 감지[/]")
    results = []
    for p in posts:
        console.print(f"\n처리: #{p['id']} {p['title']}")
        cl = classify(p["title"], p.get("content",""))
        console.print(f"  분류: {cl['category']} ({cl['confidence']:.0%})")
        rp = generate(p["title"], p.get("content",""), cl["category"], p["author"], p.get("email"))
        console.print(f"  신뢰도: {rp['confidence']:.0%} | 파일: {len(rp.get('matched_files',[]))}건")
        results.append({"post":p, "classification":cl, "reply":rp, "ts":datetime.now().isoformat()})
    # 저장
    hist = DATA_DIR / "reply_history.json"
    old = json.loads(hist.read_text()) if hist.exists() else []
    old.extend(results)
    hist.write_text(json.dumps(old, ensure_ascii=False, indent=2))
    # 요약
    t = Table(title="답변 초안")
    t.add_column("#"); t.add_column("제목"); t.add_column("분류"); t.add_column("신뢰도"); t.add_column("파일")
    for r in results:
        t.add_row(str(r["post"]["id"]), r["post"]["title"][:25], r["classification"]["category"],
                   f"{r['reply']['confidence']:.0%}", str(len(r["reply"].get("matched_files",[]))))
    console.print(t)

if __name__ == "__main__":
    asyncio.run(run())
