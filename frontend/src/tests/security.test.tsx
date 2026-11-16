import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '../components/chat/MessageBubble';
import { Message } from '../types/chat';

describe('Frontend Security & XSS Sanitization', () => {
  it('safely escapes raw script tags in assistant messages without creating script elements', () => {
    const maliciousMessage: Message = {
      id: 'msg-xss',
      conversationId: 'conv-xss',
      role: 'assistant',
      content: 'Here is some text: <script>window.__xss_executed = true;</script>',
      status: 'complete',
      createdAt: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={maliciousMessage} />);

    // Ensure no <script> element was injected into the DOM
    const scriptElements = container.querySelectorAll('script');
    expect(scriptElements.length).toBe(0);

    // Ensure window global was not altered
    expect((window as unknown as { __xss_executed?: boolean }).__xss_executed).toBeUndefined();

    // Verify the text content is rendered safely as escaped text
    expect(screen.getByText(/Here is some text:/)).toBeInTheDocument();
  });

  it('safely handles img onerror injection attempts', () => {
    const maliciousImgMessage: Message = {
      id: 'msg-xss-img',
      conversationId: 'conv-xss',
      role: 'assistant',
      content: 'Image test: <img src="invalid-url" onerror="window.__xss_img = true;" />',
      status: 'complete',
      createdAt: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={maliciousImgMessage} />);
    const imgElements = container.querySelectorAll('img[onerror]');
    expect(imgElements.length).toBe(0);
    expect((window as unknown as { __xss_img?: boolean }).__xss_img).toBeUndefined();
  });
});
