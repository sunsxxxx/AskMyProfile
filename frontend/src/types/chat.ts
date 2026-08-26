export type ChatRole = 'user' | 'assistant'

export interface SourceItem {
  title: string
  source: string
  section: string
  category: string
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  intermediate?: string
  sources?: SourceItem[]
  error?: boolean
}

export interface SSEEvent {
  event: string
  data: unknown
}
