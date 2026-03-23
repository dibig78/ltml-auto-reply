# LT소재 고객 게시판 자동 답변 시스템

ltml.co.kr 고객게시판 문의에 대한 AI 답변 자동 생성 + 관리자 대시보드.

## 시스템 구조

```
[게시판 새 글] → [크롤링] → [문의 분류(6종)] → [파일 검색(TDS)] → [RAG+Claude 답변 생성]
      ↓                                                                    ↓
[관리자 대시보드] ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
      ↓ (검토/수정/승인)
[게시판 답변 게시] + [이메일 파일 첨부 발송]
```

## Quick Start (Claude Code)

```bash
cd ltml-auto-reply
claude

# Step 1: 환경 설정
"setup.sh 실행하고 .env 파일 설정해줘"

# Step 2: 게시판 크롤러
"board_scraper.py의 로그인 페이지를 확인하고 실제 구조에 맞게 수정해줘"

# Step 3: 기술자료실 인덱싱
"tech_library.py로 기술자료실 파일 목록을 크롤링해서 file_index.json을 만들어줘"

# Step 4: 지식 베이스
"data/knowledge_base/에 있는 PDF를 벡터 DB에 임베딩해줘"

# Step 5: 답변 생성 테스트
"게시판에서 답변 대기 글 3건을 읽고 AI 답변 초안을 생성해줘"

# Step 6: 관리자 API
"FastAPI 서버를 실행해줘"

# Step 7: 대시보드
"React 관리자 대시보드를 실행해줘"
```

## 커스텀 명령어

```
/check-board        — 게시판 새 문의 확인
/generate-reply     — 답변 초안 생성
/build-file-index   — 기술자료실 파일 인덱스 재구축
/sync-knowledge     — 지식 베이스 갱신
```
