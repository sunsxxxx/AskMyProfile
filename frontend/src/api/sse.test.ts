import { describe, expect, it } from 'vitest'
import { SSEParser } from './sse'

describe('SSEParser', () => {
  it('handles UTF-8 content split across network chunks', () => {
    const parser = new SSEParser()
    expect(parser.push('event: token\ndata: {"content":"你')).toEqual([])
    expect(parser.push('好"}\n\nevent: done\ndata: {}\n\n')).toEqual([
      { event: 'token', data: { content: '你好' } },
      { event: 'done', data: {} },
    ])
  })

  it('handles CRLF and more than one event in a chunk', () => {
    const parser = new SSEParser()
    expect(parser.push('event: status\r\ndata: {"message":"检索"}\r\n\r\nevent: token\r\ndata: {"content":"我"}\r\n\r\n')).toHaveLength(2)
  })
})
