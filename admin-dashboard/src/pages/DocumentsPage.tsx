import { useState } from 'react'
import { api } from '../api'
import type { Document } from '../types'

const DOC_TYPES = ['', 'TDS', 'MSDS', 'ICP']

export default function DocumentsPage() {
  const [query, setQuery] = useState('')
  const [docType, setDocType] = useState('')
  const [results, setResults] = useState<Document[]>([])
  const [searching, setSearching] = useState(false)

  const search = async () => {
    setSearching(true)
    try {
      const docs = await api.searchDocuments(query, docType || undefined)
      setResults(docs)
    } catch (e) {
      console.error(e)
    } finally {
      setSearching(false)
    }
  }

  const download = async (docId: string) => {
    try {
      const { signed_url } = await api.getSignedUrl(docId)
      window.open(signed_url, '_blank')
    } catch (e) {
      alert(`다운로드 실패: ${e}`)
    }
  }

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          placeholder="제품코드 또는 제품명으로 검색 (예: SAC305, LTS-200)"
          className="flex-1 border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <select value={docType} onChange={e => setDocType(e.target.value)}
          className="border rounded-md px-3 py-2 text-sm">
          <option value="">전체 유형</option>
          {DOC_TYPES.filter(Boolean).map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button onClick={search} disabled={searching}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50">
          {searching ? '검색 중...' : '검색'}
        </button>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="px-4 py-3 text-left font-medium">제품코드</th>
              <th className="px-4 py-3 text-left font-medium">제품명</th>
              <th className="px-4 py-3 text-left font-medium">유형</th>
              <th className="px-4 py-3 text-left font-medium">언어</th>
              <th className="px-4 py-3 text-left font-medium">파일명</th>
              <th className="px-4 py-3 text-left font-medium">Revision</th>
              <th className="px-4 py-3 text-left font-medium">액션</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                {searching ? '검색 중...' : '검색어를 입력하세요'}
              </td></tr>
            ) : results.map(doc => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-900">{doc.product_code}</td>
                <td className="px-4 py-3 text-gray-600">{doc.product_name || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    doc.doc_type === 'TDS' ? 'bg-blue-100 text-blue-800' :
                    doc.doc_type === 'MSDS' ? 'bg-orange-100 text-orange-800' :
                    doc.doc_type === 'ICP' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>{doc.doc_type}</span>
                </td>
                <td className="px-4 py-3 text-gray-600">{doc.language.toUpperCase()}</td>
                <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{doc.file_name}</td>
                <td className="px-4 py-3 text-gray-500">{doc.revision || '-'}</td>
                <td className="px-4 py-3">
                  <button onClick={() => download(doc.id)}
                    className="text-blue-600 hover:underline text-xs">
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
