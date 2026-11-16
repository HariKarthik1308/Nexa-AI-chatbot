import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

describe('NexaAI Phase 1 UI Foundation', () => {
  it('renders branding and Phase 1 mock mode indicators', () => {
    render(<App />);
    expect(screen.getAllByText('NexaAI').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Phase 1 Mock Mode/i).length).toBeGreaterThan(0);
  });

  it('renders initial conversations in the sidebar', () => {
    render(<App />);
    expect(screen.getByText('Project Architecture & Tech Stack')).toBeInTheDocument();
    expect(screen.getByText('Security & Auth Blueprint')).toBeInTheDocument();
  });

  it('clicking New Chat switches to the welcome screen', async () => {
    render(<App />);
    const newChatBtn = screen.getByRole('button', { name: /new chat/i });
    fireEvent.click(newChatBtn);

    expect(screen.getByText('Try an example prompt (Phase 1 Mock Simulation)')).toBeInTheDocument();
    expect(screen.getByText('Real-Time Streaming Architecture')).toBeInTheDocument();
  });

  it('allows user to send a prompt and shows user message and streaming state', async () => {
    render(<App />);

    // Start a new chat
    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));

    const textarea = screen.getByLabelText('Chat input message');
    fireEvent.change(textarea, { target: { value: 'How is NexaAI structured?' } });

    const sendBtn = screen.getByLabelText('Send message');
    fireEvent.click(sendBtn);

    // User message should appear in chat
    expect(screen.getAllByText('How is NexaAI structured?').length).toBeGreaterThan(0);

    // Stop button should be visible during streaming
    await waitFor(() => {
      expect(screen.getByLabelText('Stop generation')).toBeInTheDocument();
    });

    // Clicking stop generation stops generation cleanly
    const stopBtn = screen.getByLabelText('Stop generation');
    fireEvent.click(stopBtn);

    // After stopping, stop button is replaced by send button
    await waitFor(() => {
      expect(screen.getByLabelText('Send message')).toBeInTheDocument();
    });
  });

  it('supports theme toggle', () => {
    render(<App />);
    const themeBtn = screen.getByLabelText('Toggle theme');
    fireEvent.click(themeBtn);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('allows filtering conversations with search', () => {
    render(<App />);
    const searchInput = screen.getByPlaceholderText('Search conversations...');
    fireEvent.change(searchInput, { target: { value: 'Security' } });

    expect(screen.getByText('Security & Auth Blueprint')).toBeInTheDocument();
    expect(screen.queryByText('Project Architecture & Tech Stack')).not.toBeInTheDocument();
  });
});
