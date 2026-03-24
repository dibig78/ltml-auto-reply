import { useState, useCallback, createContext, useContext } from 'react'
import InquiriesPage from './pages/InquiriesPage'
import DocumentsPage from './pages/DocumentsPage'
import StatsPage from './pages/StatsPage'
import { api } from './api'

/* ── Toast system ─────────────────────────────────────── */
type ToastType = 'success' | 'error' | 'info'
interface Toast { id: number; message: string; type: ToastType }
interface ToastCtx { push: (message: string, type?: ToastType) => void }

const ToastContext = createContext<ToastCtx>({ push: () => {} })
export const useToast = () => useContext(ToastContext)

let _toastId = 0

function ToastContainer({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => (
        <div
          key={t.id}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium shadow-lg pointer-events-auto animate-slide-up ${
            t.type === 'success' ? 'bg-emerald-600 text-white' :
            t.type === 'error'   ? 'bg-red-600 text-white' :
                                   'bg-gray-800 text-white'
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  )
}

/* ── Tab types ────────────────────────────────────────── */
type Tab = 'inquiries' | 'documents' | 'stats'

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'inquiries', label: '문의 관리', icon: 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' },
  { key: 'documents', label: '문서 검색', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { key: 'stats', label: '통계', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
]

/* ── App ──────────────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState<Tab>('inquiries')
  const [scanning, setScanning] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [refreshKey, setRefreshKey] = useState(0)

  const pushToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++_toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }, [])

  const handleScan = async () => {
    setScanning(true)
    pushToast('게시판 스캔 중...', 'info')
    try {
      const result = await api.scanBoard()
      if (result.scanned > 0) {
        pushToast(`${result.scanned}건의 새 문의를 발견했습니다`, 'success')
        setRefreshKey(k => k + 1)
      } else {
        pushToast('새 문의가 없습니다', 'info')
      }
    } catch {
      pushToast('게시판 스캔 실패', 'error')
    } finally {
      setScanning(false)
    }
  }

  return (
    <ToastContext.Provider value={{ push: pushToast }}>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6">
            <div className="flex items-center justify-between h-14">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center">
                  <span className="text-white text-xs font-bold">LT</span>
                </div>
                <div>
                  <h1 className="text-sm font-bold text-gray-900 leading-none">LT소재</h1>
                  <span className="text-[11px] text-gray-400">고객문의 관리</span>
                </div>
              </div>
              <button
                onClick={handleScan}
                disabled={scanning}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition disabled:opacity-60"
              >
                {scanning ? (
                  <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                )}
                {scanning ? '스캔 중...' : '게시판 스캔'}
              </button>
            </div>

            {/* Tabs */}
            <nav className="flex gap-1 -mb-px">
              {TABS.map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium border-b-2 transition ${
                    tab === t.key
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d={t.icon} />
                  </svg>
                  {t.label}
                </button>
              ))}
            </nav>
          </div>
        </header>

        {/* Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          {tab === 'inquiries' && <InquiriesPage key={refreshKey} />}
          {tab === 'documents' && <DocumentsPage />}
          {tab === 'stats' && <StatsPage />}
        </main>

        <ToastContainer toasts={toasts} />
      </div>
    </ToastContext.Provider>
  )
}
