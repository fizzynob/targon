import React, { useState } from 'react';
import {
  Trash2,
  Heart,
  X,
  CheckSquare,
  Gamepad2,
  FileDown,
  ArrowLeftRight,
  Tag,
  Star,
  RotateCw,
  Plus,
} from 'lucide-react';
import { sound } from '../../utils/sound';

interface MultiSelectActionBarProps {
  selectedCount: number;
  selectedGameCount?: number;
  onClearSelection: () => void;
  onBatchFavorite: () => void;
  onBatchDelete: () => void;
  onDeselectGameAssets?: () => void;
  onExportXmp?: () => void;
  onOpenCompare?: () => void;
  onBatchTag?: (tagName: string) => void;
  onBatchRating?: (rating: number) => void;
  onBatchRotate?: () => void;
}

export const MultiSelectActionBar: React.FC<MultiSelectActionBarProps> = ({
  selectedCount,
  selectedGameCount = 0,
  onClearSelection,
  onBatchFavorite,
  onBatchDelete,
  onDeselectGameAssets,
  onExportXmp,
  onOpenCompare,
  onBatchTag,
  onBatchRating,
  onBatchRotate,
}) => {
  const [showTagInput, setShowTagInput] = useState(false);
  const [tagInput, setTagInput] = useState('');

  if (selectedCount === 0) return null;

  const handleSubmitTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (tagInput.trim() && onBatchTag) {
      sound.playPop();
      onBatchTag(tagInput.trim());
      setTagInput('');
      setShowTagInput(false);
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 animate-slide-up select-none">
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white/95 backdrop-blur-xl border border-black/[0.08] shadow-2xl text-xs font-medium text-[#1C1C1E]">
        {/* Count Pill */}
        <div className="flex items-center gap-1.5 pr-2.5 border-r border-black/[0.08] text-[#0071E3] font-semibold">
          <CheckSquare className="w-4 h-4" />
          <span>{selectedCount} selected</span>
        </div>

        {/* Compare Button (When exactly 2 photos are selected) */}
        {selectedCount === 2 && onOpenCompare && (
          <button
            onClick={() => {
              sound.playPop();
              onOpenCompare();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#0071E3] text-white hover:bg-[#0077ED] font-semibold transition-colors shadow-2xs lowercase"
            title="compare (c)"
          >
            <ArrowLeftRight className="w-3.5 h-3.5" />
            <span>compare</span>
            <kbd className="hidden sm:inline-block px-1 py-0.2 rounded bg-white/20 text-[10px] font-mono text-white lowercase">
              c
            </kbd>
          </button>
        )}

        {/* Favorite (F) */}
        <button
          onClick={() => {
            sound.playFavorite();
            onBatchFavorite();
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-black/5 text-[#1C1C1E] transition-colors lowercase"
          title="favorite (f)"
        >
          <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500/20" />
          <span>favorite</span>
          <kbd className="hidden sm:inline-block px-1 py-0.2 rounded bg-black/5 text-[10px] text-[#86868B] font-mono lowercase">
            f
          </kbd>
        </button>

        {/* Batch Rating Stars */}
        {onBatchRating && (
          <div className="hidden lg:flex items-center gap-0.5 px-1 py-1 rounded-xl bg-black/[0.03]">
            {[1, 2, 3, 4, 5].map((s) => (
              <button
                key={s}
                onClick={() => {
                  sound.playPop();
                  onBatchRating(s);
                }}
                className="p-1 hover:text-amber-400 text-neutral-300 transition-colors"
                title={`rate ${s} (${s})`}
              >
                <Star className="w-3.5 h-3.5" />
              </button>
            ))}
          </div>
        )}

        {/* Batch Tag Button / Popover */}
        {onBatchTag && (
          <div className="relative">
            {showTagInput ? (
              <form onSubmit={handleSubmitTag} className="flex items-center gap-1">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  placeholder="new tag..."
                  autoFocus
                  className="px-2.5 py-1 text-xs bg-[#F5F5F7] rounded-lg border border-[#0071E3] outline-none text-[#1D1D1F] w-28 lowercase"
                />
                <button
                  type="submit"
                  className="p-1 rounded-lg bg-[#0071E3] text-white hover:bg-[#0077ED]"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setShowTagInput(false)}
                  className="p-1 rounded-lg hover:bg-black/5 text-[#86868B]"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </form>
            ) : (
              <button
                onClick={() => setShowTagInput(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-black/5 text-[#1C1C1E] transition-colors lowercase"
                title="add tag to selected"
              >
                <Tag className="w-3.5 h-3.5 text-[#0071E3]" />
                <span>+ tag</span>
              </button>
            )}
          </div>
        )}

        {/* Rotate Button */}
        {onBatchRotate && (
          <button
            onClick={() => {
              sound.playPop();
              onBatchRotate();
            }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl hover:bg-black/5 text-[#1C1C1E] transition-colors"
            title="rotate 90° (r)"
          >
            <RotateCw className="w-3.5 h-3.5 text-[#86868B]" />
          </button>
        )}

        {/* Game Assets Deselection Button */}
        {selectedGameCount > 0 && onDeselectGameAssets && (
          <button
            onClick={() => {
              sound.playPop();
              onDeselectGameAssets();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100/80 text-purple-700 transition-colors border border-purple-200/50 lowercase"
            title="unselect game files"
          >
            <Gamepad2 className="w-3.5 h-3.5 text-purple-600" />
            <span>unselect game files ({selectedGameCount})</span>
          </button>
        )}

        {/* Export XMP Sidecars */}
        {onExportXmp && (
          <button
            onClick={() => {
              sound.playPop();
              onExportXmp();
            }}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-black/5 text-[#1C1C1E] transition-colors lowercase"
            title="save .xmp files"
          >
            <FileDown className="w-3.5 h-3.5 text-[#0071E3]" />
            <span>save .xmp</span>
          </button>
        )}

        {/* Delete (Backspace) */}
        <button
          onClick={() => {
            sound.playDelete();
            onBatchDelete();
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-rose-50 text-rose-600 transition-colors lowercase"
          title="remove selected (delete)"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>remove</span>
          <kbd className="hidden sm:inline-block px-1 py-0.2 rounded bg-rose-100/60 text-[10px] text-rose-500 font-mono">
            ⌫
          </kbd>
        </button>

        {/* Clear Selection (Esc) */}
        <button
          onClick={() => {
            sound.playPop();
            onClearSelection();
          }}
          className="flex items-center gap-1 p-1.5 rounded-xl text-[#8E8E93] hover:text-[#1D1D1F] hover:bg-black/5 ml-1 transition-colors"
          title="clear selection (esc)"
        >
          <X className="w-3.5 h-3.5" />
          <kbd className="hidden sm:inline-block px-1 py-0.2 rounded bg-black/5 text-[9px] text-[#86868B] font-mono lowercase">
            esc
          </kbd>
        </button>
      </div>
    </div>
  );
};
