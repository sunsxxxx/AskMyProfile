import type { SSEEvent } from '../types/chat'

export class SSEParser {
  private buffer = ''

  push(chunk: string): SSEEvent[] {
    this.buffer += chunk.replaceAll('\r\n', '\n')
    const frames = this.buffer.split('\n\n')
    this.buffer = frames.pop() ?? ''
    return frames.flatMap((frame) => this.parseFrame(frame))
  }

  finish(): SSEEvent[] {
    const frame = this.buffer
    this.buffer = ''
    return frame.trim() ? this.parseFrame(frame) : []
  }

  private parseFrame(frame: string): SSEEvent[] {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of frame.split('\n')) {
      if (!line || line.startsWith(':')) continue
      const separator = line.indexOf(':')
      const field = separator === -1 ? line : line.slice(0, separator)
      let value = separator === -1 ? '' : line.slice(separator + 1)
      if (value.startsWith(' ')) value = value.slice(1)
      if (field === 'event') event = value
      if (field === 'data') dataLines.push(value)
    }
    if (!dataLines.length) return []
    const raw = dataLines.join('\n')
    try {
      return [{ event, data: raw ? JSON.parse(raw) : null }]
    } catch {
      return [{ event, data: raw }]
    }
  }
}

