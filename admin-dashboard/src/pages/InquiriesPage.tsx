import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Inquiry } from '../types'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending:   { label: '답변 대기', color: 'bg-yellow-100 text-yellow-800' },
  reviewed:  { label: '검토 완료', color: 'bg-blue-100 text-blue-800' },
  approved:  { label: '승인됨',   color: 'bg-green-100 text-green-800' },
  sent:      { label: '발송 완료', color: 'bg-emerald-100 text-emerald-800' },
  escalated: { label: '에스컬레이션', color: 'bg-red-100 text-red-800' },
}

const CATEGORY_LABELS: Record<string, string> = {
  tds_request: 'TDS/MSDS 요청',
  product_recommend: '제품 추천',
  pricing: '가격/견적',
  technical: '기술 문의',
  delivery: '납기/배송',
  general: '기타',
}

export default function InquiriesPage() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [filter, setFilter] = useState<string>('')
  const [selected, setSelected] = useState<Inquiry | null>(null)
  const [editReply, setEditReply] = useState('')
  const [loading, setLoading] = useState(false)

  const load = () => {
    api.getInquiries(filter || undefined).then(setInquiries).catch(console.error)
  }

  useEffect(() => { load() }, [filter])

  const handleAction = async (action: string) => {
    if (!selected) return
    setLoading(true)
    try {
      const updated = await api.performAction(selected.id, action, editReply || undefined)
      setSelected(updated)
      load()
    } catch (e) {
      alert(`오류: ${e}`)
    } finally {
      setLoading(false)
    }
  }

  if (selected) {
    const s = STATUS_LABELS[selected.status] || { label: selected.status, color: 'bg-gray-100 text-gray-800' }
    return (
      <div className="space-y-4">
        <button onClick={() => setSelected(null)} className="text-sm text-blue-600 hover:underline">
          &larr; 목록으로
        </button>

        <div className="bg-white rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{selected.title}</h2>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.color}`}>{s.label}</span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
            <div>작성자: <span className="text-gray-900">{selected.author}</span></div>
            <div>이메일: <span className="text-gray-900">{selected.email || '없음'}</span></div>
            <div>유형: <span className="text-gray-900">{CATEGORY_LABELS[selected.category] || selected.category}</span></div>
            <div>신뢰도: <span className="text-gray-900">{(selected.confidence * 100).toFixed(0)}%</span></div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-1">고객 문의 내용</h3>
            <p className="text-sm bg-gray-50 rounded p-3 whitespace-pre-wrap">{selected.content}</p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-1">AI 답변 초안</h3>
            <p className="text-sm bg-blue-50 rounded p-3 whitespace-pre-wrap">{selected.ai_reply}</p>
          </div>

          {selected.matched_files?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-1">매칭 파일</h3>
              <ul className="text-sm space-y-1">
                {selected.matched_files.map((f, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{f.doc_type || 'TDS'}</span>
                    <span>{f.product_name} / {f.file_name}</span>
                    <span className="text-gray-400 text-xs">score: {f.score.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-1">답변 수정</h3>
            <textarea
              value={editReply}
              onChange={e => setEditReply(e.target.value)}
              placeholder={selected.edited_reply || selected.ai_reply}
              rows={6}
              className="w-full border rounded-md p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button onClick={() => handleAction('save_edit')} disabled={loading}
              className="px-3 py-1.5 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50">
              수정 저장
            </button>
            <button onClick={() => handleAction('approve')} disabled={loading}
              className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50">
              승인
            </button>
            <button onClick={() => handleAction('send_email')} disabled={loading || !selected.email}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50">
              이메일 발송
            </button>
            <button onClick={() => handleAction('escalate')} disabled={loading}
              className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50">
              에스컬레이션
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex gap-2">
        {['', 'pending', 'reviewed', 'approved', 'sent', 'escalated'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1 text-sm rounded-full border transition ${
              filter === s ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}>
            {s ? (STATUS_LABELS[s]?.label || s) : '전체'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="px-4 py-3 text-left font-medium">제목</th>
              <th className="px-4 py-3 text-left font-medium">작성자</th>
              <th className="px-4 py-3 text-left font-medium">유형</th>
              <th className="px-4 py-3 text-left font-medium">상태</th>
              <th className="px-4 py-3 text-left font-medium">신뢰도</th>
              <th className="px-4 py-3 text-left font-medium">날짜</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {inquiries.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">문의가 없습니다</td></tr>
            ) : inquiries.map(inq => {
              const s = STATUS_LABELS[inq.status] || { label: inq.status, color: 'bg-gray-100 text-gray-800' }
              return (
                <tr key={inq.id} onClick={() => { setSelected(inq); setEditReply(inq.edited_reply || '') }}
                  className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{inq.title}</td>
                  <td className="px-4 py-3 text-gray-600">{inq.author}</td>
                  <td className="px-4 py-3 text-gray-600">{CATEGORY_LABELS[inq.category] || inq.category}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.color}`}>{s.label}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{(inq.confidence * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-gray-500">{inq.date}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
