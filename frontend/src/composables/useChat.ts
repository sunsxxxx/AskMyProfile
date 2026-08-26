import { computed, nextTick, reactive, ref } from 'vue'
import { ChatApiError, streamChat } from '../api/chat'
import type { ChatMessage, SourceItem, SSEEvent } from '../types/chat'

const THREAD_KEY = 'interview-ai-thread-id'

function threadId(): string {
  const stored = localStorage.getItem(THREAD_KEY)
  if (stored) {
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(stored)) return stored
  }
  const created = crypto.randomUUID()
  localStorage.setItem(THREAD_KEY, created)
  return created
}

export function useChat(onUpdated?: () => void) {
  const messages = ref<ChatMessage[]>([])
  const input = ref('')
  const status = ref('')
  const isStreaming = ref(false)
  const currentThreadId = ref(threadId())
  let controller: AbortController | null = null

  const canSend = computed(() => input.value.trim().length > 0 && !isStreaming.value)

  function notifyUpdate() {
    void nextTick(() => onUpdated?.())
  }

  async function send(preset?: string) {
    const content = (preset ?? input.value).trim()
    if (!content || isStreaming.value) return
    input.value = ''
    messages.value.push({ id: crypto.randomUUID(), role: 'user', content })
    // Keep the same reactive proxy that Vue renders. Mutating the raw object
    // after pushing it into a ref-backed array does not trigger updates, which
    // makes all streamed chunks appear only when another state change renders.
    const assistant = reactive<ChatMessage>({ id: crypto.randomUUID(), role: 'assistant', content: '' })
    messages.value.push(assistant)
    isStreaming.value = true
    status.value = '正在连接...'
    controller = new AbortController()
    notifyUpdate()

    const handleEvent = (event: SSEEvent) => {
      const data = event.data as Record<string, unknown> | SourceItem[] | null
      if (event.event === 'status' && data && !Array.isArray(data)) {
        status.value = String(data.message ?? '')
      } else if (event.event === 'intermediate' && data && !Array.isArray(data)) {
        const trace = String(data.content ?? '').trim()
        if (trace) assistant.intermediate = [assistant.intermediate, trace].filter(Boolean).join('\n\n')
      } else if (event.event === 'token' && data && !Array.isArray(data)) {
        assistant.content += String(data.content ?? '')
        status.value = ''
      } else if (event.event === 'sources' && Array.isArray(data)) {
        assistant.sources = data as SourceItem[]
      } else if (event.event === 'error' && data && !Array.isArray(data)) {
        throw new ChatApiError(String(data.message ?? '回答生成失败'), 500)
      }
      notifyUpdate()
    }

    try {
      await streamChat({
        message: content,
        threadId: currentThreadId.value,
        signal: controller.signal,
        onEvent: handleEvent,
      })
      if (!assistant.content) assistant.content = '现有资料暂时无法生成回答，请稍后再试。'
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        assistant.content ||= '已停止生成。'
      } else {
        assistant.error = true
        if (error instanceof ChatApiError && error.status === 429) {
          assistant.content = `${error.message}${error.retryAfter ? `（约 ${error.retryAfter} 秒后可重试）` : ''}`
        } else {
          assistant.content = error instanceof Error ? error.message : '网络异常，请稍后重试。'
        }
      }
    } finally {
      isStreaming.value = false
      status.value = ''
      controller = null
      notifyUpdate()
    }
  }

  function stop() {
    controller?.abort()
  }

  function newConversation() {
    controller?.abort()
    const created = crypto.randomUUID()
    localStorage.setItem(THREAD_KEY, created)
    currentThreadId.value = created
    messages.value = []
    input.value = ''
    status.value = ''
  }

  return { messages, input, status, isStreaming, canSend, send, stop, newConversation }
}
