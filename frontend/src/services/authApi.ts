import { AuthUser } from '../types/auth';

export async function registerUser(email: string, password: string): Promise<AuthUser> {
  const res = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed');
  }

  return res.json();
}

export async function loginUser(email: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Invalid email or password');
  }

  return res.json();
}

export async function logoutUser(): Promise<void> {
  await fetch('/api/v1/auth/logout', { method: 'POST' });
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  try {
    const res = await fetch('/api/v1/auth/me', { method: 'GET' });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
