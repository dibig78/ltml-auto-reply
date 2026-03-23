"""SMTP 이메일 발송 — 로컬 파일 첨부 또는 Supabase Storage 파일 첨부."""
import smtplib
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from pathlib import Path
from src.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


def send_tds_email(
    to_email: str,
    to_name: str,
    product: str,
    doc_type: str,
    file_paths: list[Path] | None = None,
    portal_files: list[dict] | None = None,
) -> bool:
    """TDS/MSDS/ICP 파일 첨부 이메일 발송.

    Args:
        file_paths: 로컬 파일 경로 (legacy)
        portal_files: 포털 문서 정보 [{"file_name", "file_path", "signed_url", "document_id"}]
            - file_path가 있으면 Storage에서 다운로드 후 첨부
            - signed_url만 있으면 본문에 링크 포함
    """
    if not SMTP_PASS:
        print("[ERROR] SMTP_PASS 미설정")
        return False

    msg = MIMEMultipart()
    msg["From"] = formataddr(("LT소재 영업팀", SMTP_USER))
    msg["To"] = to_email
    msg["Subject"] = f"[LT소재] 요청하신 {product} {doc_type} 자료 안내"

    attached_names = []
    download_links = []

    # 1) 포털 파일 처리 (Supabase Storage)
    if portal_files:
        for pf in portal_files:
            file_data = _download_from_storage(pf.get("file_path", ""))
            if file_data:
                fname = pf.get("file_name", "document.pdf")
                att = MIMEApplication(file_data, _subtype="pdf")
                att.add_header("Content-Disposition", "attachment", filename=fname)
                msg.attach(att)
                attached_names.append(fname)
            elif pf.get("signed_url"):
                download_links.append((pf.get("file_name", "문서"), pf["signed_url"]))

    # 2) 로컬 파일 처리 (legacy)
    if file_paths:
        for fp in file_paths:
            if fp.exists():
                att = MIMEApplication(fp.read_bytes(), _subtype="pdf")
                att.add_header("Content-Disposition", "attachment", filename=fp.name)
                msg.attach(att)
                attached_names.append(fp.name)

    # 본문 구성
    body_parts = [f"{to_name}님, 안녕하세요.", "LT소재 주식회사입니다.", "",
                  f"요청하신 {product}의 {doc_type} 자료를 안내드립니다."]

    if attached_names:
        body_parts.append("")
        body_parts.append("■ 첨부 자료")
        for name in attached_names:
            body_parts.append(f"  - {name}")

    if download_links:
        body_parts.append("")
        body_parts.append("■ 다운로드 링크 (7일간 유효)")
        for name, url in download_links:
            body_parts.append(f"  - {name}: {url}")

    body_parts.extend(["", "추가 문의: 031-330-1000 / dwkim@ltml.co.kr", "", "감사합니다.", "LT소재 영업팀"])

    msg.attach(MIMEText("\n".join(body_parts), "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] 발송 실패: {e}")
        return False


def _download_from_storage(file_path: str) -> bytes | None:
    """Supabase Storage에서 파일 다운로드."""
    if not file_path:
        return None
    try:
        from src.db.supabase_client import get_client
        sb = get_client()
        data = sb.storage.from_("documents").download(file_path)
        return data
    except Exception as e:
        print(f"[WARN] Storage 다운로드 실패 ({file_path}): {e}")
        return None
