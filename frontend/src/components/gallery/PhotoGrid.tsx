import React, { useState, useEffect } from 'react';
import {
  FolderPlus,
  ArrowLeft,
  Check,
  Edit3,
  Heart,
  Gamepad2,
  X,
  Star,
  Copy,
  RotateCw,
  Maximize2,
  FolderOpen,
  Trash2,
  Layers,
  Compass,
} from 'lucide-react';
import { PhotoItem, SubjectItem } from '../../types';
import { PhotoCard } from './PhotoCard';
import { MultiSelectActionBar } from './MultiSelectActionBar';
import { resolveMediaUrl } from '../../api/client';
import { sound } from '../../utils/sound';

function getDateGroup(dateStr?: string | null): string {
  if (!dateStr) return 'no date';
  const clean = dateStr.replace(/:/g, '-').slice(0, 7); // e.g. "2026-10"
  try {
    const [year, month] = clean.split('-');
    if (year && month) {
      const monthNames = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
      ];
      const mIdx = parseInt(month, 10) - 1;
      if (mIdx >= 0 && mIdx < 12) {
        return `${monthNames[mIdx]} ${year}`;
      }
    }
  } catch {}
  return dateStr.slice(0, 10);
}

interface PhotoGridProps {
  photos: PhotoItem[];
  subjects: SubjectItem[];
  selectedPhoto: PhotoItem | null;
  onSelectPhoto: (photo: PhotoItem) => void;
  selectedPhotoIds: Set<number>;
  onTogglePhotoSelection: (photoId: number, isMulti: boolean) => void;
  onSelectRange?: (photoIds: number[]) => void;
  onClearSelection: () => void;
  onBatchFavorite: () => Promise<void>;
  onBatchDelete: () => Promise<void>;
  onOpenLightbox: (photo: PhotoItem) => void;
  onToggleFavorite: (e: React.MouseEvent, photoId: number) => void;
  onSelectSubject: (subject: SubjectItem) => void;
  onSelectCategory: (category: string, label: string) => void;
  onSelectTag: (tagName: string) => void;
  onResetFilter: () => void;
  onRenameSubject: (subjectId: number, newName: string) => Promise<void>;
  onOpenScanModal: () => void;
  onLoadDemoLibrary: () => Promise<void>;
  gridCols: number;
  activeSubject: SubjectItem | null;
  hasActiveFilter: boolean;
  excludeGames?: boolean;
  onToggleExcludeGames?: () => void;
  onDeselectGameAssets?: () => void;
  onExportXmp?: () => void;
  activeTag?: string | null;
  activeCategory?: string | null;
  isFavoritesView?: boolean;
  onToggleFavoritesView?: () => void;
  groupByDate?: boolean;
  minRating?: number | null;
  onToggleMinRating?: (rating: number) => void;
  onOpenCompare?: () => void;
  onBatchTag?: (tagName: string) => void;
  onBatchRating?: (rating: number) => void;
  onBatchRotate?: () => void;
  onRotatePhoto?: (photoId: number) => void;
  onSetRating?: (photoId: number, rating: number) => void;
  onRevealInExplorer?: (photoId: number) => void;
  onDeletePhoto?: (photoId: number) => void;
  duplicatesOnly?: boolean;
  onToggleDuplicatesOnly?: () => void;
  orientationFilter?: string | null;
  onSetOrientationFilter?: (orientation: string | null) => void;
  reduceMotion?: boolean;
  showCardTags?: boolean;
}

