import { useEffect, useState } from 'react'
import { api } from '../api'
import { useToast } from '../App'
import type { Inquiry } from '../types'

const STATUS_CFG: Record<string, { label: string; color: string; bg: string }> = {
  pending:   { label: '답변 대기',     color: 'text-amber-700',   bg: 'bg-amber-50 border-amber-200' },
  reviewed:  { label: '검토 완료',     color: 'text-blue-700',    bg: 'bg-blue-50 border-blue-200' },
  approved:  { label: '승인됨',       color: 'text-green-700',   bg: 'bg-green-50 border-green-200' },
  sent:      { label: '발송 완료',     color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  escalated: { label: '에스컬레이션',  color: 'text-red-700',     bg: 'bg-red-50 border-red-200' },
}

const CATEGORY_LABELS: Record<string, string> = {
  tds_request: 'TDS/MSDS',
  product_recommend: '제품 추천',
  pricing: '가격/견적',
  technical: '기술 문의',
  delivery: '납기/배송',
  general: '기타',
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CFG[status] || { label: status, color: 'text-gray-700', bg: 'bg-gray-50 border-gray-200' }
  return <span className={`inline-flex px-2 py-0.5 rounded border text-xs font-medium ${cfg.color} ${cfg.bg}`}>{cfg.label}</span>
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 tabular-nums">{pct}%</span>
    </div>
  )
}

