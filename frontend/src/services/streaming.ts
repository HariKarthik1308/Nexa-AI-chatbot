export interface StreamCallbacks {
  onStart?: (data: { messageId: string; model: string; provider: string }) => void;
  onDelta: (delta: string) => void;
  onComplete?: (data: { messageId: string; content: string }) => void;
  onError?: (error: { code: string; message: string }) => void;
}

export async function streamBackendMessage(
  chatId: string,
  content: string,
  provider: string,
  model: string,
  signal: AbortSignal,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch(`/api/v1/chats/${chatId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content,
      provider: provider.toLowerCase(),
      model,
    }),
    signal,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Server responded with ${response.status}`);
  }

  if (!response.body) {
    throw new Error('ReadableStream not supported by browser environment.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      if (signal.aborted) {
        await reader.cancel();
        break;
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        const lines = part.split('\n');
        let event = '';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            event = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            dataStr = line.replace('data:', '').trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          if (event === 'message_start' && callbacks.onStart) {
            callbacks.onStart(parsed);
          } else if (event === 'content_delta') {
            callbacks.onDelta(parsed.delta);
          } else if (event === 'message_complete' && callbacks.onComplete) {
            callbacks.onComplete(parsed);
          } else if (event === 'error' && callbacks.onError) {
            callbacks.onError(parsed);
          }
        } catch {
          // Ignore malformed partial chunks
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
