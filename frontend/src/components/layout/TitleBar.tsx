import React, { useState } from 'react';
import {
  Search,
  FolderPlus,
  Sparkles,
  Info,
  ZoomIn,
  ZoomOut,
  Loader2,
  CheckCircle2,
  X,
  ArrowUpDown,
  Calendar,
  LayoutGrid,
  HelpCircle,
  ArrowLeftRight,
} from 'lucide-react';
import { ScanStatus, SettingsModel } from '../../types';
import { sound } from '../../utils/sound';

interface TitleBarProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  onOpenSpotlight: () => void;
  gridCols: number;
  onGridColsChange: (cols: number) => void;
  onOpenScanModal: () => void;
  onOpenSettingsModal: () => void;
  inspectorOpen: boolean;
  onToggleInspector: () => void;
  scanStatus: ScanStatus;
  settings: SettingsModel;
  activeViewTitle: string;
  photoCount: number;
  sortBy: string;
  onSortByChange: (val: string) => void;
  groupByDate: boolean;
  onToggleGroupByDate: () => void;
  onOpenShortcutsModal: () => void;
  onOpenCompare?: () => void;
  canCompare?: boolean;
}

export const TitleBar: React.FC<TitleBarProps> = ({
  searchQuery,
  onSearchChange,
  onOpenSpotlight,
  gridCols,
  onGridColsChange,
  onOpenScanModal,
  onOpenSettingsModal,
  inspectorOpen,
  onToggleInspector,
  scanStatus,
  settings,
  activeViewTitle,
  photoCount,
  sortBy,
  onSortByChange,
  groupByDate,
  onToggleGroupByDate,
  onOpenShortcutsModal,
  onOpenCompare,
  canCompare = false,
}) => {
  const isScanning =
    scanStatus.status === 'indexing' || scanStatus.status === 'analyzing';

  const modeLabel =
    settings.ai_mode === 'local'
      ? 'offline'
      : settings.ai_mode === 'hybrid'
      ? 'hybrid'
      : 'cloud';

  return (
    <header className="h-16 px-6 flex items-center justify-between bg-white/80 backdrop-blur-2xl border-b border-black/[0.06] select-none app-drag-region z-20 shrink-0">
      {/* Left: View Title & Subtitle */}
      <div className="flex items-center gap-3 app-no-drag min-w-[200px]">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-[18px] font-semibold tracking-tight text-[#1D1D1F] lowercase">
              {activeViewTitle}
            </h1>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[#F5F5F7] text-[#86868B] lowercase">
              {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
            </span>
          </div>
        </div>
      </div>

      {/* Center: Spotlight Search Bar */}
      <div className="flex-1 max-w-md mx-4 app-no-drag">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-[#86868B] absolute left-3.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="search something or press ctrl+k..."
            className="w-full pl-9 pr-16 py-1.5 text-[13px] bg-[#F5F5F7]/90 hover:bg-[#EEEEF0] focus:bg-white text-[#1D1D1F] placeholder-[#86868B] rounded-full border border-transparent focus:border-[#0071E3]/40 focus:ring-4 focus:ring-[#0071E3]/10 outline-none transition-all duration-200 lowercase"
          />
          {searchQuery ? (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 p-0.5 rounded-full hover:bg-black/10 text-[#86868B]"
              title="clear"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={onOpenSpotlight}
              className="absolute right-2.5 px-1.5 py-0.5 text-[10px] font-medium text-[#86868B] bg-white rounded border border-black/10 shadow-2xs hover:text-[#1D1D1F] lowercase"
              title="search (ctrl+k)"
            >
              ctrl+k
            </button>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5 app-no-drag">
        {/* Sort Selector Dropdown */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-[#F5F5F7] text-xs font-medium text-[#1D1D1F]">
          <ArrowUpDown className="w-3.5 h-3.5 text-[#86868B]" />
          <select
            value={sortBy}
            onChange={(e) => {
              sound.playPop();
              onSortByChange(e.target.value);
            }}
            className="bg-transparent outline-none cursor-pointer text-xs font-medium text-[#1D1D1F] lowercase"
            title="sort"
          >
            <option value="date_desc">date: newest</option>
            <option value="date_asc">date: oldest</option>
            <option value="rating_desc">rating: highest (★)</option>
            <option value="name_asc">name: a → z</option>
            <option value="name_desc">name: z → a</option>
            <option value="size_desc">size: largest</option>
            <option value="size_asc">size: smallest</option>
          </select>
        </div>

        {/* Group By Date / Flat View Toggle */}
        <button
          onClick={() => {
            sound.playPop();
            onToggleGroupByDate();
          }}
          className={`p-2 rounded-full transition-colors ${
            groupByDate
              ? 'bg-[#0071E3] text-white shadow-2xs'
              : 'bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED]'
          }`}
          title={
            groupByDate
              ? 'grouped by date'
              : 'flat grid'
          }
        >
          {groupByDate ? (
            <Calendar className="w-3.5 h-3.5" />
          ) : (
            <LayoutGrid className="w-3.5 h-3.5" />
          )}
        </button>

        {/* Compare Button (When 2 photos selected) */}
        {canCompare && onOpenCompare && (
          <button
            onClick={() => {
              sound.playPop();
              onOpenCompare();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0071E3] text-white text-xs font-semibold shadow-xs hover:bg-[#0077ED] transition-all lowercase"
            title="compare (c)"
          >
            <ArrowLeftRight className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">compare</span>
          </button>
        )}

        {/* Grid Zoom Slider */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F5F5F7]">
          <button
            onClick={() => onGridColsChange(Math.min(6, gridCols + 1))}
            className="text-[#86868B] hover:text-[#1D1D1F] transition-colors"
            title="smaller thumbnails"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <input
            type="range"
            min={2}
            max={6}
            step={1}
            value={8 - gridCols}
            onChange={(e) => onGridColsChange(8 - Number(e.target.value))}
            className="w-14 accent-[#0071E3] cursor-pointer h-1"
          />
          <button
            onClick={() => onGridColsChange(Math.max(2, gridCols - 1))}
            className="text-[#86868B] hover:text-[#1D1D1F] transition-colors"
            title="larger thumbnails"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Live Scan Status Pill or AI Mode Pill */}
        {isScanning ? (
          <button
            onClick={onOpenScanModal}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0071E3]/10 text-[#0071E3] text-xs font-medium animate-pulse lowercase"
          >
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>
              scanning {scanStatus.analyzed_files}/{scanStatus.total_files} ({scanStatus.progress_percent}%)
            </span>
          </button>
        ) : (
          <button
            onClick={onOpenSettingsModal}
            className="hidden 2xl:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F5F5F7] hover:bg-[#EBEBED] text-[#1D1D1F] text-xs font-medium transition-colors lowercase"
            title="settings"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#0071E3]" />
            <span>{modeLabel}</span>
            <CheckCircle2 className="w-3 h-3 text-emerald-500 ml-0.5" />
          </button>
        )}

        {/* Scan Button */}
        <button
          onClick={onOpenScanModal}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#0071E3] hover:bg-[#0077ED] active:scale-[0.98] text-white text-xs font-medium shadow-xs transition-all lowercase"
        >
          <FolderPlus className="w-3.5 h-3.5" />
          <span>scan folder</span>
        </button>

        {/* Keyboard Shortcuts Help Button (?) */}
        <button
          onClick={onOpenShortcutsModal}
          className="p-2 rounded-full bg-[#F5F5F7] text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors"
          title="shortcuts (?)"
        >
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* Inspector Toggle Button */}
        <button
          onClick={onToggleInspector}
          className={`p-2 rounded-full transition-colors ${
            inspectorOpen
              ? 'bg-[#0071E3] text-white shadow-xs'
              : 'bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED]'
          }`}
          title="info (i)"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
