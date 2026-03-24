import { useState } from 'react'
import { api } from '../api'
import { useToast } from '../App'
import type { Document } from '../types'

const DOC_TYPE_COLORS: Record<string, string> = {
  TDS:  'bg-blue-50 text-blue-700 border-blue-200',
  MSDS: 'bg-orange-50 text-orange-700 border-orange-200',
  ICP:  'bg-purple-50 text-purple-700 border-purple-200',
}

export default function DocumentsPage() {
  const { push } = useToast()
  const [query, setQuery] = useState('')
  const [docType, setDocType] = useState('')
  const [results, setResults] = useState<Document[]>([])
  const [searched, setSearched] = useState(false)
  const [searching, setSearching] = useState(false)

  const search = async () => {
    if (!query && !docType) return
    setSearching(true)
    setSearched(true)
    try {
      const docs = await api.searchDocuments(query, docType || undefined)
      setResults(docs)
      if (docs.length === 0) push('검색 결과가 없습니다', 'info')
    } catch {
      push('문서 검색 실패', 'error')
    } finally {
      setSearching(false)
    }
  }

  const download = async (docId: string, fileName: string) => {
    try {
      const { signed_url } = await api.getSignedUrl(docId)
      window.open(signed_url, '_blank')
      push(`${fileName} 다운로드 시작`, 'success')
    } catch {
      push('다운로드 링크 생성 실패', 'error')
    }
  }

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
              placeholder="제품코드 또는 제품명 (예: SAC305, RS60, LFM-48W)"
              className="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <select
            value={docType}
            onChange={e => setDocType(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-white"
          >
            <option value="">전체 유형</option>
            <option value="TDS">TDS</option>
            <option value="MSDS">MSDS</option>
            <option value="ICP">ICP</option>
          </select>
          <button
            onClick={search}
            disabled={searching}
            className="px-5 py-2.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-60 transition font-medium"
          >
            {searching ? '검색 중...' : '검색'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {searched && results.length > 0 && (
          <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50/50">
            <span className="text-xs text-gray-500">{results.length}건의 문서</span>
          </div>
        )}
        <table className="w-full text-sm table-fixed">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-28">제품코드</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-16">유형</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide w-16">언어</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">파일명</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wide w-20"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {searching ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-20" /></td>
                  <td className="px-4 py-3"><div className="h-5 bg-gray-100 rounded w-12" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-8" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-40" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-14" /></td>
                </tr>
              ))
            ) : results.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-16 text-center">
                  <div className="text-gray-300 mb-2">
                    <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-sm text-gray-400">{searched ? '검색 결과가 없습니다' : '제품코드 또는 제품명으로 검색하세요'}</p>
                  <p className="text-xs text-gray-300 mt-1">포털에 등록된 TDS, MSDS, ICP 문서를 검색할 수 있습니다</p>
                </td>
              </tr>
            ) : results.map(doc => (
              <tr key={doc.id} className="hover:bg-gray-50/50 transition">
                <td className="px-4 py-3">
                  <span className="font-mono font-medium text-gray-900">{doc.product_code}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded border text-[10px] font-bold ${DOC_TYPE_COLORS[doc.doc_type] || 'bg-gray-50 text-gray-700 border-gray-200'}`}>
                    {doc.doc_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${doc.language === 'ko' ? 'text-gray-600' : 'text-gray-400'}`}>
                    {doc.language === 'ko' ? '한국어' : doc.language === 'en' ? 'English' : doc.language.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600 truncate">{doc.file_name}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => download(doc.id, doc.file_name)}
                    className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium transition"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    다운로드
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
