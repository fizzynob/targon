import React, { useState } from 'react';
import {
  X,
  ArrowLeftRight,
  Heart,
  Star,
  Camera,
  Layers,
  Sparkles,
  Maximize2,
  Minimize2,
  Calendar,
  HardDrive,
} from 'lucide-react';
import { PhotoItem } from '../../types';
import { resolveMediaUrl } from '../../api/client';
import { sound } from '../../utils/sound';

interface CompareModalProps {
  photos: [PhotoItem, PhotoItem] | null;
  onClose: () => void;
  onToggleFavorite: (e: React.MouseEvent, photoId: number) => void;
  onSetRating: (photoId: number, rating: number) => void;
}

export const CompareModal: React.FC<CompareModalProps> = ({
  photos,
  onClose,
  onToggleFavorite,
  onSetRating,
}) => {
  const [swapped, setSwapped] = useState(false);
  const [zoomMode, setZoomMode] = useState<'fit' | '100%'>('fit');

  if (!photos || photos.length < 2) return null;

  const photoA = swapped ? photos[1] : photos[0];
  const photoB = swapped ? photos[0] : photos[1];

  const handleSwap = () => {
    sound.playPop();
    setSwapped((prev) => !prev);
  };

  const getMegapixels = (p: PhotoItem) => {
    if (!p.width || !p.height) return null;
    return ((p.width * p.height) / 1000000).toFixed(1) + ' mp';
  };

  const renderSideCard = (photo: PhotoItem, label: string) => {
    const rs = photo.root_systems;
    const mp = getMegapixels(photo);

    return (
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-white/70 backdrop-blur-xl rounded-3xl border border-black/[0.08] shadow-xl">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-black/[0.06] flex items-center justify-between bg-white/80 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="px-2 py-0.5 rounded-full bg-[#0071E3] text-white text-[11px] font-bold lowercase">
              {label}
            </span>
            <span className="text-xs font-semibold text-[#1D1D1F] truncate lowercase" title={photo.filename}>
              {photo.filename}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Interactive Stars */}
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => {
                    sound.playPop();
                    const newRating = (photo.rating || 0) === star ? 0 : star;
                    onSetRating(photo.id, newRating);
                  }}
                  className="p-0.5 text-neutral-300 hover:text-amber-400 transition-colors"
                  title={`rate ${star}`}
                >
                  <Star
                    className={`w-3.5 h-3.5 ${
                      (photo.rating || 0) >= star
                        ? 'text-amber-400 fill-amber-400'
                        : ''
                    }`}
                  />
                </button>
              ))}
            </div>

            {/* Favorite button */}
            <button
              onClick={(e) => {
                if (photo.is_favorite) sound.playUnfavorite();
                else sound.playFavorite();
                onToggleFavorite(e, photo.id);
              }}
              className={`p-1.5 rounded-full transition-colors ${
                photo.is_favorite
                  ? 'bg-rose-50 text-rose-500'
                  : 'text-[#86868B] hover:text-[#1D1D1F] hover:bg-black/5'
              }`}
            >
              <Heart
                className={`w-4 h-4 ${photo.is_favorite ? 'fill-rose-500' : ''}`}
              />
            </button>
          </div>
        </div>

        {/* Image Preview Canvas */}
        <div className="flex-1 min-h-[320px] bg-[#F5F5F7] overflow-auto flex items-center justify-center p-4 relative">
          <img
            src={resolveMediaUrl(photo.preview_url || photo.thumbnail_url)}
            alt={photo.filename}
            className={`transition-all duration-200 rounded-xl select-none ${
              zoomMode === '100%'
                ? 'max-w-none object-none cursor-grab'
                : 'max-h-full max-w-full object-contain'
            }`}
          />
        </div>

        {/* Detailed Metrics Drawer */}
        <div className="p-4 bg-white/95 border-t border-black/[0.06] space-y-3 shrink-0 max-h-[220px] overflow-y-auto">
          {/* Quick Specs Pill Row */}
          <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono lowercase">
            <span className="px-2 py-0.5 rounded-lg bg-black/[0.04] text-[#1D1D1F] font-semibold">
              {photo.image_type.toLowerCase()}
            </span>
            <span className="px-2 py-0.5 rounded-lg bg-black/[0.04] text-[#1D1D1F]">
              {photo.width}×{photo.height}
            </span>
            {mp && (
              <span className="px-2 py-0.5 rounded-lg bg-[#0071E3]/10 text-[#0071E3] font-semibold">
                {mp}
              </span>
            )}
            <span className="px-2 py-0.5 rounded-lg bg-black/[0.04] text-[#86868B]">
              {(photo.file_size / 1024 / 1024).toFixed(2)} mb
            </span>
          </div>

          {/* Camera Optics Capsule */}
          <div className="grid grid-cols-4 gap-1.5 text-center font-mono text-xs lowercase">
            <div className="p-1.5 rounded-xl bg-black/[0.03]">
              <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">device</span>
              <span className="text-[11px] font-semibold truncate block text-[#1D1D1F]" title={photo.device_name}>
                {photo.device_name?.toLowerCase()}
              </span>
            </div>
            <div className="p-1.5 rounded-xl bg-black/[0.03]">
              <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">aperture</span>
              <span className="text-[11px] font-semibold text-[#1D1D1F]">
                {photo.aperture ? `ƒ/${photo.aperture}` : '—'}
              </span>
            </div>
            <div className="p-1.5 rounded-xl bg-black/[0.03]">
              <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">shutter</span>
              <span className="text-[11px] font-semibold text-[#1D1D1F]">
                {photo.shutter_speed ? `${photo.shutter_speed}s` : '—'}
              </span>
            </div>
            <div className="p-1.5 rounded-xl bg-black/[0.03]">
              <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">iso</span>
              <span className="text-[11px] font-semibold text-[#1D1D1F]">
                {photo.iso ? `iso ${photo.iso}` : '—'}
              </span>
            </div>
          </div>

          {/* Hierarchy Chain */}
          <div className="p-2 rounded-xl bg-[#F5F5F7]/80 text-[11px] space-y-1 lowercase">
            <div className="flex items-center gap-1.5 text-[#1D1D1F]">
              <span className="text-[9px] font-bold lowercase tracking-wider text-[#86868B]">type:</span>
              <span className="font-semibold text-[#0071E3]">
                {rs?.type_root?.specific || '—'} → {rs?.type_root?.category || '—'} → {rs?.type_root?.super_type || '—'}
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[#86868B] truncate">
              <span className="text-[9px] font-bold lowercase tracking-wider">folder:</span>
              <span className="truncate">{photo.path}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex flex-col items-center justify-center p-6 select-none animate-fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-7xl h-[92vh] flex flex-col gap-4"
      >
        {/* Top Control Bar */}
        <div className="flex items-center justify-between px-6 py-3 rounded-2xl bg-white/90 backdrop-blur-xl border border-black/[0.08] shadow-lg shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
              <ArrowLeftRight className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#1D1D1F] lowercase">
                compare
              </h3>
              <p className="text-[11px] text-[#86868B] lowercase">
                see two photos side by side
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Swap Left & Right */}
            <button
              onClick={handleSwap}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-xs font-medium text-[#1D1D1F] transition-colors lowercase"
              title="swap"
            >
              <ArrowLeftRight className="w-3.5 h-3.5" />
              <span>swap</span>
            </button>

            {/* Zoom Toggle */}
            <button
              onClick={() => {
                sound.playPop();
                setZoomMode((prev) => (prev === 'fit' ? '100%' : 'fit'));
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-xs font-medium text-[#1D1D1F] transition-colors lowercase"
              title="fit / 100%"
            >
              {zoomMode === 'fit' ? (
                <>
                  <Maximize2 className="w-3.5 h-3.5" />
                  <span>100% zoom</span>
                </>
              ) : (
                <>
                  <Minimize2 className="w-3.5 h-3.5" />
                  <span>fit to screen</span>
                </>
              )}
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 rounded-full text-[#86868B] hover:text-[#1D1D1F] hover:bg-black/5 ml-2 transition-colors"
              title="close (esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Side-by-Side Split View */}
        <div className="flex-1 flex gap-4 min-h-0">
          {renderSideCard(photoA, 'left')}
          {renderSideCard(photoB, 'right')}
        </div>
      </div>
    </div>
  );
};
