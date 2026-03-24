import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Stats } from '../types'

const CARDS: { key: keyof Stats; label: string; icon: string; color: string; accent: string }[] = [
  { key: 'total',           label: '전체 문의',   icon: 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4', color: 'text-gray-900', accent: 'bg-gray-100' },
  { key: 'pending',         label: '답변 대기',   icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-amber-600', accent: 'bg-amber-50' },
  { key: 'reviewed',        label: '검토 완료',   icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', color: 'text-blue-600', accent: 'bg-blue-50' },
  { key: 'approved',        label: '승인됨',     icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-green-600', accent: 'bg-green-50' },
  { key: 'sent',            label: '발송 완료',   icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z', color: 'text-emerald-600', accent: 'bg-emerald-50' },
  { key: 'escalated',       label: '에스컬레이션', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-red-600', accent: 'bg-red-50' },
  { key: 'total_documents', label: '포털 문서',   icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', color: 'text-purple-600', accent: 'bg-purple-50' },
]

const BARS = [
  { key: 'sent' as const,      label: '발송',    color: 'bg-emerald-500' },
  { key: 'approved' as const,   label: '승인',    color: 'bg-green-400' },
  { key: 'reviewed' as const,   label: '검토',    color: 'bg-blue-400' },
  { key: 'pending' as const,    label: '대기',    color: 'bg-amber-400' },
  { key: 'escalated' as const,  label: '에스컬',  color: 'bg-red-400' },
]

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    api.getStats().then(setStats).catch(console.error)
  }, [])

  if (!stats) {
    return (
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-gray-900">대시보드</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
              <div className="h-3 bg-gray-100 rounded w-16 mb-3" />
              <div className="h-7 bg-gray-100 rounded w-10" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const inquiryTotal = stats.total || 1 // avoid div by 0

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">대시보드</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {CARDS.map(c => (
          <div key={c.key} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 hover:shadow-md transition">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-7 h-7 rounded-lg ${c.accent} flex items-center justify-center`}>
                <svg className={`w-3.5 h-3.5 ${c.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d={c.icon} />
                </svg>
              </div>
              <span className="text-xs text-gray-500">{c.label}</span>
            </div>
            <p className={`text-2xl font-bold tabular-nums ${c.color}`}>{stats[c.key]}</p>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {stats.total > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">처리 현황</h3>
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-100 gap-px">
            {BARS.map(b => {
              const val = stats[b.key]
              if (!val) return null
              return (
                <div
                  key={b.key}
                  className={`${b.color} transition-all duration-500 first:rounded-l-full last:rounded-r-full`}
                  style={{ width: `${(val / inquiryTotal) * 100}%` }}
                  title={`${b.label}: ${val}건`}
                />
              )
            })}
          </div>
          <div className="flex gap-4 mt-3">
            {BARS.map(b => (
              <div key={b.key} className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className={`w-2 h-2 rounded-full ${b.color}`} />
                <span>{b.label}</span>
                <span className="font-medium text-gray-700 tabular-nums">{stats[b.key]}건</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">시스템 현황</h3>
          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">포털 문서 수</span>
              <span className="font-medium text-gray-900">{stats.total_documents}건</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">답변 대기율</span>
              <span className="font-medium text-gray-900">
                {stats.total > 0 ? `${Math.round((stats.pending / stats.total) * 100)}%` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">처리 완료율</span>
              <span className="font-medium text-emerald-600">
                {stats.total > 0 ? `${Math.round(((stats.sent + stats.approved) / stats.total) * 100)}%` : '-'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">빠른 작업</h3>
          <div className="space-y-2">
            <a href="https://www.ltml.co.kr/customer/02/" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              ltml.co.kr 게시판 열기
            </a>
            <a href="https://www.ltml.co.kr/customer/05/?ct1=1" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              기술자료실 (TDS)
            </a>
            <a href="https://www.ltml.co.kr/customer/05/?ct1=2" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              기술자료실 (MSDS)
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
