"""게시판 크롤링 — 새 글 감지 + 비밀글 내용 읽기."""
import asyncio, json, re
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


async def scrape_board_page(page, page_num: int = 1) -> list[dict]:
    """게시판 페이지에서 글 목록 추출.

    사이트 구조:
    - URL: /customer/02/ (1페이지), /customer/02/p-{n}/ (n페이지)
    - 테이블: 번호 | 제목 | 등록인 | 등록일 | 처리상태
    - 글 링크: /customer/02/v/{id}
    """
    url = LTML_BOARD_URL if page_num <= 1 else f"{LTML_BASE_URL}/customer/02/p-{page_num}/"
    await page.goto(url, wait_until="domcontentloaded", timeout=15000)

    posts = []
    body_text = await page.inner_text("body")
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]

    # 글 링크에서 ID 추출
    links = await page.query_selector_all("a[href*='/customer/02/v/']")
    for link in links:
        href = await link.get_attribute("href") or ""
        title = (await link.inner_text()).strip()

        # ID 추출: /customer/02/v/{id}
        match = re.search(r"/customer/02/v/(\d+)", href)
        if not match:
            continue
        post_id = int(match.group(1))

        # 부모 행에서 추가 정보 추출
        parent = await link.evaluate_handle("el => el.closest('tr') || el.closest('li') || el.parentElement?.parentElement")
        row_text = (await parent.inner_text()).strip() if parent else ""

        # 처리상태 확인
        status = ""
        if "답변 대기" in row_text:
            status = "답변 대기"
        elif "답변 완료" in row_text:
            status = "답변 완료"

        # 등록인, 등록일 추출 (행 텍스트에서 파싱)
        parts = [p.strip() for p in row_text.split("\t") if p.strip()]
        author = ""
        date = ""
        if len(parts) >= 4:
            # 번호 | 제목 | 등록인 | 등록일 | 처리상태
            author = parts[2] if len(parts) > 2 else ""
            date = parts[3] if len(parts) > 3 else ""

        posts.append({
            "id": post_id,
            "title": title,
            "author": author,
            "date": date,
            "status": status,
            "url": href,
        })

    return posts


async def read_post_content(page, post_url: str, admin_pw: str = "") -> dict:
    """게시물 상세에서 본문 + 이메일 추출. 비밀글이면 비밀번호 입력."""
    full_url = post_url if post_url.startswith("http") else f"{LTML_BASE_URL}{post_url}"
    await page.goto(full_url, wait_until="domcontentloaded", timeout=15000)

    # 비밀글 비밀번호 폼 확인
    pass_input = await page.query_selector("input[name='pass']")
    if pass_input and admin_pw:
        await pass_input.fill(admin_pw)
        submit = await page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            await submit.click()
            await page.wait_for_load_state("domcontentloaded", timeout=10000)

    # 본문 추출 — ltml.co.kr 실제 셀렉터 순서
    content = ""
    for sel in [".board_con", ".board_view .txt_box", ".board_view_content", ".view_content", ".bo_content"]:
        el = await page.query_selector(sel)
        if el:
            content = (await el.inner_text()).strip()
            if content:
                break

    # 본문이 비어있으면 .board_view에서 메타 제거 후 추출
    if not content:
        view_el = await page.query_selector(".board_view")
        if view_el:
            full = (await view_el.inner_text()).strip()
            # 제목/등록인/등록일/조회수/처리상태 행 이후가 본문
            lines = full.split("\n")
            start = 0
            for i, line in enumerate(lines):
                if "처리상태" in line or "조회수" in line:
                    start = i + 1
                    break
            content = "\n".join(lines[start:]).strip()

    # 이메일 추출
    full_text = await page.inner_text("body")
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", full_text)
    # 사이트 자체 이메일 제외
    customer_emails = [e for e in emails if "ltml.co.kr" not in e and "almit" not in e.lower()]

    return {
        "content": content,
        "email": customer_emails[0] if customer_emails else None,
    }


async def check_new_posts(max_pages: int = 3) -> list[dict]:
    """새 '답변 대기' 게시물 확인 + 내용 읽기."""
    seen = load_seen()
    new_posts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        # 페이지별 스캔
        for page_num in range(1, max_pages + 1):
            posts = await scrape_board_page(page, page_num)
            pending = [p for p in posts if p["status"] == "답변 대기"]

            if not pending:
                break  # 답변 대기가 없으면 이전 페이지이므로 중단

            for post in pending:
                if post["id"] in seen:
                    continue
                if post["url"]:
                    detail = await read_post_content(page, post["url"], LTML_ADMIN_PW)
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
    results = asyncio.run(check_new_posts())
    print(f"\n총 {len(results)}건의 새 답변 대기 문의")
    for p in results:
        print(f"  [{p['id']}] {p['title']} — {p.get('author','')} — email: {p.get('email','없음')}")
        if p.get("content"):
            print(f"    내용: {p['content'][:100]}...")
