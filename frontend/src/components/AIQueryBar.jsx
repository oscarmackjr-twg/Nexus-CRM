import { useState } from 'react';

export default function AIQueryBar({ open, onOpenChange }) {
  const [query, setQuery] = useState('');

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/40"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-xl bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 py-3 border-b border-gray-100">
          <span className="mr-2 text-[#1a3868]">✦</span>
          <input
            autoFocus
            className="flex-1 text-sm outline-none placeholder-gray-400"
            placeholder="Ask anything about your deals, contacts, or data…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') onOpenChange(false);
            }}
          />
          <kbd className="ml-2 text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">Esc</kbd>
        </div>
        <div className="px-4 py-3 text-xs text-gray-400 text-center">
          AI query coming in Phase 14+
        </div>
      </div>
    </div>
  );
}
