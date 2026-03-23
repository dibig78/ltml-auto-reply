"""게시판 크롤링 — 새 글 감지 + 비밀글 내용 읽기."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from src.config import LTML_BASE_URL, LTML_BOARD_URL, LTML_ADMIN_ID, LTML_ADMIN_PW, DATA_DIR

SEEN_FILE = DATA_DIR / "seen_posts.json"

def load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(seen: set):
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(list(seen)))

async def admin_login(page):
    """관리자 로그인. TODO: 실제 로그인 URL/폼 구조에 맞게 수정."""
    # Claude Code에서 실제 구조 확인 후 아래를 수정하세요:
    # 1) Playwright로 ltml.co.kr 방문 → 로그인 링크 찾기
    # 2) 로그인 폼의 input name 확인
    # 3) 아래 코드를 실제 값으로 교체
    login_url = f"{LTML_BASE_URL}/bbs/login.php"  # 추정값
    await page.goto(login_url, wait_until="domcontentloaded")
    await page.fill("input[name=mb_id]", LTML_ADMIN_ID)
    await page.fill("input[name=mb_password]", LTML_ADMIN_PW)
    await page.click("button[type=submit], input[type=submit]")
    await page.wait_for_load_state("domcontentloaded")

async def scrape_pending_posts(page) -> list[dict]:
    """'답변 대기' 게시물 목록 추출."""
    await page.goto(LTML_BOARD_URL, wait_until="domcontentloaded")
    posts = []
    rows = await page.query_selector_all("table tbody tr")
    for row in rows:
        status_el = await row.query_selector("td:last-child")
        if not status_el:
            continue
        status = (await status_el.inner_text()).strip()
        if "답변 대기" not in status:
            continue
        num_el = await row.query_selector("td:first-child")
        if not num_el:
            continue
        num_text = (await num_el.inner_text()).strip()
        if not num_text.isdigit():
            continue
        link_el = await row.query_selector("td:nth-child(2) a")
        title = (await link_el.inner_text()).strip() if link_el else ""
        url = (await link_el.get_attribute("href") or "") if link_el else ""
        author_el = await row.query_selector("td:nth-child(3)")
        date_el = await row.query_selector("td:nth-child(4)")
        posts.append({
            "id": int(num_text),
            "title": title,
            "author": (await author_el.inner_text()).strip() if author_el else "",
            "date": (await date_el.inner_text()).strip() if date_el else "",
            "url": url,
        })
    return posts

async def read_post_content(page, post_url: str) -> dict:
    """게시물 상세에서 본문 + 이메일 추출."""
    full_url = post_url if post_url.startswith("http") else f"{LTML_BASE_URL}{post_url}"
    await page.goto(full_url, wait_until="domcontentloaded")
    content_el = await page.query_selector(".board_view_content, .view_content, .content, .bo_content")
    content = (await content_el.inner_text()).strip() if content_el else ""
    # 이메일 추출 시도
    import re
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", content)
    return {"content": content, "email": emails[0] if emails else None}

async def check_new_posts() -> list[dict]:
    """새 답변 대기 게시물 확인 + 내용 읽기."""
    seen = load_seen()
    new_posts = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await admin_login(page)
        posts = await scrape_pending_posts(page)
        for post in posts:
            if post["id"] in seen:
                continue
            if post["url"]:
                detail = await read_post_content(page, post["url"])
                post.update(detail)
            else:
                post["content"] = ""
                post["email"] = None
            new_posts.append(post)
            seen.add(post["id"])
        await browser.close()
    save_seen(seen)
    return new_posts

if __name__ == "__main__":
    for p in asyncio.run(check_new_posts()):
        print(f"[{p['id']}] {p['title']} — {p.get('email','')}")
