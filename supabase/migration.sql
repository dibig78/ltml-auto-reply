-- 고객 문의 테이블
CREATE TABLE IF NOT EXISTS inquiries (
    id SERIAL PRIMARY KEY,
    board_id INT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT,
    email TEXT,
    content TEXT,
    date TEXT,
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'pending',  -- pending/reviewed/approved/sent/escalated
    ai_reply TEXT,
    edited_reply TEXT,
    confidence FLOAT DEFAULT 0,
    matched_files JSONB DEFAULT '[]'::jsonb,
    needs_review BOOLEAN DEFAULT TRUE,
    email_sent BOOLEAN DEFAULT FALSE,
    board_posted BOOLEAN DEFAULT FALSE,
    assignee TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 파일 인덱스 테이블
CREATE TABLE IF NOT EXISTS file_index (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    file_name TEXT,
    download_url TEXT,
    detail_url TEXT,
    category TEXT,  -- TDS, MSDS, CoA
    keywords TEXT[],
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 이메일 발송 로그
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    inquiry_id INT REFERENCES inquiries(id),
    to_email TEXT NOT NULL,
    to_name TEXT,
    files_sent TEXT[],
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT FALSE
);

-- RLS 정책 (필요 시)
-- ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;
