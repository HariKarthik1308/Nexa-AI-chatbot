export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch('/api/v1/health', { method: 'GET' });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export async function createBackendConversation(title: string = 'New Conversation') {
  const res = await fetch('/api/v1/chats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to create conversation');
  return res.json();
}

export async function listBackendConversations() {
  const res = await fetch('/api/v1/chats');
  if (!res.ok) throw new Error('Failed to list conversations');
  return res.json();
}

export async function getBackendConversation(chatId: string) {
  const res = await fetch(`/api/v1/chats/${chatId}`);
  if (!res.ok) throw new Error('Failed to get conversation');
  return res.json();
}

export async function renameBackendConversation(chatId: string, title: string) {
  const res = await fetch(`/api/v1/chats/${chatId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to rename conversation');
  return res.json();
}

export async function deleteBackendConversation(chatId: string) {
  const res = await fetch(`/api/v1/chats/${chatId}`, {
    method: 'DELETE',
  });
  return res.ok;
}
