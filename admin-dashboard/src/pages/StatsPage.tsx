import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Stats } from '../types'

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    api.getStats().then(setStats).catch(console.error)
  }, [])

  if (!stats) return <div className="text-center text-gray-400 py-8">로딩 중...</div>

  const cards = [
    { label: '전체 문의', value: stats.total, color: 'bg-gray-900' },
    { label: '답변 대기', value: stats.pending, color: 'bg-yellow-500' },
    { label: '검토 완료', value: stats.reviewed, color: 'bg-blue-500' },
    { label: '승인됨', value: stats.approved, color: 'bg-green-500' },
    { label: '발송 완료', value: stats.sent, color: 'bg-emerald-500' },
    { label: '에스컬레이션', value: stats.escalated, color: 'bg-red-500' },
    { label: '포털 문서 수', value: stats.total_documents, color: 'bg-purple-500' },
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">대시보드 통계</h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {cards.map(c => (
          <div key={c.label} className="bg-white rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-2 h-2 rounded-full ${c.color}`} />
              <span className="text-xs text-gray-500">{c.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{c.value}</p>
          </div>
        ))}
      </div>

      {stats.total > 0 && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4">처리 현황</h3>
          <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
            {stats.sent > 0 && (
              <div className="bg-emerald-500" style={{ width: `${(stats.sent / stats.total) * 100}%` }}
                title={`발송 완료: ${stats.sent}`} />
            )}
            {stats.approved > 0 && (
              <div className="bg-green-500" style={{ width: `${(stats.approved / stats.total) * 100}%` }}
                title={`승인됨: ${stats.approved}`} />
            )}
            {stats.reviewed > 0 && (
              <div className="bg-blue-500" style={{ width: `${(stats.reviewed / stats.total) * 100}%` }}
                title={`검토 완료: ${stats.reviewed}`} />
            )}
            {stats.pending > 0 && (
              <div className="bg-yellow-500" style={{ width: `${(stats.pending / stats.total) * 100}%` }}
                title={`답변 대기: ${stats.pending}`} />
            )}
            {stats.escalated > 0 && (
              <div className="bg-red-500" style={{ width: `${(stats.escalated / stats.total) * 100}%` }}
                title={`에스컬레이션: ${stats.escalated}`} />
            )}
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> 발송</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> 승인</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" /> 검토</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" /> 대기</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> 에스컬</span>
          </div>
        </div>
      )}
    </div>
  )
}
