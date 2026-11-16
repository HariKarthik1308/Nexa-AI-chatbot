export interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type AuthMode = 'login' | 'register';
