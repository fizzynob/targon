import React, { useState, useEffect } from 'react';
import { Search, Sparkles, Tag, X } from 'lucide-react';
import { SubjectItem, TagInfo } from '../../types';
import { resolveMediaUrl } from '../../api/client';

interface SpotlightModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjects: SubjectItem[];
  tags: TagInfo[];
  onSelectSubject: (subj: SubjectItem) => void;
  onSelectTag: (tagName: string) => void;
  onRunSearch: (query: string) => void;
}

export const SpotlightModal: React.FC<SpotlightModalProps> = ({
  isOpen,
  onClose,
  subjects,
  tags,
  onSelectSubject,
  onSelectTag,
  onRunSearch,
}) => {
  const [input, setInput] = useState('');

  useEffect(() => {
    if (isOpen) setInput('');
  }, [isOpen]);

  if (!isOpen) return null;

  const q = input.trim().toLowerCase();
  const matchedSubjects = subjects.filter(
    (s) =>
      !q ||
      s.display_name.toLowerCase().includes(q) ||
      s.category.toLowerCase().includes(q)
  );
  const matchedTags = tags
    .filter((t) => !q || t.name.toLowerCase().includes(q))
    .slice(0, 10);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/25 backdrop-blur-xs p-4"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg bg-white/95 backdrop-blur-2xl rounded-3xl shadow-appleModal border border-black/10 overflow-hidden"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onRunSearch(input);
            onClose();
          }}
          className="px-5 py-4 border-b border-black/[0.06] flex items-center gap-3"
        >
          <Search className="w-5 h-5 text-[#0071E3]" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="search photos..."
            autoFocus
            className="flex-1 text-base bg-transparent text-[#1D1D1F] placeholder-[#86868B] outline-none lowercase"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-full hover:bg-[#F5F5F7] text-[#86868B]"
          >
            <X className="w-4 h-4" />
          </button>
        </form>

        <div className="p-5 space-y-5 max-h-96 overflow-y-auto">
          {matchedSubjects.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B] mb-2">
                people & pets
              </p>
              <div className="flex flex-wrap gap-2">
                {matchedSubjects.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => {
                      onSelectSubject(s);
                      onClose();
                    }}
                    className="flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-full bg-[#F5F5F7] hover:bg-[#0071E3] hover:text-white transition-colors lowercase"
                  >
                    {s.avatar_url ? (
                      <img
                        src={resolveMediaUrl(s.avatar_url)}
                        alt={s.display_name}
                        className="w-6 h-6 rounded-full object-cover"
                      />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    <span className="text-xs font-semibold lowercase">{s.display_name}</span>
                    <span className="text-[10px] opacity-75 lowercase">({s.category})</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {matchedTags.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B] mb-2">
                tags
              </p>
              <div className="flex flex-wrap gap-1.5">
                {matchedTags.map((t) => (
                  <button
                    key={`${t.tag_type}-${t.name}`}
                    onClick={() => {
                      onSelectTag(t.name);
                      onClose();
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F5F5F7] hover:bg-[#0071E3] hover:text-white text-xs font-medium transition-colors lowercase"
                  >
                    <Tag className="w-3 h-3 opacity-70" />
                    <span>{t.name.toLowerCase()}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
