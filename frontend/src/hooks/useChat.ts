import { useState, useRef, useEffect, useCallback } from 'react';
import { Conversation, Message, ModelOption } from '../types/chat';
import {
  AVAILABLE_MODELS,
  INITIAL_CONVERSATIONS,
  INITIAL_MESSAGES,
  streamMockResponse,
} from '../services/mockChatService';
import {
  checkBackendHealth,
  createBackendConversation,
} from '../services/api';
import { streamBackendMessage } from '../services/streaming';

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    INITIAL_CONVERSATIONS[0]?.id || null
  );
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>(INITIAL_MESSAGES);
  const [selectedModel, setSelectedModel] = useState<ModelOption>(AVAILABLE_MODELS[0]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isBackendOnline, setIsBackendOnline] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Probe backend health on mount
  useEffect(() => {
    let mounted = true;
    checkBackendHealth().then((online) => {
      if (mounted) setIsBackendOnline(online);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const activeMessages = activeConversationId ? messagesMap[activeConversationId] || [] : [];

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const createNewChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
    const newId = `conv-${Date.now()}`;
    const newConv: Conversation = {
      id: newId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastMessagePreview: '',
    };

    setConversations((prev) => [newConv, ...prev]);
    setMessagesMap((prev) => ({ ...prev, [newId]: [] }));
    setActiveConversationId(newId);
  }, []);

  const selectConversation = useCallback((id: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
    setActiveConversationId(id);
  }, []);

  const renameConversation = useCallback((id: string, newTitle: string) => {
    if (!newTitle.trim()) return;
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === id
          ? { ...conv, title: newTitle.trim(), updatedAt: new Date().toISOString() }
          : conv
      )
    );
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((conv) => conv.id !== id));
    setMessagesMap((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
    setActiveConversationId((prev) => {
      if (prev === id) {
        const remaining = conversations.filter((c) => c.id !== id);
        return remaining[0]?.id || null;
      }
      return prev;
    });
  }, [conversations]);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);

      if (activeConversationId) {
        setMessagesMap((prev) => {
          const list = prev[activeConversationId] || [];
          return {
            ...prev,
            [activeConversationId]: list.map((msg) =>
              msg.status === 'streaming' ? { ...msg, status: 'partial' as const } : msg
            ),
          };
        });
      }
    }
  }, [activeConversationId]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      let convId = activeConversationId;
      let isFirstMessage = false;

      // Create conversation if none active
      if (!convId) {
        convId = `conv-${Date.now()}`;
        const newConv: Conversation = {
          id: convId,
          title: trimmed.slice(0, 32) + (trimmed.length > 32 ? '...' : ''),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          lastMessagePreview: trimmed,
        };
        setConversations((prev) => [newConv, ...prev]);
        setMessagesMap((prev) => ({ ...prev, [convId!]: [] }));
        setActiveConversationId(convId);
        isFirstMessage = true;
      }

      // Check if this conversation had 0 messages (update title to first user prompt)
      const currentList = messagesMap[convId] || [];
      if (currentList.length === 0 && !isFirstMessage) {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  title: trimmed.slice(0, 32) + (trimmed.length > 32 ? '...' : ''),
                  lastMessagePreview: trimmed,
                  updatedAt: new Date().toISOString(),
                }
              : c
          )
        );
      }

      const userMessageId = `msg-user-${Date.now()}`;
      const userMessage: Message = {
        id: userMessageId,
        conversationId: convId,
        role: 'user',
        content: trimmed,
        status: 'complete',
        createdAt: new Date().toISOString(),
      };

      const assistantMessageId = `msg-assistant-${Date.now() + 1}`;
      const assistantMessage: Message = {
        id: assistantMessageId,
        conversationId: convId,
        role: 'assistant',
        content: '',
        status: 'streaming',
        modelProvider: selectedModel.provider,
        modelName: selectedModel.name,
        createdAt: new Date().toISOString(),
      };

      // Append user message and empty streaming assistant message
      setMessagesMap((prev) => ({
        ...prev,
        [convId!]: [...(prev[convId!] || []), userMessage, assistantMessage],
      }));

      // Update conversation preview
      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId
            ? { ...c, lastMessagePreview: trimmed, updatedAt: new Date().toISOString() }
            : c
        )
      );

      // Setup streaming
      setIsStreaming(true);
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        let accumulated = '';

        // If backend is online and not using offline mock provider, use live SSE stream!
        if (isBackendOnline && selectedModel.provider !== 'Mock') {
          // If conversation id is local, create a real backend conversation first
          let backendChatId = convId;
          if (convId.startsWith('conv-')) {
            try {
              const remote = await createBackendConversation(trimmed.slice(0, 32));
              backendChatId = remote.id;
            } catch {
              // Fallback to local id
            }
          }

          await streamBackendMessage(
            backendChatId,
            trimmed,
            selectedModel.provider,
            selectedModel.id,
            controller.signal,
            {
              onDelta: (chunk) => {
                accumulated += chunk;
                setMessagesMap((prev) => {
                  const list = prev[convId!] || [];
                  return {
                    ...prev,
                    [convId!]: list.map((msg) =>
                      msg.id === assistantMessageId ? { ...msg, content: accumulated } : msg
                    ),
                  };
                });
              },
              onComplete: (data) => {
                setMessagesMap((prev) => {
                  const list = prev[convId!] || [];
                  return {
                    ...prev,
                    [convId!]: list.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, status: 'complete' as const, content: data.content || accumulated }
                        : msg
                    ),
                  };
                });
              },
              onError: (err) => {
                setMessagesMap((prev) => {
                  const list = prev[convId!] || [];
                  return {
                    ...prev,
                    [convId!]: list.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, status: 'error' as const, error: err.message }
                        : msg
                    ),
                  };
                });
              },
            }
          );
        } else {
          // Fallback to client-side simulated generator
          for await (const chunk of streamMockResponse(trimmed, selectedModel, controller.signal)) {
            if (controller.signal.aborted) break;
            accumulated += chunk;
            setMessagesMap((prev) => {
              const list = prev[convId!] || [];
              return {
                ...prev,
                [convId!]: list.map((msg) =>
                  msg.id === assistantMessageId ? { ...msg, content: accumulated } : msg
                ),
              };
            });
          }

          if (!controller.signal.aborted) {
            setMessagesMap((prev) => {
              const list = prev[convId!] || [];
              return {
                ...prev,
                [convId!]: list.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, status: 'complete' as const, content: accumulated }
                    : msg
                ),
              };
            });
          }
        }
      } catch (err: unknown) {
        if (!controller.signal.aborted) {
          const errorMessage = err instanceof Error ? err.message : 'Unknown streaming error';
          setMessagesMap((prev) => {
            const list = prev[convId!] || [];
            return {
              ...prev,
              [convId!]: list.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, status: 'error' as const, error: errorMessage }
                  : msg
              ),
            };
          });
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, isBackendOnline, isStreaming, messagesMap, selectedModel]
  );

  const regenerateMessage = useCallback(
    async (messageId: string) => {
      if (isStreaming || !activeConversationId) return;

      const currentList = messagesMap[activeConversationId] || [];
      const msgIndex = currentList.findIndex((m) => m.id === messageId);
      if (msgIndex === -1) return;

      let prompt = 'Please regenerate your answer.';
      for (let i = msgIndex - 1; i >= 0; i--) {
        if (currentList[i].role === 'user') {
          prompt = currentList[i].content;
          break;
        }
      }

      setMessagesMap((prev) => {
        const list = prev[activeConversationId!] || [];
        return {
          ...prev,
          [activeConversationId!]: list.map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  content: '',
                  status: 'streaming' as const,
                  error: undefined,
                  modelProvider: selectedModel.provider,
                  modelName: selectedModel.name,
                }
              : m
          ),
        };
      });

      setIsStreaming(true);
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        let accumulated = '';
        for await (const chunk of streamMockResponse(prompt, selectedModel, controller.signal)) {
          if (controller.signal.aborted) break;
          accumulated += chunk;
          setMessagesMap((prev) => {
            const list = prev[activeConversationId!] || [];
            return {
              ...prev,
              [activeConversationId!]: list.map((msg) =>
                msg.id === messageId ? { ...msg, content: accumulated } : msg
              ),
            };
          });
        }

        if (!controller.signal.aborted) {
          setMessagesMap((prev) => {
            const list = prev[activeConversationId!] || [];
            return {
              ...prev,
              [activeConversationId!]: list.map((msg) =>
                msg.id === messageId
                  ? { ...msg, status: 'complete' as const, content: accumulated }
                  : msg
              ),
            };
          });
        }
      } catch (err: unknown) {
        if (!controller.signal.aborted) {
          const errorMessage = err instanceof Error ? err.message : 'Regeneration failed';
          setMessagesMap((prev) => {
            const list = prev[activeConversationId!] || [];
            return {
              ...prev,
              [activeConversationId!]: list.map((msg) =>
                msg.id === messageId
                  ? { ...msg, status: 'error' as const, error: errorMessage }
                  : msg
              ),
            };
          });
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, isStreaming, messagesMap, selectedModel]
  );

  const setFeedback = useCallback(
    (messageId: string, rating: 'up' | 'down') => {
      if (!activeConversationId) return;
      setMessagesMap((prev) => {
        const list = prev[activeConversationId!] || [];
        return {
          ...prev,
          [activeConversationId!]: list.map((m) =>
            m.id === messageId
              ? { ...m, feedback: m.feedback === rating ? null : rating }
              : m
          ),
        };
      });
    },
    [activeConversationId]
  );

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    conversations: filteredConversations,
    allConversationsCount: conversations.length,
    activeConversationId,
    activeMessages,
    selectedModel,
    setSelectedModel,
    isStreaming,
    searchQuery,
    setSearchQuery,
    isBackendOnline,
    createNewChat,
    selectConversation,
    renameConversation,
    deleteConversation,
    sendMessage,
    stopGeneration,
    regenerateMessage,
    setFeedback,
  };
}
