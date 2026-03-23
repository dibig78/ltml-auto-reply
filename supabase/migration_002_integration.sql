-- ════════════════════════════════════════════════════════
-- Migration 002: lt-docs-portal 연계 테이블
-- ltml-auto-reply ↔ lt-docs-portal 통합을 위한 추가 스키마
-- 반드시 001_initial_schema.sql, migration.sql 이후에 실행
-- ════════════════════════════════════════════════════════

-- ── 1. 문의-문서 연결 테이블 (junction) ─────────────────
CREATE TABLE IF NOT EXISTS inquiry_document_links (
    id          SERIAL PRIMARY KEY,
    inquiry_id  INT NOT NULL REFERENCES inquiries(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    link_type   TEXT NOT NULL DEFAULT 'auto_matched'
                CHECK (link_type IN ('auto_matched', 'manual_attached', 'email_sent')),
    signed_url  TEXT,
    url_expires_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(inquiry_id, document_id, link_type)
);

CREATE INDEX IF NOT EXISTS idx_idl_inquiry_id ON inquiry_document_links(inquiry_id);
CREATE INDEX IF NOT EXISTS idx_idl_document_id ON inquiry_document_links(document_id);

-- ── 2. email_logs 확장 ──────────────────────────────────
ALTER TABLE email_logs
    ADD COLUMN IF NOT EXISTS portal_document_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS signed_urls TEXT[] DEFAULT '{}';

-- ── 3. inquiries 확장 ───────────────────────────────────
ALTER TABLE inquiries
    ADD COLUMN IF NOT EXISTS portal_files JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS doc_type TEXT DEFAULT 'TDS';

-- ── 4. RLS (서비스 역할은 bypass, 일반 사용자는 admin만) ─
ALTER TABLE inquiry_document_links ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin can manage inquiry_document_links"
    ON inquiry_document_links FOR ALL
    TO authenticated
    USING (
        EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- service_role key는 RLS를 bypass하므로 Python 백엔드에서 자유롭게 접근 가능
