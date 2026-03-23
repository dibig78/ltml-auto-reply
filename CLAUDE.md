# LT소재 고객 게시판 자동 답변 시스템

## 프로젝트 목적
ltml.co.kr 고객게시판(/customer/02/) 문의에 대한 AI 답변 자동 생성 + 관리자 대시보드 시스템.
- 1단계(반자동): AI 답변 초안 → 관리자 대시보드에서 검토/수정 → 게시판 게시 + 이메일 발송
- 2단계(자동): 정형 문의(TDS 요청 등) 자동 게시, 비정형은 사람 검토 유지

## 회사 정보
- 회사명: LT소재 주식회사 (ltml.co.kr)
- 주소: 경기도 용인시 처인구 남사읍 당하로 113-19
- TEL: 031-330-1000 / 영업 이메일: dwkim@ltml.co.kr
- 기술 파트너: 일본 Nihon Almit
- 제품: 솔더 페이스트(크림솔더), 솔더 와이어/바, 플럭스, OLED, Fuel Cell, Silicone Pad, Side Seal, Thermal Resin, AMB ceramic substrates
- 주요 솔더 합금: SAC305, SAC405, SAC0307(무연) / Sn63Pb37(유연)
- Type 분류: Type 3(25~45μm), Type 4(20~38μm), Type 4.5, Type 5(15~25μm)

## 게시판 구조
- URL: https://www.ltml.co.kr/customer/02/
- 글 상세: /customer/02/v/{id} | 페이지: /customer/02/p-{page}/
- 기술자료실: /customer/05/?ct1=1(TDS), ?ct1=2(MSDS)
- 총 1,743건+, 대부분 비밀글, 처리상태: "답변 대기" / "답변 완료"
- 관리자: ID=admin, PW=환경변수 LTML_ADMIN_PW 참조

## 문의 유형 6종
1. tds_request — TDS/MSDS/CoA/SDS 요청 → 파일 검색+첨부+이메일 발송
2. product_recommend — 공정 조건 기반 제품 추천
3. pricing — 가격/견적/샘플 → 무조건 영업 담당자 연결
4. technical — 기술 문의 (인쇄성, 보이드, 웨팅 등)
5. delivery — 납기/배송/재고
6. general — 기타

## 답변 절대 규칙
1. 공식 비즈니스 한국어, 존칭 필수
2. "LT소재" 또는 "당사"로 지칭
3. **가격 정보 절대 불포함** → 영업 담당자 연결
4. 기술 수치는 반드시 TDS 출처 명시
5. 불확실하면 담당자 연락처(031-330-1000, dwkim@ltml.co.kr) 안내
6. 답변 말미에 연락처 포함, 200~500자
7. 클레임/불만 → AI 답변 금지, 에스컬레이션

## 기술 스택
- Backend: Python 3.11+, FastAPI (관리자 API)
- Frontend: React + Tailwind (관리자 대시보드)
- DB: Supabase (PostgreSQL)
- Scraping: Playwright
- AI: Claude API (claude-sonnet-4-6), LangChain + ChromaDB (RAG)
- Email: SMTP (dwkim@ltml.co.kr)
- 배포: VPS 또는 Supabase Edge Functions

## 환경 변수 (.env)
```
LTML_ADMIN_ID=admin
LTML_ADMIN_PW=ltml1234%
LTML_BASE_URL=https://www.ltml.co.kr
ANTHROPIC_API_KEY=sk-ant-xxxxx
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=dwkim@ltml.co.kr
SMTP_PASS=앱비밀번호
CHROMA_PERSIST_DIR=./data/chroma_db
```

## 디렉토리 구조
```
src/
├── monitor/board_scraper.py     — 게시판 크롤링 + 새 글 감지
├── files/tech_library.py        — 기술자료실 파일 인덱싱
├── files/file_searcher.py       — 문의→파일 매칭 검색
├── knowledge/ingest_tds.py      — TDS/MSDS 벡터 임베딩
├── knowledge/retriever.py       — RAG 검색
├── reply/classifier.py          — 문의 유형 분류 (6종)
├── reply/generator.py           — RAG + Claude API 답변 생성
├── reply/prompts/               — 카테고리별 시스템 프롬프트 6개
├── notify/email_sender.py       — SMTP 파일 첨부 발송
├── api/main.py                  — FastAPI 관리자 API
└── api/routes.py                — API 라우트
admin-dashboard/                 — React 관리자 대시보드
scripts/                         — cron, setup 스크립트
```

## 개발 우선순위
1. board_scraper.py (게시판 크롤링)
2. tech_library.py (기술자료실 파일 인덱싱)
3. file_searcher.py (파일 검색)
4. classifier.py + generator.py (답변 생성)
5. email_sender.py (이메일 발송)
6. FastAPI 관리자 API
7. React 관리자 대시보드
8. Supabase 테이블 + RLS
9. cron 스케줄링
10. Playwright 자동 게시 (2단계)
