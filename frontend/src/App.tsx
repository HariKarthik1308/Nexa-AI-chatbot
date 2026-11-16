import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ChatArea } from './components/chat/ChatArea';
import { useChat } from './hooks/useChat';
import { useTheme } from './hooks/useTheme';

export const App: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    conversations,
    activeMessages,
    selectedModel,
    setSelectedModel,
    isStreaming,
    searchQuery,
    setSearchQuery,
    createNewChat,
    selectConversation,
    renameConversation,
    deleteConversation,
    sendMessage,
    stopGeneration,
    regenerateMessage,
    setFeedback,
    activeConversationId,
  } = useChat();

  // Keyboard shortcut: Ctrl+N or Cmd+N for new chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        createNewChat();
      } else if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [createNewChat, sidebarOpen]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans antialiased">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={selectConversation}
        onNewChat={createNewChat}
        onRename={renameConversation}
        onDelete={deleteConversation}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        <Header
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          theme={theme}
          onToggleTheme={toggleTheme}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <ChatArea
          messages={activeMessages}
          isStreaming={isStreaming}
          onSendMessage={sendMessage}
          onStopGeneration={stopGeneration}
          onRegenerate={regenerateMessage}
          onFeedback={setFeedback}
        />
      </div>
    </div>
  );
};

export default App;
