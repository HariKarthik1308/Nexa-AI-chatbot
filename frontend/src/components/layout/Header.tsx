import React, { useState, useRef, useEffect } from 'react';
import {
  Menu,
  Moon,
  Sun,
  ChevronDown,
  Sparkles,
  Shield,
  Check,
} from 'lucide-react';
import { ModelOption } from '../../types/chat';
import { AVAILABLE_MODELS } from '../../services/mockChatService';

interface HeaderProps {
  selectedModel: ModelOption;
  onSelectModel: (model: ModelOption) => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onOpenSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedModel,
  onSelectModel,
  theme,
  onToggleTheme,
  onOpenSidebar,
}) => {
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setModelDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 flex items-center justify-between z-10 select-none">
      <div className="flex items-center gap-3">
        {/* Mobile Sidebar Toggle */}
        <button
          type="button"
          onClick={onOpenSidebar}
          className="md:hidden p-2 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Open conversation list"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Model Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setModelDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-expanded={modelDropdownOpen}
          >
            <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>{selectedModel.name}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {modelDropdownOpen && (
            <div className="absolute left-0 mt-1.5 w-72 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-1.5 z-50">
              <div className="px-2.5 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Select Model Provider (Phase 1)
              </div>
              {AVAILABLE_MODELS.map((model) => {
                const isSelected = model.id === selectedModel.id;
                return (
                  <button
                    key={model.id}
                    type="button"
                    onClick={() => {
                      onSelectModel(model);
                      setModelDropdownOpen(false);
                    }}
                    className={`w-full flex items-start gap-2.5 p-2 rounded-lg text-left transition-colors ${
                      isSelected
                        ? 'bg-teal-50 dark:bg-teal-950/60 text-teal-900 dark:text-teal-100'
                        : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="mt-0.5">
                      {isSelected ? (
                        <Check className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                      ) : (
                        <div className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="text-xs font-semibold">{model.name}</div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                        {model.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Mock Mode Pill */}
        <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
          <Shield className="w-3 h-3" />
          Phase 1 Mock Mode
        </span>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        {/* Theme Toggle Button */}
        <button
          type="button"
          onClick={onToggleTheme}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
