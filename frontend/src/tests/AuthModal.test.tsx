import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthModal } from '../components/auth/AuthModal';
import * as authApi from '../services/authApi';

describe('AuthModal Component', () => {
  it('switches between Sign In and Create Account modes', () => {
    const handleClose = vi.fn();
    const handleSuccess = vi.fn();

    render(
      <AuthModal
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
        initialMode="login"
      />
    );

    expect(screen.getByRole('heading', { name: 'Sign in to NexaAI' })).toBeInTheDocument();

    const tabs = screen.getAllByRole('button', { name: 'Create Account' });
    fireEvent.click(tabs[0]);

    expect(screen.getByRole('heading', { name: 'Create an Account' })).toBeInTheDocument();
  });

  it('validates password minimum length for registration', async () => {
    const { container } = render(
      <AuthModal
        isOpen={true}
        onClose={() => {}}
        onSuccess={() => {}}
        initialMode="register"
      />
    );

    const emailInput = screen.getByPlaceholderText('name@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');
    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement;

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('Password must be at least 8 characters long.')
    ).toBeInTheDocument();
  });

  it('calls login API and onSuccess callback on valid credentials', async () => {
    const mockUser = {
      id: 'uuid-123',
      email: 'user@example.com',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.spyOn(authApi, 'loginUser').mockResolvedValue({ access_token: 'fake-token' });
    vi.spyOn(authApi, 'getCurrentUser').mockResolvedValue(mockUser);

    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    const { container } = render(
      <AuthModal
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
        initialMode="login"
      />
    );

    fireEvent.change(screen.getByPlaceholderText('name@example.com'), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'validPassword123!' },
    });

    const submitBtn = container.querySelector('button[type="submit"]') as HTMLButtonElement;
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(mockUser);
      expect(handleClose).toHaveBeenCalled();
    });
  });
});