export const PhotoGrid: React.FC<PhotoGridProps> = ({
  photos,
  subjects,
  selectedPhoto,
  onSelectPhoto,
  selectedPhotoIds,
  onTogglePhotoSelection,
  onSelectRange,
  onClearSelection,
  onBatchFavorite,
  onBatchDelete,
  onOpenLightbox,
  onToggleFavorite,
  onSelectSubject,
  onSelectCategory,
  onSelectTag,
  onResetFilter,
  onRenameSubject,
  onOpenScanModal,
  onLoadDemoLibrary,
  gridCols,
  activeSubject,
  hasActiveFilter,
  excludeGames = false,
  onToggleExcludeGames,
  onDeselectGameAssets,
  onExportXmp,
  activeTag,
  activeCategory,
  isFavoritesView = false,
  onToggleFavoritesView,
  groupByDate = true,
  minRating = null,
  onToggleMinRating,
  onOpenCompare,
  onBatchTag,
  onBatchRating,
  onBatchRotate,
  onRotatePhoto,
  onSetRating,
  onRevealInExplorer,
  onDeletePhoto,
  duplicatesOnly = false,
  onToggleDuplicatesOnly,
  orientationFilter = null,
  onSetOrientationFilter,
  reduceMotion = false,
  showCardTags = true,
}) => {
  const [editingSubjectName, setEditingSubjectName] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [lastClickedId, setLastClickedId] = useState<number | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; photo: PhotoItem } | null>(null);
  const [visibleLimit, setVisibleLimit] = useState<number>(120);

  // Close context menu on any outside click or Esc
  useEffect(() => {
    const handleClose = () => setContextMenu(null);
    window.addEventListener('click', handleClose);
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setContextMenu(null);
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('click', handleClose);
      window.removeEventListener('keydown', handleKey);
    };
  }, []);

  const selectedPhotosList = photos.filter((p) => selectedPhotoIds.has(p.id));
  const selectedGameCount = selectedPhotosList.filter((p) => p.is_game_asset).length;

  const gridClassMap: Record<number, string> = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4',
    5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5',
    6: 'grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6',
  };

  const handleStartEditSubject = (subj: SubjectItem) => {
    setNameInput(subj.name || '');
    setEditingSubjectName(true);
  };

  const handleSaveSubjectName = async () => {
    if (!activeSubject || !nameInput.trim()) return;
    await onRenameSubject(activeSubject.id, nameInput.trim());
    setEditingSubjectName(false);
  };

  const handleDemoClick = async () => {
    setLoadingDemo(true);
    try {
      await onLoadDemoLibrary();
    } finally {
      setLoadingDemo(false);
    }
  };

  const visiblePhotos = photos.slice(0, visibleLimit);

  // Group photos by date if groupByDate is enabled
  const dateGroups: Array<{ title: string; photos: PhotoItem[] }> = [];
  if (groupByDate && visiblePhotos.length > 0) {
    const groupMap = new Map<string, PhotoItem[]>();
    visiblePhotos.forEach((p) => {
      const g = getDateGroup(p.date_taken || p.created_at);
      if (!groupMap.has(g)) {
        groupMap.set(g, []);
      }
      groupMap.get(g)!.push(p);
    });
    groupMap.forEach((pList, title) => {
      dateGroups.push({ title, photos: pList });
    });
  }

  const handleCardSelect = (photo: PhotoItem, opts: { isMulti: boolean; isRange: boolean }) => {
    if (opts.isRange && lastClickedId !== null && onSelectRange) {
      const idx1 = photos.findIndex((p) => p.id === lastClickedId);
      const idx2 = photos.findIndex((p) => p.id === photo.id);
      if (idx1 !== -1 && idx2 !== -1) {
        const start = Math.min(idx1, idx2);
        const end = Math.max(idx1, idx2);
        const rangeIds = photos.slice(start, end + 1).map((p) => p.id);
        onSelectRange(rangeIds);
        return;
      }
    }

    if (opts.isMulti) {
      onTogglePhotoSelection(photo.id, true);
      setLastClickedId(photo.id);
    } else {
      onSelectPhoto(photo);
      onTogglePhotoSelection(photo.id, false);
      setLastClickedId(photo.id);
    }
  };

  const renderPhotoCard = (photo: PhotoItem) => (
    <PhotoCard
      key={photo.id}
      photo={photo}
      isSelected={selectedPhoto?.id === photo.id}
      isMultiSelected={selectedPhotoIds.has(photo.id)}
      reduceMotion={reduceMotion}
      showCardTags={showCardTags}
      onSelect={handleCardSelect}
      onDoubleClick={onOpenLightbox}
      onToggleFavorite={onToggleFavorite}
      onFilterBySubject={(e, subjId) => {
        e.stopPropagation();
        const found = subjects.find((s) => s.id === subjId);
        if (found) onSelectSubject(found);
      }}
      onFilterByTag={(e, tagName) => {
        e.stopPropagation();
        onSelectTag(tagName);
      }}
      onContextMenu={(e, p) => {
        const x = Math.min(e.clientX, window.innerWidth - 220);
        const y = Math.min(e.clientY, window.innerHeight - 300);
        setContextMenu({ x, y, photo: p });
      }}
    />
  );

  return (
    <div
      onScroll={(e) => {
        if (visibleLimit >= photos.length) return;
        const el = e.currentTarget;
        if (el.scrollHeight - el.scrollTop - el.clientHeight < 420) {
          setVisibleLimit((prev) => Math.min(photos.length, prev + 120));
        }
      }}
      className="flex-1 h-full overflow-y-auto px-8 py-6 space-y-5 bg-[#FBFBFD] select-none relative"
    >
      {/* Quick Filter Strip */}
      <div className="flex items-center justify-between gap-3 overflow-x-auto pb-1 no-scrollbar">
        <div className="flex items-center gap-2">
          {/* All Photos Pill */}
          <button
            onClick={() => {
              sound.playPop();
              onResetFilter();
            }}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
              !hasActiveFilter && minRating === null && !duplicatesOnly && !orientationFilter
                ? 'bg-[#0071E3] text-white shadow-xs'
                : 'bg-white hover:bg-[#F5F5F7] text-[#1D1D1F] border border-black/[0.06]'
            }`}
          >
            all photos
          </button>

          {/* Favorites Pill */}
          <button
            onClick={() => {
              sound.playPop();
              if (onToggleFavoritesView) onToggleFavoritesView();
            }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
              isFavoritesView
                ? 'bg-rose-500 text-white shadow-xs'
                : 'bg-white hover:bg-rose-50 text-[#1D1D1F] border border-black/[0.06]'
            }`}
          >
            <Heart
              className={`w-3.5 h-3.5 ${
                isFavoritesView ? 'fill-white' : 'text-rose-500'
              }`}
            />
            <span>favorites</span>
          </button>

          {/* Star Rating Filter */}
          {onToggleMinRating && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  sound.playPop();
                  onToggleMinRating(4);
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                  minRating === 4
                    ? 'bg-amber-500 text-white shadow-xs'
                    : 'bg-white hover:bg-amber-50 text-[#1D1D1F] border border-black/[0.06]'
                }`}
                title="★ 4+"
              >
                <Star
                  className={`w-3 h-3 ${
                    minRating === 4 ? 'fill-white' : 'text-amber-500'
                  }`}
                />
                <span>★ 4+</span>
              </button>

              <button
                onClick={() => {
                  sound.playPop();
                  onToggleMinRating(5);
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                  minRating === 5
                    ? 'bg-amber-500 text-white shadow-xs'
                    : 'bg-white hover:bg-amber-50 text-[#1D1D1F] border border-black/[0.06]'
                }`}
                title="★ 5"
              >
                <Star
                  className={`w-3 h-3 ${
                    minRating === 5 ? 'fill-white' : 'text-amber-500'
                  }`}
                />
                <span>★ 5</span>
              </button>
            </div>
          )}

          {/* Exclude Games Pill */}
          {onToggleExcludeGames && (
            <button
              onClick={() => {
                sound.playPop();
                onToggleExcludeGames();
              }}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                excludeGames
                  ? 'bg-purple-600 text-white shadow-xs'
                  : 'bg-white hover:bg-purple-50 text-purple-700 border border-purple-200/60'
              }`}
              title="filter game files"
            >
              <Gamepad2 className="w-3.5 h-3.5" />
              <span>{excludeGames ? 'games hidden' : 'hide game files'}</span>
            </button>
          )}

          {/* Similar / Duplicate Shots Filter */}
          {onToggleDuplicatesOnly && (
            <button
              onClick={() => {
                sound.playPop();
                onToggleDuplicatesOnly();
              }}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                duplicatesOnly
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-white hover:bg-indigo-50 text-[#1D1D1F] border border-black/[0.06]'
              }`}
              title="find duplicate or similar shots"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>similar shots</span>
            </button>
          )}

          {/* Orientation Filter */}
          {onSetOrientationFilter && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  sound.playPop();
                  onSetOrientationFilter(orientationFilter === 'landscape' ? null : 'landscape');
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                  orientationFilter === 'landscape'
                    ? 'bg-cyan-600 text-white shadow-xs'
                    : 'bg-white hover:bg-cyan-50 text-[#1D1D1F] border border-black/[0.06]'
                }`}
              >
                <Compass className="w-3 h-3" />
                <span>landscape</span>
              </button>
              <button
                onClick={() => {
                  sound.playPop();
                  onSetOrientationFilter(orientationFilter === 'portrait' ? null : 'portrait');
                }}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                  orientationFilter === 'portrait'
                    ? 'bg-cyan-600 text-white shadow-xs'
                    : 'bg-white hover:bg-cyan-50 text-[#1D1D1F] border border-black/[0.06]'
                }`}
              >
                <span>portrait</span>
              </button>
            </div>
          )}

          {/* Active Tag pill if any */}
          {activeTag && (
            <button
              onClick={() => {
                sound.playPop();
                onSelectTag(activeTag);
              }}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#0071E3] text-white shadow-xs group lowercase"
              title="remove filter"
            >
              <span>#{activeTag.toLowerCase()}</span>
              <X className="w-3 h-3 group-hover:rotate-90 transition-transform" />
            </button>
          )}

          {/* Active Category pill if any */}
          {activeCategory && (
            <button
              onClick={() => {
                sound.playPop();
                onSelectCategory(activeCategory, activeCategory);
              }}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-600 text-white shadow-xs group lowercase"
              title="remove filter"
            >
              <span>category: {activeCategory.toLowerCase()}</span>
              <X className="w-3 h-3 group-hover:rotate-90 transition-transform" />
            </button>
          )}
        </div>

        {/* Multi-Select Select All quick action */}
        {photos.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                sound.playPop();
                if (selectedPhotoIds.size === photos.length) {
                  onClearSelection();
                } else {
                  for (const p of photos) {
                    onTogglePhotoSelection(p.id, true);
                  }
                }
              }}
              className="text-xs text-[#86868B] hover:text-[#1D1D1F] px-2.5 py-1 rounded-lg hover:bg-black/5 transition-colors font-medium lowercase"
            >
              {selectedPhotoIds.size === photos.length ? 'deselect all' : 'select all'}
            </button>
          </div>
        )}
      </div>

      {/* Subject Filter Header Banner (if filtering by subject) */}
      {activeSubject && (
        <div className="bg-white rounded-3xl p-6 border border-black/[0.06] shadow-apple flex items-center justify-between">
          <div className="flex items-center gap-4">
            {activeSubject.avatar_url ? (
              <img
                src={resolveMediaUrl(activeSubject.avatar_url)}
                alt={activeSubject.display_name}
                className="w-16 h-16 rounded-2xl object-cover ring-2 ring-[#0071E3]/20"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold text-xl">
                {activeSubject.display_name[0]}
              </div>
            )}
            <div>
              {editingSubjectName ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={nameInput}
                    onChange={(e) => setNameInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveSubjectName();
                    }}
                    placeholder="e.g. blu"
                    autoFocus
                    className="px-3 py-1 text-base font-semibold bg-[#F5F5F7] rounded-xl border border-[#0071E3] outline-none lowercase"
                  />
                  <button
                    onClick={handleSaveSubjectName}
                    className="p-1.5 rounded-lg bg-[#0071E3] text-white"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setEditingSubjectName(false)}
                    className="p-1.5 rounded-lg bg-[#F5F5F7] text-[#86868B]"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold tracking-tight text-[#1D1D1F] lowercase">
                    {activeSubject.display_name.toLowerCase()}
                  </h2>
                  <button
                    onClick={() => handleStartEditSubject(activeSubject)}
                    className="p-1 text-[#86868B] hover:text-[#0071E3] transition-colors"
                    title="rename"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                </div>
              )}
              <p className="text-xs text-[#86868B] mt-0.5 lowercase">
                tag: #{activeSubject.category.toLowerCase()} • {photos.length} {photos.length === 1 ? 'photo' : 'photos'}
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              sound.playPop();
              onResetFilter();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#F5F5F7] hover:bg-[#E8E8ED] text-[#1D1D1F] transition-colors lowercase"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>all photos</span>
          </button>
        </div>
      )}

      {/* Photos Grid Content */}
      {photos.length === 0 ? (
        <div className="min-h-[50vh] flex flex-col items-center justify-center text-center p-8">
          <div className="w-16 h-16 rounded-3xl bg-white border border-black/[0.06] shadow-apple flex items-center justify-center text-[#86868B] mb-4">
            <FolderPlus className="w-8 h-8 stroke-[1.5]" />
          </div>
          <h3 className="text-lg font-bold text-[#1D1D1F] tracking-tight lowercase">
            {hasActiveFilter ? 'nothing found' : 'no photos yet'}
          </h3>
          <p className="text-xs text-[#86868B] max-w-sm mt-1 mb-6 leading-relaxed lowercase">
            {hasActiveFilter
              ? 'nothing matches this filter. try clicking all photos.'
              : 'pick a folder with pictures to get started.'}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            {hasActiveFilter ? (
              <button
                onClick={() => {
                  sound.playPop();
                  onResetFilter();
                }}
                className="px-5 py-2.5 rounded-full text-xs font-semibold bg-[#0071E3] text-white shadow-apple hover:shadow-appleHover transition-all lowercase"
              >
                all photos
              </button>
            ) : (
              <>
                <button
                  onClick={onOpenScanModal}
                  className="px-5 py-2.5 rounded-full text-xs font-semibold bg-[#0071E3] text-white shadow-apple hover:shadow-appleHover transition-all lowercase"
                >
                  scan folder
                </button>
                <button
                  onClick={handleDemoClick}
                  disabled={loadingDemo}
                  className="px-5 py-2.5 rounded-full text-xs font-semibold bg-white border border-black/[0.08] text-[#1D1D1F] hover:bg-[#F5F5F7] shadow-xs transition-all disabled:opacity-50 lowercase"
                >
                  {loadingDemo ? 'loading...' : 'load sample photos'}
                </button>
              </>
            )}
          </div>
        </div>
      ) : groupByDate ? (
        <div className="space-y-8">
          {dateGroups.map((group) => (
            <div key={group.title} className="space-y-3">
              <div className="sticky top-0 z-10 py-1.5 bg-[#FBFBFD]/95 flex items-center justify-between border-b border-black/[0.04]">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#86868B] lowercase">
                  {group.title}
                </h3>
                <span className="text-[11px] font-medium text-[#86868B] lowercase">
                  {group.photos.length} {group.photos.length === 1 ? 'photo' : 'photos'}
                </span>
              </div>
              <div className={`grid ${gridClassMap[gridCols] || gridClassMap[4]} gap-4`}>
                {group.photos.map(renderPhotoCard)}
              </div>
            </div>
          ))}
          {visibleLimit < photos.length && (
            <div className="flex justify-center pt-2 pb-6">
              <button
                onClick={() => setVisibleLimit((prev) => prev + 180)}
                className="px-5 py-2 rounded-full bg-white hover:bg-[#F5F5F7] text-xs font-semibold text-[#1D1D1F] border border-black/[0.08] shadow-2xs lowercase"
              >
                show more ({photos.length - visibleLimit} left)
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className={`grid ${gridClassMap[gridCols] || gridClassMap[4]} gap-4`}>
            {visiblePhotos.map(renderPhotoCard)}
          </div>
          {visibleLimit < photos.length && (
            <div className="flex justify-center pt-2 pb-6">
              <button
                onClick={() => setVisibleLimit((prev) => prev + 180)}
                className="px-5 py-2 rounded-full bg-white hover:bg-[#F5F5F7] text-xs font-semibold text-[#1D1D1F] border border-black/[0.08] shadow-2xs lowercase"
              >
                show more ({photos.length - visibleLimit} left)
              </button>
            </div>
          )}
        </div>
      )}

      {/* Floating Bottom Multi-Select Action Bar */}
      <MultiSelectActionBar
        selectedCount={selectedPhotoIds.size}
        selectedGameCount={selectedGameCount}
        onClearSelection={onClearSelection}
        onBatchFavorite={onBatchFavorite}
        onBatchDelete={onBatchDelete}
        onDeselectGameAssets={onDeselectGameAssets}
        onExportXmp={onExportXmp}
        onOpenCompare={onOpenCompare}
        onBatchTag={onBatchTag}
        onBatchRating={onBatchRating}
        onBatchRotate={onBatchRotate}
      />

      {/* Right-Click Context Menu */}
      {contextMenu && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{ top: contextMenu.y, left: contextMenu.x }}
          className="fixed z-50 w-52 bg-white/95 backdrop-blur-xl border border-black/10 rounded-2xl shadow-2xl py-1.5 text-xs text-[#1D1D1F] select-none lowercase"
        >
          <button
            onClick={() => {
              onOpenLightbox(contextMenu.photo);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#0071E3] hover:text-white transition-colors text-left"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>open in full view</span>
          </button>

          <button
            onClick={(e) => {
              onToggleFavorite(e, contextMenu.photo.id);
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#0071E3] hover:text-white transition-colors text-left"
          >
            <Heart
              className={`w-3.5 h-3.5 ${
                contextMenu.photo.is_favorite ? 'fill-rose-500 text-rose-500' : ''
              }`}
            />
            <span>{contextMenu.photo.is_favorite ? 'unfavorite' : 'favorite'}</span>
          </button>

          {onSetRating && (
            <div className="px-3 py-1.5 border-t border-black/5 flex items-center justify-between">
              <span className="text-[#86868B]">rate:</span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => {
                      onSetRating(contextMenu.photo.id, (contextMenu.photo.rating || 0) === star ? 0 : star);
                      setContextMenu(null);
                    }}
                    className="p-0.5 hover:scale-125 transition-transform"
                    title={`${star} star${star > 1 ? 's' : ''}`}
                  >
                    <Star
                      className={`w-3.5 h-3.5 ${
                        (contextMenu.photo.rating || 0) >= star
                          ? 'fill-amber-400 text-amber-500'
                          : 'text-[#86868B]'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
          )}

          {onRotatePhoto && (
            <button
              onClick={() => {
                onRotatePhoto(contextMenu.photo.id);
                setContextMenu(null);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#0071E3] hover:text-white transition-colors text-left"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>rotate 90°</span>
            </button>
          )}

          <button
            onClick={() => {
              navigator.clipboard?.writeText(contextMenu.photo.path);
              sound.playPop();
              setContextMenu(null);
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#0071E3] hover:text-white transition-colors text-left"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>copy file path</span>
          </button>

          {onRevealInExplorer && (
            <button
              onClick={() => {
                onRevealInExplorer(contextMenu.photo.id);
                setContextMenu(null);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#0071E3] hover:text-white transition-colors text-left"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              <span>show in explorer</span>
            </button>
          )}

          {onDeletePhoto && (
            <div className="border-t border-black/5 mt-1 pt-1">
              <button
                onClick={() => {
                  onDeletePhoto(contextMenu.photo.id);
                  setContextMenu(null);
                }}
                className="w-full flex items-center gap-2.5 px-3 py-1.5 text-rose-600 hover:bg-rose-500 hover:text-white transition-colors text-left"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>remove from library</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
