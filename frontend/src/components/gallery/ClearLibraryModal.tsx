import React, { useState } from 'react';
import { Trash2, AlertTriangle, X } from 'lucide-react';

interface ClearLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmClear: (deleteFiles: boolean) => Promise<void>;
  photoCount: number;
}

export const ClearLibraryModal: React.FC<ClearLibraryModalProps> = ({
  isOpen,
  onClose,
  onConfirmClear,
  photoCount,
}) => {
  const [deleteFiles, setDeleteFiles] = useState(false);
  const [clearing, setClearing] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setClearing(true);
    try {
      await onConfirmClear(deleteFiles);
      onClose();
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-md bg-white rounded-3xl p-6 border border-black/[0.08] shadow-2xl space-y-5 animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <Trash2 className="w-6 h-6" />
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-[#8E8E93] hover:text-[#1C1C1E] hover:bg-black/5 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div>
          <h2 className="text-lg font-bold text-[#1C1C1E] tracking-tight lowercase">
            clear library ({photoCount} photos)
          </h2>
          <p className="text-xs text-[#8E8E93] mt-2 leading-relaxed lowercase">
            removes everything from this list. your actual files on your computer won't be touched unless you check the box below.
          </p>
        </div>

        {/* Optional delete from disk toggle */}
        <label className="flex items-start gap-2.5 p-3 rounded-xl bg-[#F5F5F7] border border-black/[0.04] cursor-pointer select-none">
          <input
            type="checkbox"
            checked={deleteFiles}
            onChange={(e) => setDeleteFiles(e.target.checked)}
            className="mt-0.5 rounded text-rose-600 focus:ring-rose-500"
          />
          <div className="text-xs lowercase">
            <span className="font-semibold text-rose-600 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> also delete the actual files from disk
            </span>
            <span className="text-[#8E8E93] block text-[11px] mt-0.5">
              careful: this really deletes them from your computer.
            </span>
          </div>
        </label>

        <div className="flex items-center justify-end gap-2.5 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={clearing}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#1C1C1E] bg-[#F5F5F7] hover:bg-[#E5E5EA] transition-colors lowercase"
          >
            cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={clearing}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-sm disabled:opacity-50 lowercase"
          >
            {clearing ? 'clearing...' : 'clear library'}
          </button>
        </div>
      </div>
    </div>
  );
};
