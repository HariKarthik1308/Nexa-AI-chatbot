import { describe, it, expect, vi } from 'vitest';
import { streamBackendMessage } from '../services/streaming';

describe('SSE Frontend Streaming Consumer', () => {
  it('parses SSE chunks and triggers callbacks', async () => {
    const ssePayload = [
      'event: message_start\ndata: {"messageId": "msg-1", "model": "gemini-1.5-flash", "provider": "Gemini"}\n\n',
      'event: content_delta\ndata: {"delta": "Hello "}\n\n',
      'event: content_delta\ndata: {"delta": "world!"}\n\n',
      'event: message_complete\ndata: {"messageId": "msg-1", "status": "complete", "content": "Hello world!"}\n\n',
    ].join('');

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: stream,
    });

    const deltas: string[] = [];
    const controller = new AbortController();

    let startedId = '';
    let completedContent = '';

    await streamBackendMessage(
      'chat-123',
      'Hello',
      'gemini',
      'gemini-1.5-flash',
      controller.signal,
      {
        onStart: (data) => {
          startedId = data.messageId;
        },
        onDelta: (chunk) => {
          deltas.push(chunk);
        },
        onComplete: (data) => {
          completedContent = data.content;
        },
      }
    );

    expect(startedId).toBe('msg-1');
    expect(deltas).toEqual(['Hello ', 'world!']);
    expect(completedContent).toBe('Hello world!');
  });

  it('triggers onError callback when error event is received', async () => {
    const ssePayload =
      'event: error\ndata: {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded"}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: stream,
    });

    const controller = new AbortController();
    let errorCode = '';
    let errorMessage = '';

    await streamBackendMessage(
      'chat-123',
      'Hello',
      'gemini',
      'gemini-1.5-flash',
      controller.signal,
      {
        onDelta: () => {},
        onError: (err) => {
          errorCode = err.code;
          errorMessage = err.message;
        },
      }
    );

    expect(errorCode).toBe('RATE_LIMIT_EXCEEDED');
    expect(errorMessage).toBe('Rate limit exceeded');
  });
});
