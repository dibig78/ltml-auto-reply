export interface Inquiry {
  id: number
  board_id: number
  title: string
  author: string
  email?: string
  content: string
  date: string
  category: string
  status: string
  confidence: number
  ai_reply: string
  edited_reply?: string
  matched_files: FileMatch[]
  portal_files: FileMatch[]
  needs_review: boolean
  email_sent: boolean
  board_posted: boolean
}

export interface FileMatch {
  product_name: string
  file_name: string
  download_url: string
  portal_url?: string
  document_id?: string
  doc_type?: string
  score: number
}

export interface Document {
  id: string
  product_code: string
  product_name?: string
  doc_type: string
  language: string
  revision?: string
  file_name: string
  file_path: string
  is_active: boolean
  uploaded_at: string
}

export interface Stats {
  total: number
  pending: number
  reviewed: number
  approved: number
  sent: number
  escalated: number
  total_documents: number
}
