import React, { useState, useEffect } from 'react';
import {
  X,
  FolderPlus,
  HardDrive,
  Sparkles,
  Loader2,
  CheckCircle2,
  FolderOpen,
} from 'lucide-react';
import { ScanStatus, DriveQuickFolder } from '../../types';
import { api } from '../../api/client';

interface ScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  scanStatus: ScanStatus;
  onStartScan: (folderPath: string, recursive: boolean) => Promise<void>;
  onCancelScan: () => Promise<void>;
  onScanDemo: () => Promise<void>;
}

export const ScanModal: React.FC<ScanModalProps> = ({
  isOpen,
  onClose,
  scanStatus,
  onStartScan,
  onCancelScan,
  onScanDemo,
}) => {
  const [customPath, setCustomPath] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [quickFolders, setQuickFolders] = useState<DriveQuickFolder[]>([]);
  const [drives, setDrives] = useState<DriveQuickFolder[]>([]);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api
        .getDrives()
        .then((data) => {
          setQuickFolders(data.quick_folders || []);
          setDrives(data.drives || []);
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isScanning = scanStatus.status === 'indexing' || scanStatus.status === 'analyzing';

  const handleNativeBrowse = async () => {
    if (window.targonDesktop?.selectFolder) {
      const chosen = await window.targonDesktop.selectFolder();
      if (chosen) {
        setCustomPath(chosen);
      }
    }
  };

  const handleStartCustomScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customPath.trim()) return;
    await onStartScan(customPath.trim(), recursive);
  };

  const handleRunDemo = async () => {
    setDemoLoading(true);
    try {
      await onScanDemo();
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-white rounded-3xl shadow-appleModal border border-black/[0.08] overflow-hidden">
        {/* Header */}
        <div className="px-7 py-5 border-b border-black/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#1D1D1F] lowercase">scan folder</h3>
              <p className="text-xs text-[#86868B] lowercase">
                pick a folder and we'll look through it for photos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#F5F5F7] text-[#86868B] hover:text-[#1D1D1F]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-7 space-y-6">
          {/* Active Scan Progress Card */}
          {(isScanning || scanStatus.status === 'completed') && scanStatus.total_files > 0 && (
            <div className="p-4 rounded-2xl bg-[#F5F5F7] border border-black/[0.05] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-xs font-semibold text-[#1D1D1F] lowercase">
                  {isScanning ? (
                    <>
                      <Loader2 className="w-4 h-4 text-[#0071E3] animate-spin" />
                      <span>looking through photos...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      <span>done scanning</span>
                    </>
                  )}
                </span>
                <span className="text-xs font-bold text-[#0071E3]">
                  {scanStatus.analyzed_files} / {scanStatus.total_files} ({scanStatus.progress_percent}%)
                </span>
              </div>

              <div className="w-full h-2 rounded-full bg-black/[0.08] overflow-hidden">
                <div
                  className="h-full bg-[#0071E3] transition-all duration-300 rounded-full"
                  style={{ width: `${scanStatus.progress_percent}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-[#86868B] lowercase">
                <span className="truncate max-w-[320px]">
                  {scanStatus.current_file || scanStatus.current_folder}
                </span>
                <span>{scanStatus.speed_fps}/s</span>
              </div>

              {isScanning && (
                <div className="pt-1 flex justify-end">
                  <button
                    onClick={onCancelScan}
                    className="px-3 py-1 rounded-lg bg-white text-xs font-medium text-rose-600 border border-black/10 hover:bg-rose-50 lowercase"
                  >
                    stop scan
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Custom Folder Input + Native Browse */}
          <form onSubmit={handleStartCustomScan} className="space-y-3">
            <label className="block text-xs font-semibold lowercase tracking-wider text-[#86868B]">
              folder path
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={customPath}
                onChange={(e) => setCustomPath(e.target.value)}
                placeholder="c:\users\...\pictures"
                className="flex-1 px-4 py-2.5 text-sm bg-[#F5F5F7] focus:bg-white rounded-2xl border border-transparent focus:border-[#0071E3] outline-none lowercase"
              />
              {window.targonDesktop?.isElectron && (
                <button
                  type="button"
                  onClick={handleNativeBrowse}
                  className="px-4 py-2.5 rounded-2xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-xs font-semibold text-[#1D1D1F] shrink-0 lowercase"
                >
                  browse...
                </button>
              )}
              <button
                type="submit"
                disabled={isScanning || !customPath.trim()}
                className="px-5 py-2.5 rounded-2xl bg-[#0071E3] hover:bg-[#0077ED] disabled:opacity-40 text-white text-xs font-semibold shadow-xs shrink-0 lowercase"
              >
                start
              </button>
            </div>

            <label className="inline-flex items-center gap-2 text-xs text-[#86868B] cursor-pointer lowercase">
              <input
                type="checkbox"
                checked={recursive}
                onChange={(e) => setRecursive(e.target.checked)}
                className="rounded accent-[#0071E3]"
              />
              <span>look in subfolders too</span>
            </label>
          </form>

          {/* Quick Folders & Demo Dataset */}
          <div className="space-y-2.5">
            <p className="text-xs font-semibold lowercase tracking-wider text-[#86868B]">
              quick folders
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-52 overflow-y-auto pr-1">
              {quickFolders.map((qf) => (
                <button
                  key={qf.path}
                  onClick={() =>
                    qf.type === 'demo' ? handleRunDemo() : onStartScan(qf.path, recursive)
                  }
                  disabled={isScanning || demoLoading}
                  className={`flex items-center justify-between p-3 rounded-2xl border text-left transition-all ${
                    qf.type === 'demo'
                      ? 'bg-[#0071E3]/[0.06] border-[#0071E3]/20 hover:bg-[#0071E3]/10'
                      : 'bg-[#F5F5F7]/70 border-black/[0.05] hover:bg-[#F5F5F7]'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {qf.type === 'demo' ? (
                      <Sparkles className="w-4 h-4 text-[#0071E3] shrink-0" />
                    ) : (
                      <FolderOpen className="w-4 h-4 text-[#86868B] shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-[#1D1D1F] truncate lowercase">{qf.name}</p>
                      <p className="text-[10px] text-[#86868B] truncate lowercase">{qf.path}</p>
                    </div>
                  </div>
                </button>
              ))}

              {drives.map((dr) => (
                <button
                  key={dr.path}
                  onClick={() => setCustomPath(dr.path)}
                  className="flex items-center justify-between p-3 rounded-2xl bg-[#F5F5F7]/70 border border-black/[0.05] hover:bg-[#F5F5F7] text-left transition-all"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <HardDrive className="w-4 h-4 text-[#86868B] shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-[#1D1D1F] truncate lowercase">{dr.name}</p>
                      <p className="text-[10px] text-[#86868B] truncate lowercase">{dr.path}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
