import React from 'react';
import { X, Command, Keyboard } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const sections = [
    {
      title: 'viewing & navigation',
      shortcuts: [
        { key: 'space / dbl click', desc: 'open photo in full view' },
        { key: '← / →', desc: 'previous / next photo in full view' },
        { key: 'z', desc: 'zoom 200% / fit to screen' },
        { key: 'c', desc: 'compare photos side by side' },
        { key: 'i or ctrl+i', desc: 'show / hide photo info' },
        { key: 'ctrl+k', desc: 'search photos' },
      ],
    },
    {
      title: 'organizing',
      shortcuts: [
        { key: 'shift+click', desc: 'select range of photos' },
        { key: 'right click', desc: 'open quick menu' },
        { key: '1 – 5', desc: 'rate 1 to 5 stars' },
        { key: '0', desc: 'clear rating' },
        { key: 'f', desc: 'favorite / unfavorite' },
        { key: 'r', desc: 'rotate 90°' },
        { key: 'ctrl+a', desc: 'select all' },
        { key: 'delete', desc: 'remove from library' },
        { key: 'esc', desc: 'close / deselect' },
        { key: '?', desc: 'show this list' },
      ],
    },
  ];

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg bg-white rounded-3xl border border-black/[0.08] shadow-appleModal overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-black/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
              <Keyboard className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#1D1D1F] lowercase">
                keyboard shortcuts
              </h3>
              <p className="text-[11px] text-[#86868B] lowercase">
                keys you can press
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#86868B] hover:text-[#1D1D1F] hover:bg-black/5 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
          {sections.map((sec) => (
            <div key={sec.title} className="space-y-2">
              <h4 className="text-[11px] font-bold lowercase tracking-wider text-[#86868B]">
                {sec.title}
              </h4>
              <div className="space-y-1.5 bg-[#F5F5F7]/70 rounded-2xl p-3 border border-black/[0.04]">
                {sec.shortcuts.map((sc) => (
                  <div
                    key={sc.key}
                    className="flex items-center justify-between py-1 px-1.5 text-xs lowercase"
                  >
                    <span className="text-[#1D1D1F] font-medium">{sc.desc}</span>
                    <kbd className="px-2 py-1 rounded-lg bg-white border border-black/10 shadow-2xs font-mono text-[11px] font-semibold text-[#1D1D1F] lowercase">
                      {sc.key}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-[#F5F5F7] border-t border-black/[0.06] flex items-center justify-between text-xs text-[#86868B] lowercase">
          <span>esc to close.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold hover:bg-[#0077ED] transition-colors lowercase"
          >
            done
          </button>
        </div>
      </div>
    </div>
  );
};
