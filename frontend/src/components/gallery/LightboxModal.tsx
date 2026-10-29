import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Heart,
  Star,
  RotateCw,
  Info,
  Maximize2,
  Minimize2,
  FolderOpen,
  Copy,
  Tag,
  Sparkles,
  Camera,
  Check,
} from 'lucide-react';
import { PhotoItem } from '../../types';
import { resolveMediaUrl } from '../../api/client';
import { sound } from '../../utils/sound';

interface LightboxModalProps {
  photo: PhotoItem | null;
  photos: PhotoItem[];
  onClose: () => void;
  onSelectPhoto: (photo: PhotoItem) => void;
  onToggleFavorite?: (e: React.MouseEvent, photoId: number) => void;
  onSetRating?: (photoId: number, rating: number) => void;
  onRotatePhoto?: (photoId: number) => void;
  onDeletePhoto?: (photoId: number) => void;
  onRevealInExplorer?: (photoId: number) => void;
}

export const LightboxModal: React.FC<LightboxModalProps> = ({
  photo,
  photos,
  onClose,
  onSelectPhoto,
  onToggleFavorite,
  onSetRating,
  onRotatePhoto,
  onRevealInExplorer,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showInfo, setShowInfo] = useState(false);
  const [copiedOcr, setCopiedOcr] = useState(false);

  const filmstripRef = useRef<HTMLDivElement>(null);

  const currentIndex = photo ? photos.findIndex((p) => p.id === photo.id) : -1;
  const currentPhoto = photo;

  const goToNext = useCallback(() => {
    if (photos.length <= 1 || currentIndex === -1) return;
    const nextIdx = (currentIndex + 1) % photos.length;
    setZoom(1);
    setPan({ x: 0, y: 0 });
    onSelectPhoto(photos[nextIdx]);
    sound.playPop();
  }, [photos, currentIndex, onSelectPhoto]);

  const goToPrev = useCallback(() => {
    if (photos.length <= 1 || currentIndex === -1) return;
    const prevIdx = (currentIndex - 1 + photos.length) % photos.length;
    setZoom(1);
    setPan({ x: 0, y: 0 });
    onSelectPhoto(photos[prevIdx]);
    sound.playPop();
  }, [photos, currentIndex, onSelectPhoto]);

  // Keyboard navigation & controls
  useEffect(() => {
    if (!currentPhoto) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          e.stopPropagation();
          onClose();
          break;
        case 'ArrowRight':
          goToNext();
          break;
        case 'ArrowLeft':
          goToPrev();
          break;
        case 'f':
        case 'F':
          if (onToggleFavorite && currentPhoto) {
            onToggleFavorite(e as unknown as React.MouseEvent, currentPhoto.id);
          }
          break;
        case 'r':
        case 'R':
          if (onRotatePhoto && currentPhoto) {
            onRotatePhoto(currentPhoto.id);
          }
          break;
        case 'i':
        case 'I':
          setShowInfo((prev) => !prev);
          sound.playPop();
          break;
        case 'z':
        case 'Z':
          setZoom((prev) => (prev > 1 ? 1 : 2));
          setPan({ x: 0, y: 0 });
          sound.playPop();
          break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5': {
          const val = parseInt(e.key, 10);
          if (onSetRating && currentPhoto) {
            onSetRating(currentPhoto.id, currentPhoto.rating === val ? 0 : val);
          }
          break;
        }
        case '0':
          if (onSetRating && currentPhoto) {
            onSetRating(currentPhoto.id, 0);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPhoto, goToNext, goToPrev, onClose, onToggleFavorite, onRotatePhoto, onSetRating]);

  // Auto-scroll active thumbnail into view in the filmstrip
  useEffect(() => {
    if (!filmstripRef.current || currentIndex === -1) return;
    const container = filmstripRef.current;
    const item = container.children[currentIndex] as HTMLElement | undefined;
    if (item) {
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [currentIndex]);

  if (!currentPhoto) return null;

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || zoom <= 1) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const toggleZoom = () => {
    if (zoom > 1) {
      setZoom(1);
      setPan({ x: 0, y: 0 });
    } else {
      setZoom(2.2);
    }
    sound.playPop();
  };

  return (
    <div
      onClick={onClose}
      onMouseUp={handleMouseUp}
      className="fixed inset-0 z-50 bg-black/90 backdrop-blur-2xl flex flex-col justify-between select-none overflow-hidden"
    >
      {/* Top Floating Control Bar */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="h-16 px-6 flex items-center justify-between text-white bg-gradient-to-b from-black/70 via-black/30 to-transparent z-10"
      >
        {/* Left: Counter & Filename */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-white/70 lowercase">
            {currentIndex >= 0 ? `${currentIndex + 1} of ${photos.length}` : 'photo'}
          </span>
          <span className="text-white/30">•</span>
          <span className="text-xs font-medium text-white/90 truncate max-w-[240px] lowercase">
            {currentPhoto.filename}
          </span>
        </div>

        {/* Center: In-Lightbox Ratings & Favorite */}
        <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white/10 shadow-lg">
          {/* Favorite button */}
          <button
            onClick={(e) => {
              if (onToggleFavorite) onToggleFavorite(e, currentPhoto.id);
            }}
            className={`p-1 rounded-full transition-transform hover:scale-110 ${
              currentPhoto.is_favorite ? 'text-rose-500' : 'text-white/70 hover:text-white'
            }`}
            title="favorite (f)"
          >
            <Heart className={`w-4 h-4 ${currentPhoto.is_favorite ? 'fill-rose-500' : ''}`} />
          </button>

          <div className="w-[1px] h-3.5 bg-white/20" />

          {/* Star rating buttons */}
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => {
                  if (onSetRating) {
                    onSetRating(currentPhoto.id, currentPhoto.rating === star ? 0 : star);
                  }
                }}
                className="p-0.5 hover:scale-125 transition-transform"
                title={`rate ${star} (press ${star})`}
              >
                <Star
                  className={`w-3.5 h-3.5 ${
                    (currentPhoto.rating || 0) >= star
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-white/30 hover:text-white/70'
                  }`}
                />
              </button>
            ))}
          </div>

          <div className="w-[1px] h-3.5 bg-white/20" />

          {/* Rotate button */}
          <button
            onClick={() => {
              if (onRotatePhoto) onRotatePhoto(currentPhoto.id);
            }}
            className="p-1 rounded-full text-white/70 hover:text-white hover:scale-110 transition-transform"
            title="rotate 90° (r)"
          >
            <RotateCw className="w-4 h-4" />
          </button>

          {/* Zoom toggle */}
          <button
            onClick={toggleZoom}
            className={`p-1 rounded-full transition-transform hover:scale-110 ${
              zoom > 1 ? 'text-[#0071E3]' : 'text-white/70 hover:text-white'
            }`}
            title={zoom > 1 ? 'fit to screen (z)' : 'zoom 200% (z)'}
          >
            {zoom > 1 ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>

        {/* Right: Info toggle & Close */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setShowInfo((prev) => !prev);
              sound.playPop();
            }}
            className={`p-2 rounded-full transition-all ${
              showInfo
                ? 'bg-[#0071E3] text-white'
                : 'bg-white/10 hover:bg-white/20 text-white/80'
            }`}
            title="toggle info (i)"
          >
            <Info className="w-4 h-4" />
          </button>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-all"
            title="close (esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Center Area: Photo + Floating Nav Chevrons + Info Drawer */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex-1 relative flex items-center justify-center overflow-hidden px-4"
      >
        {/* Left Arrow Button */}
        {photos.length > 1 && (
          <button
            onClick={goToPrev}
            className="absolute left-6 z-20 p-3 rounded-full bg-black/40 hover:bg-black/70 backdrop-blur-md text-white/80 hover:text-white transition-all hover:scale-110 shadow-xl border border-white/10"
            title="previous (left arrow)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        )}

        {/* The Photo */}
        <div
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onDoubleClick={toggleZoom}
          className={`max-w-full max-h-full flex items-center justify-center transition-transform duration-100 ${
            zoom > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-zoom-in'
          }`}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          }}
        >
          <img
            src={resolveMediaUrl(currentPhoto.original_url || currentPhoto.preview_url)}
            alt={currentPhoto.filename}
            style={{
              transform: currentPhoto.rotation ? `rotate(${currentPhoto.rotation}deg)` : undefined,
            }}
            className="max-h-[70vh] max-w-[85vw] rounded-2xl object-contain shadow-2xl transition-all duration-200"
          />
        </div>

        {/* Right Arrow Button */}
        {photos.length > 1 && (
          <button
            onClick={goToNext}
            className="absolute right-6 z-20 p-3 rounded-full bg-black/40 hover:bg-black/70 backdrop-blur-md text-white/80 hover:text-white transition-all hover:scale-110 shadow-xl border border-white/10"
            title="next (right arrow)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}

        {/* Overlaid Info Drawer (toggled with 'i') */}
        {showInfo && (
          <div
            onClick={(e) => e.stopPropagation()}
            className="absolute right-6 top-6 bottom-6 w-84 bg-black/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-5 text-white overflow-y-auto z-30 shadow-2xl space-y-4 no-scrollbar lowercase"
          >
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <span className="text-xs font-semibold text-white/90">photo info</span>
              <button
                onClick={() => setShowInfo(false)}
                className="p-1 rounded-full hover:bg-white/10 text-white/60 hover:text-white transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Basic details */}
            <div className="space-y-1.5 text-xs">
              <p className="font-semibold text-white truncate">{currentPhoto.filename}</p>
              <p className="text-white/60 text-[11px]">
                {currentPhoto.width} × {currentPhoto.height} px • {(currentPhoto.file_size / (1024 * 1024)).toFixed(1)} mb
              </p>
              {currentPhoto.date_taken && (
                <p className="text-white/50 text-[11px]">{currentPhoto.date_taken}</p>
              )}
            </div>

            {/* Camera Capsule */}
            {(currentPhoto.camera_make || currentPhoto.camera_model) && (
              <div className="p-3 rounded-2xl bg-white/10 border border-white/10 space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs text-white/90 font-medium">
                  <Camera className="w-3.5 h-3.5 text-[#0071E3]" />
                  <span>{currentPhoto.camera_make} {currentPhoto.camera_model}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[10px] text-white/60 pt-1 border-t border-white/10">
                  {currentPhoto.aperture && <div>f/{currentPhoto.aperture}</div>}
                  {currentPhoto.shutter_speed && <div>{currentPhoto.shutter_speed}s</div>}
                  {currentPhoto.iso && <div>iso {currentPhoto.iso}</div>}
                </div>
              </div>
            )}

            {/* Detected People & Pets */}
            {currentPhoto.subjects.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-white/70">people & pets</span>
                <div className="flex flex-wrap gap-1.5">
                  {currentPhoto.subjects.map((s) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#0071E3] text-[11px] font-medium"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>{s.display_name.toLowerCase()}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {currentPhoto.tags.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-white/70">tags</span>
                <div className="flex flex-wrap gap-1.5">
                  {currentPhoto.tags.slice(0, 10).map((t) => (
                    <span
                      key={t.id}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-white/15 text-[11px] text-white/80"
                    >
                      <Tag className="w-2.5 h-2.5 opacity-60" />
                      <span>#{t.name.toLowerCase()}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Live Text OCR */}
            {currentPhoto.ocr_text && (
              <div className="p-3 rounded-2xl bg-white/10 border border-white/10 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-white/70">text found</span>
                  <button
                    onClick={() => {
                      navigator.clipboard?.writeText(currentPhoto.ocr_text || '');
                      setCopiedOcr(true);
                      setTimeout(() => setCopiedOcr(false), 1500);
                    }}
                    className="flex items-center gap-1 text-[10px] text-white/70 hover:text-white"
                  >
                    {copiedOcr ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedOcr ? 'copied' : 'copy'}</span>
                  </button>
                </div>
                <p className="text-[11px] text-white/80 leading-relaxed font-mono bg-black/30 p-2 rounded-xl max-h-24 overflow-y-auto">
                  {currentPhoto.ocr_text}
                </p>
              </div>
            )}

            {/* Reveal in Explorer */}
            {onRevealInExplorer && (
              <button
                onClick={() => onRevealInExplorer(currentPhoto.id)}
                className="w-full flex items-center justify-center gap-2 py-2 rounded-2xl bg-white/15 hover:bg-white/25 text-xs font-medium text-white transition-colors"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span>show file in explorer</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Bottom Filmstrip Scrubber */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="h-20 px-6 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex items-center justify-center z-10"
      >
        <div
          ref={filmstripRef}
          className="flex items-center gap-2 overflow-x-auto max-w-4xl py-2 px-3 no-scrollbar"
        >
          {photos.map((p, idx) => {
            const isCurrent = p.id === currentPhoto.id;
            return (
              <div
                key={p.id}
                onClick={() => {
                  setZoom(1);
                  setPan({ x: 0, y: 0 });
                  onSelectPhoto(p);
                  sound.playPop();
                }}
                className={`relative shrink-0 w-12 h-12 rounded-xl overflow-hidden cursor-pointer transition-all duration-150 ${
                  isCurrent
                    ? 'ring-2 ring-[#0071E3] scale-110 shadow-lg'
                    : 'opacity-50 hover:opacity-100 hover:scale-105'
                }`}
              >
                <img
                  src={resolveMediaUrl(p.thumbnail_url)}
                  alt=""
                  className="w-full h-full object-cover"
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
