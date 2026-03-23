import { useState } from 'react'
import InquiriesPage from './pages/InquiriesPage'
import DocumentsPage from './pages/DocumentsPage'
import StatsPage from './pages/StatsPage'

type Tab = 'inquiries' | 'documents' | 'stats'

const TABS: { key: Tab; label: string }[] = [
  { key: 'inquiries', label: '문의 관리' },
  { key: 'documents', label: '문서 검색' },
  { key: 'stats', label: '통계' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('inquiries')

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-gray-900">LT소재</h1>
              <span className="text-sm text-gray-500">고객문의 관리 시스템</span>
            </div>
            <button
              onClick={() => fetch('/api/inquiries/scan', { method: 'POST' }).then(() => window.location.reload())}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition"
            >
              게시판 스캔
            </button>
          </div>
          <nav className="flex gap-6 -mb-px">
            {TABS.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`py-3 text-sm font-medium border-b-2 transition ${
                  tab === t.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {tab === 'inquiries' && <InquiriesPage />}
        {tab === 'documents' && <DocumentsPage />}
        {tab === 'stats' && <StatsPage />}
      </main>
    </div>
  )
}
