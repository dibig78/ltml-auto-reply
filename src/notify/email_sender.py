"""SMTP 이메일 발송 — TDS/MSDS 파일 첨부."""
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from pathlib import Path
from src.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, DATA_DIR

def send_tds_email(to_email: str, to_name: str, product: str, doc_type: str, file_paths: list[Path]) -> bool:
    if not SMTP_PASS:
        print("[ERROR] SMTP_PASS 미설정")
        return False
    msg = MIMEMultipart()
    msg["From"] = formataddr(("LT소재 영업팀", SMTP_USER))
    msg["To"] = to_email
    msg["Subject"] = f"[LT소재] 요청하신 {product} {doc_type} 자료 안내"
    file_list = "\n".join(f"  - {fp.name}" for fp in file_paths)
    body = f"""{to_name}님, 안녕하세요.\nLT소재 주식회사입니다.\n\n요청하신 {product}의 {doc_type} 자료를 첨부합니다.\n\n■ 첨부 자료\n{file_list}\n\n추가 문의: 031-330-1000 / dwkim@ltml.co.kr\n\n감사합니다.\nLT소재 영업팀"""
    msg.attach(MIMEText(body, "plain", "utf-8"))
    for fp in file_paths:
        if fp.exists():
            att = MIMEApplication(fp.read_bytes(), _subtype="pdf")
            att.add_header("Content-Disposition", "attachment", filename=fp.name)
            msg.attach(att)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] 발송 실패: {e}")
        return False
