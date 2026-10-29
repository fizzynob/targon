import React from 'react';
import { Heart, User, Check, Gamepad2 } from 'lucide-react';
import { PhotoItem } from '../../types';
import { resolveMediaUrl } from '../../api/client';
import { sound } from '../../utils/sound';

interface PhotoCardProps {
  photo: PhotoItem;
  isSelected: boolean;
  isMultiSelected?: boolean;
  reduceMotion?: boolean;
  showCardTags?: boolean;
  onSelect: (photo: PhotoItem, options: { isMulti: boolean; isRange: boolean }) => void;
  onDoubleClick: (photo: PhotoItem) => void;
  onToggleFavorite: (e: React.MouseEvent, photoId: number) => void;
  onFilterBySubject: (e: React.MouseEvent, subjectId: number) => void;
  onFilterByTag: (e: React.MouseEvent, tagName: string) => void;
  onContextMenu?: (e: React.MouseEvent, photo: PhotoItem) => void;
}

const PhotoCardInner: React.FC<PhotoCardProps> = ({
  photo,
  isSelected,
  isMultiSelected = false,
  reduceMotion = false,
  showCardTags = true,
  onSelect,
  onDoubleClick,
  onToggleFavorite,
  onFilterBySubject,
  onContextMenu,
}) => {
  const primarySubject = photo.subjects[0] || null;
  const faceCount = photo.face_count || 0;

  return (
    <div
      onClick={(e) => {
        sound.playPop();
        onSelect(photo, { isMulti: e.ctrlKey || e.metaKey, isRange: e.shiftKey });
      }}
      onDoubleClick={() => onDoubleClick(photo)}
      onContextMenu={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onContextMenu?.(e, photo);
      }}
      style={{
        contentVisibility: 'auto',
        containIntrinsicSize: '220px 195px',
      }}
      className={`group relative bg-white rounded-2xl overflow-hidden cursor-pointer flex flex-col select-none ${
        reduceMotion ? '' : 'transition-all duration-150'
      } ${
        isSelected || isMultiSelected
          ? 'ring-2 ring-[#0071E3] shadow-md'
          : 'border border-black/[0.06] shadow-xs hover:border-black/[0.14]'
      }`}
    >
      {/* Photo Container */}
      <div
        className="relative w-full aspect-[4/3] overflow-hidden bg-[#F5F5F7]"
        style={{ backgroundColor: photo.dominant_color || '#F5F5F7' }}
      >
        <img
          src={resolveMediaUrl(photo.thumbnail_url)}
          alt={photo.filename}
          loading="lazy"
          decoding="async"
          style={{
            transform: photo.rotation ? `rotate(${photo.rotation}deg)` : undefined,
          }}
          className={`w-full h-full object-cover ${
            reduceMotion
              ? ''
              : 'transition-transform duration-300 ease-out group-hover:scale-102'
          }`}
        />

        {/* Multi-select checkmark circle */}
        <div
          onClick={(e) => {
            e.stopPropagation();
            sound.playPop();
            onSelect(photo, { isMulti: true, isRange: false });
          }}
          className={`absolute top-2.5 left-2.5 w-6 h-6 rounded-full flex items-center justify-center ${
            isMultiSelected || isSelected
              ? 'bg-[#0071E3] text-white opacity-100 shadow-xs'
              : `bg-black/45 text-white opacity-0 group-hover:opacity-100 hover:bg-black/65 ${
                  reduceMotion ? '' : 'backdrop-blur-md transition-all'
                }`
          }`}
        >
          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
        </div>

        {/* Top-Right: Game Asset Pill + Favorite Heart button */}
        <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5">
          {photo.is_game_asset && (
            <span
              className="px-1.5 py-0.5 rounded-full bg-purple-900/85 text-purple-200 text-[10px] font-semibold flex items-center gap-1 shadow-xs lowercase"
              title="game file"
            >
              <Gamepad2 className="w-3 h-3 text-purple-300" />
              <span>game</span>
            </span>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              if (photo.is_favorite) {
                sound.playUnfavorite();
              } else {
                sound.playFavorite();
              }
              onToggleFavorite(e, photo.id);
            }}
            className={`w-6 h-6 rounded-full flex items-center justify-center ${
              photo.is_favorite
                ? 'bg-white/90 text-rose-500 shadow-xs opacity-100'
                : `bg-black/45 text-white opacity-0 group-hover:opacity-100 hover:bg-black/65 ${
                    reduceMotion ? '' : 'backdrop-blur-md transition-all'
                  }`
            }`}
            title="favorite (f)"
          >
            <Heart className={`w-3.5 h-3.5 ${photo.is_favorite ? 'fill-rose-500' : ''}`} />
          </button>
        </div>

        {/* Bottom Bar overlay: Format & Face/Identity */}
        <div
          className={`absolute inset-x-0 bottom-0 p-2.5 bg-gradient-to-t from-black/50 via-black/20 to-transparent flex items-center justify-between text-white text-[11px] font-medium opacity-0 group-hover:opacity-100 lowercase ${
            reduceMotion ? '' : 'transition-opacity'
          }`}
        >
          <div className="flex items-center gap-1.5 truncate">
            {primarySubject && (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  onFilterBySubject(e, primarySubject.subject_id);
                }}
                className="hover:underline truncate flex items-center gap-1 lowercase"
              >
                <span>{primarySubject.display_name}</span>
                {photo.subjects.length > 1 && (
                  <span className="text-[9px] px-1 py-0.2 rounded-full bg-white/25 font-semibold">
                    +{photo.subjects.length - 1}
                  </span>
                )}
              </span>
            )}
            {faceCount > 0 && !primarySubject && (
              <span className="flex items-center gap-1 text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full lowercase">
                <User className="w-2.5 h-2.5" />
                <span>
                  {faceCount} {faceCount === 1 ? 'face' : 'faces'}
                </span>
              </span>
            )}
            {photo.ocr_text && !primarySubject && faceCount === 0 && (
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full truncate max-w-[120px] lowercase">
                text
              </span>
            )}
          </div>
          <span className="text-[10px] font-mono tracking-tight text-white/80 lowercase">
            {photo.image_type.toLowerCase()}
          </span>
        </div>
      </div>

      {/* Clean Subtle Card Sub-Bar */}
      {showCardTags && (
        <div className="px-3 py-2 flex items-center justify-between bg-white text-[11px] border-t border-black/[0.04]">
          <div className="flex items-center gap-1.5 min-w-0">
            {primarySubject ? (
              <span className="font-semibold text-[#1C1C1E] truncate lowercase">
                {primarySubject.display_name}
              </span>
            ) : (
              <span className="text-[#8E8E93] truncate lowercase">{photo.filename}</span>
            )}
            {primarySubject && (
              <span className="text-[10px] text-[#8E8E93] truncate lowercase">
                ({primarySubject.category})
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {(photo.rating || 0) > 0 && (
              <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200/50">
                ★ {photo.rating}
              </span>
            )}
            <span className="text-[10px] text-[#8E8E93] font-medium lowercase">
              {(photo.root_systems?.type_root?.super_type || 'animal').toLowerCase()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export const PhotoCard = React.memo(PhotoCardInner, (prev, next) => {
  return (
    prev.photo === next.photo &&
    prev.isSelected === next.isSelected &&
    prev.isMultiSelected === next.isMultiSelected &&
    prev.reduceMotion === next.reduceMotion &&
    prev.showCardTags === next.showCardTags
  );
});
