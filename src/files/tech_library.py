"""기술자료실 파일 인덱서 — Playwright로 TDS/MSDS 파일 목록 크롤링."""
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright
from src.config import LTML_BASE_URL, DATA_DIR

INDEX_FILE = DATA_DIR / "file_index.json"
CATEGORIES = {"1": "TDS", "2": "MSDS"}

def extract_keywords(name: str, fname: str) -> list[str]:
    kw = set()
    for p in [r"SAC\d{3,4}", r"Sn\d{2}Pb\d{2}", r"LTS-?\d+\w*"]:
        for m in re.findall(p, f"{name} {fname}", re.I):
            kw.add(m.upper())
    for m in re.findall(r"Type\s*(\d+\.?\d*)", f"{name} {fname}", re.I):
        kw.add(f"Type {m}")
    kw.add(name.strip())
    return list(kw)

async def crawl_category(page, cat_id: str) -> list[dict]:
    """기술자료실 카테고리별 파일 목록 크롤링."""
    files_found = []
    url = f"{LTML_BASE_URL}/customer/05/?ct1={cat_id}"
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    rows = await page.query_selector_all("table tbody tr, .board_list tr")
    for row in rows:
        try:
            title_el = await row.query_selector("td:nth-child(2) a, .subject a")
            if not title_el:
                continue
            product = (await title_el.inner_text()).strip()
            detail_url = await title_el.get_attribute("href") or ""
            # 상세 페이지에서 첨부파일 URL 추출
            if detail_url:
                full = detail_url if detail_url.startswith("http") else f"{LTML_BASE_URL}{detail_url}"
                dp = await page.context.new_page()
                await dp.goto(full, wait_until="domcontentloaded")
                await dp.wait_for_timeout(1000)
                links = await dp.query_selector_all("a[href*='.pdf'], a[href*='download'], .file_download a, .attach a")
                file_url, file_name = "", ""
                for lk in links:
                    href = await lk.get_attribute("href") or ""
                    if href and (".pdf" in href.lower() or "download" in href.lower()):
                        file_url = href if href.startswith("http") else f"{LTML_BASE_URL}{href}"
                        file_name = (await lk.inner_text()).strip() or Path(href).name
                        break
                await dp.close()
                files_found.append({
                    "product_name": product, "file_name": file_name or f"{product}.pdf",
                    "download_url": file_url, "detail_url": full,
                    "category": CATEGORIES.get(cat_id, "기타"),
                    "keywords": extract_keywords(product, file_name),
                })
        except Exception as e:
            print(f"  [WARN] {e}")
    return files_found

async def build_index():
    print("📂 기술자료실 인덱스 구축...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        from src.monitor.board_scraper import admin_login
        await admin_login(page)
        index = {}
        for cid, cname in CATEGORIES.items():
            print(f"  [{cname}] 크롤링...")
            index[cname.lower()] = await crawl_category(page, cid)
            print(f"  [{cname}] {len(index[cname.lower()])}건")
        await browser.close()
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    total = sum(len(v) for v in index.values())
    print(f"✅ {total}건 인덱싱 완료 → {INDEX_FILE}")

if __name__ == "__main__":
    asyncio.run(build_index())
