import { SSEParser } from './sse'
import type { SSEEvent } from '../types/chat'

interface StreamChatOptions {
  message: string
  threadId: string
  signal: AbortSignal
  onEvent: (event: SSEEvent) => void
}

export class ChatApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly retryAfter?: number,
  ) {
    super(message)
  }
}

export async function streamChat(options: StreamChatOptions): Promise<void> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ message: options.message, thread_id: options.threadId }),
    signal: options.signal,
  })

  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    let retryAfter: number | undefined
    try {
      const body = (await response.json()) as {
        message?: string
        retry_after?: number
        detail?: string | { message?: string }
      }
      message = body.message ?? (typeof body.detail === 'string' ? body.detail : body.detail?.message) ?? message
      retryAfter = body.retry_after
    } catch {
      // Keep the status-based fallback when an upstream proxy returns non-JSON.
    }
    throw new ChatApiError(message, response.status, retryAfter)
  }
  if (!response.body) throw new ChatApiError('浏览器未收到流式响应', response.status)

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  const parser = new SSEParser()
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    for (const event of parser.push(decoder.decode(value, { stream: true }))) {
      options.onEvent(event)
    }
  }
  for (const event of parser.push(decoder.decode())) options.onEvent(event)
  for (const event of parser.finish()) options.onEvent(event)
}