/* ── Detail View ──────────────────────────────────────── */
function InquiryDetail({ inquiry, onBack, onUpdate }: {
  inquiry: Inquiry
  onBack: () => void
  onUpdate: (updated: Inquiry) => void
}) {
  const { push } = useToast()
  const [editReply, setEditReply] = useState(inquiry.edited_reply || inquiry.ai_reply || '')
  const [loading, setLoading] = useState('')

  const handleAction = async (action: string, label: string) => {
    setLoading(action)
    try {
      const updated = await api.performAction(inquiry.id, action, editReply || undefined)
      onUpdate(updated)
      push(`${label} 완료`, 'success')
    } catch {
      push(`${label} 실패`, 'error')
    } finally {
      setLoading('')
    }
  }

  const s = STATUS_CFG[inquiry.status] || { label: inquiry.status, color: 'text-gray-700', bg: 'bg-gray-50' }

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600 transition">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        목록으로
      </button>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-gray-900 truncate">{inquiry.title}</h2>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span>{inquiry.author}</span>
              <span className="text-gray-300">|</span>
              <span>{inquiry.email || '이메일 없음'}</span>
              <span className="text-gray-300">|</span>
              <span>{CATEGORY_LABELS[inquiry.category] || inquiry.category}</span>
            </div>
          </div>
          <StatusBadge status={inquiry.status} />
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Meta */}
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">신뢰도</span>
              <ConfidenceBar value={inquiry.confidence} />
            </div>
            {inquiry.email_sent && <span className="text-emerald-600 text-xs font-medium">이메일 발송됨</span>}
            {inquiry.board_posted && <span className="text-blue-600 text-xs font-medium">게시판 등록됨</span>}
          </div>

          {/* Customer content */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">고객 문의</h3>
            <div className="text-sm bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-gray-700 leading-relaxed">
              {inquiry.content}
            </div>
          </div>

          {/* AI reply */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">AI 답변 초안</h3>
            <div className="text-sm bg-blue-50 rounded-lg p-4 whitespace-pre-wrap text-gray-700 leading-relaxed border border-blue-100">
              {inquiry.ai_reply}
            </div>
          </div>

          {/* Matched files */}
          {inquiry.matched_files?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">매칭 파일</h3>
              <div className="space-y-1.5">
                {inquiry.matched_files.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      f.doc_type === 'MSDS' ? 'bg-orange-100 text-orange-700' :
                      f.doc_type === 'ICP'  ? 'bg-purple-100 text-purple-700' :
                                               'bg-blue-100 text-blue-700'
                    }`}>{f.doc_type || 'TDS'}</span>
                    <span className="text-gray-700 font-medium">{f.product_name}</span>
                    <span className="text-gray-400">/</span>
                    <span className="text-gray-500 truncate">{f.file_name}</span>
                    <span className="ml-auto text-[11px] text-gray-400 tabular-nums">score {f.score.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Edit reply */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">답변 수정</h3>
            <textarea
              value={editReply}
              onChange={e => setEditReply(e.target.value)}
              rows={7}
              className="w-full border border-gray-200 rounded-lg p-4 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y leading-relaxed"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center gap-2">
          <button onClick={() => handleAction('save_edit', '수정 저장')} disabled={!!loading}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 disabled:opacity-50 transition font-medium">
            {loading === 'save_edit' ? '저장 중...' : '수정 저장'}
          </button>
          <button onClick={() => handleAction('approve', '승인')} disabled={!!loading}
            className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50 transition font-medium">
            {loading === 'approve' ? '처리 중...' : '승인'}
          </button>
          <button onClick={() => handleAction('send_email', '이메일 발송')} disabled={!!loading || !inquiry.email}
            title={!inquiry.email ? '고객 이메일이 없습니다' : ''}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition font-medium">
            {loading === 'send_email' ? '발송 중...' : '이메일 발송'}
          </button>
          <div className="flex-1" />
          <button onClick={() => handleAction('escalate', '에스컬레이션')} disabled={!!loading}
            className="px-4 py-2 bg-white border border-red-300 text-red-600 text-sm rounded-lg hover:bg-red-50 disabled:opacity-50 transition font-medium">
            에스컬레이션
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── List View ────────────────────────────────────────── */
export default function InquiriesPage() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<Inquiry | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.getInquiries(filter || undefined)
      .then(setInquiries)
      .catch(() => setInquiries([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  if (selected) {
    return (
      <InquiryDetail
        inquiry={selected}
        onBack={() => { setSelected(null); load() }}
        onUpdate={setSelected}
      />
    )
  }

  const filters = [
    { key: '', label: '전체' },
    { key: 'pending', label: '답변 대기' },
    { key: 'reviewed', label: '검토 완료' },
    { key: 'approved', label: '승인됨' },
    { key: 'sent', label: '발송 완료' },
    { key: 'escalated', label: '에스컬레이션' },
  ]

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-2">
        {filters.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition font-medium ${
              filter === f.key
                ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-400">{inquiries.length}건</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">제목</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-20">작성자</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-24">유형</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-24">상태</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-24">신뢰도</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-24">날짜</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-48" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-12" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-16" /></td>
                  <td className="px-4 py-3"><div className="h-5 bg-gray-100 rounded w-16" /></td>
                  <td className="px-4 py-3"><div className="h-3 bg-gray-100 rounded w-14" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-20" /></td>
                </tr>
              ))
            ) : inquiries.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-16 text-center">
                  <div className="text-gray-300 mb-2">
                    <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                  </div>
                  <p className="text-sm text-gray-400">문의가 없습니다</p>
                  <p className="text-xs text-gray-300 mt-1">'게시판 스캔' 버튼으로 새 문의를 가져올 수 있습니다</p>
                </td>
              </tr>
            ) : inquiries.map(inq => (
              <tr
                key={inq.id}
                onClick={() => setSelected(inq)}
                className="hover:bg-blue-50/50 cursor-pointer transition"
              >
                <td className="px-4 py-3">
                  <span className="font-medium text-gray-900 line-clamp-1">{inq.title}</span>
                </td>
                <td className="px-4 py-3 text-gray-500">{inq.author}</td>
                <td className="px-4 py-3">
                  <span className="text-xs text-gray-500">{CATEGORY_LABELS[inq.category] || inq.category}</span>
                </td>
                <td className="px-4 py-3"><StatusBadge status={inq.status} /></td>
                <td className="px-4 py-3"><ConfidenceBar value={inq.confidence} /></td>
                <td className="px-4 py-3 text-xs text-gray-400 tabular-nums">{inq.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
