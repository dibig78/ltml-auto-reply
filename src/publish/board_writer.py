"""Playwright로 게시판 답변 자동 게시."""
from playwright.async_api import async_playwright
from src.config import LTML_BASE_URL, LTML_ADMIN_ID, LTML_ADMIN_PW


async def post_reply(board_id: int, reply_text: str) -> bool:
    """게시판 글에 관리자 답변 게시.

    Args:
        board_id: 게시글 ID
        reply_text: 답변 내용

    Returns:
        성공 여부
    """
    if not LTML_ADMIN_ID or not LTML_ADMIN_PW:
        print("[ERROR] 관리자 계정 미설정")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # 1) 관리자 로그인
            await page.goto(f"{LTML_BASE_URL}/member/login/")
            await page.fill('input[name="mb_id"]', LTML_ADMIN_ID)
            await page.fill('input[name="mb_password"]', LTML_ADMIN_PW)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")

            # 2) 글 상세 페이지 이동
            detail_url = f"{LTML_BASE_URL}/customer/02/v/{board_id}"
            await page.goto(detail_url)
            await page.wait_for_load_state("networkidle")

            # 3) 답변 작성 폼 찾기
            # 사이트 구조에 따라 셀렉터 조정 필요
            reply_selectors = [
                'textarea[name="comment"]',
                'textarea[name="wr_content"]',
                '#wr_content',
                'textarea.reply-content',
            ]

            textarea = None
            for sel in reply_selectors:
                try:
                    textarea = await page.wait_for_selector(sel, timeout=3000)
                    if textarea:
                        break
                except:
                    continue

            if not textarea:
                print(f"[ERROR] 답변 입력 폼을 찾을 수 없습니다 (board_id={board_id})")
                return False

            # 4) 답변 입력 및 제출
            await textarea.fill(reply_text)

            submit_selectors = [
                'button[type="submit"]:has-text("등록")',
                'input[type="submit"][value*="등록"]',
                'button:has-text("답변")',
                '#btn_submit',
            ]

            submitted = False
            for sel in submit_selectors:
                try:
                    btn = await page.wait_for_selector(sel, timeout=2000)
                    if btn:
                        await btn.click()
                        submitted = True
                        break
                except:
                    continue

            if not submitted:
                print(f"[ERROR] 제출 버튼을 찾을 수 없습니다 (board_id={board_id})")
                return False

            await page.wait_for_load_state("networkidle")
            print(f"[OK] 답변 게시 완료 (board_id={board_id})")
            return True

        except Exception as e:
            print(f"[ERROR] 답변 게시 실패: {e}")
            return False
        finally:
            await browser.close()
