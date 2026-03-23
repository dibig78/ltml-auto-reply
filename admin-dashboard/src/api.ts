import type { Inquiry, Document, Stats } from './types'

const BASE = '/api'

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  getInquiries: (status?: string) =>
    fetchJSON<Inquiry[]>(`/inquiries${status ? `?status=${status}` : ''}`),

  getInquiry: (id: number) =>
    fetchJSON<Inquiry>(`/inquiries/${id}`),

  performAction: (id: number, action: string, editedReply?: string) =>
    fetchJSON<Inquiry>(`/inquiries/${id}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, edited_reply: editedReply }),
    }),

  scanBoard: () =>
    fetchJSON<{ scanned: number; inquiries: Inquiry[] }>('/inquiries/scan', { method: 'POST' }),

  searchDocuments: (q: string, docType?: string) =>
    fetchJSON<Document[]>(`/documents/search?q=${encodeURIComponent(q)}${docType ? `&doc_type=${docType}` : ''}`),

  getSignedUrl: (docId: string) =>
    fetchJSON<{ signed_url: string }>(`/documents/${docId}/signed-url`),

  getStats: () => fetchJSON<Stats>('/stats'),
}
