import React, { useState } from 'react';
import {
  X,
  Sparkles,
  Tag,
  Plus,
  FolderOpen,
  RefreshCw,
  Edit3,
  Check,
  Maximize2,
  Camera,
  Calendar,
  HardDrive,
  Layers,
  Trash2,
  User,
  FileText,
  Copy,
  CheckCheck,
  Gamepad2,
  Star,
  RotateCw,
  RotateCcw,
} from 'lucide-react';
import { PhotoItem, PhotoSubjectInfo } from '../../types';
import { resolveMediaUrl } from '../../api/client';
import { NavMode } from '../layout/Sidebar';
import { Histogram } from './Histogram';
import { sound } from '../../utils/sound';

interface InspectorPanelProps {
  photo: PhotoItem | null;
  onClose: () => void;
  onOpenLightbox: (photo: PhotoItem) => void;
  onRenameSubject: (subjectId: number, newName: string, category?: string) => Promise<void>;
  onReassignPhotoSubject: (psId: number, newName: string, category?: string) => Promise<void>;
  onAddTag: (photoId: number, tagName: string) => Promise<void>;
  onRemoveTag: (photoId: number, tagId: number) => Promise<void>;
  onReanalyzePhoto: (photoId: number) => Promise<void>;
  onRevealInExplorer: (photoId: number) => Promise<void>;
  onDeletePhoto: (photoId: number) => Promise<void>;
  onFilterBySubject: (subjectId: number) => void;
  onFilterByTag: (tagName: string) => void;
  onSelectNav: (mode: NavMode) => void;
  onSetRating?: (photoId: number, rating: number) => void;
  onRotatePhoto?: (photoId: number, degrees: number) => void;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  photo,
  onClose,
  onOpenLightbox,
  onRenameSubject,
  onReassignPhotoSubject,
  onAddTag,
  onRemoveTag,
  onReanalyzePhoto,
  onRevealInExplorer,
  onDeletePhoto,
  onFilterBySubject,
  onFilterByTag,
  onSelectNav,
  onSetRating,
  onRotatePhoto,
}) => {
  const [showBbox, setShowBbox] = useState(true);
  const [editingSubjectId, setEditingSubjectId] = useState<number | null>(null);
  const [reassigningPsId, setReassigningPsId] = useState<number | null>(null);
  const [subjectNameInput, setSubjectNameInput] = useState('');
  const [newTagInput, setNewTagInput] = useState('');
  const [reanalyzing, setReanalyzing] = useState(false);
  const [copiedOcr, setCopiedOcr] = useState(false);

  const handleCopyOcr = () => {
    if (!photo?.ocr_text) return;
    navigator.clipboard.writeText(photo.ocr_text);
    setCopiedOcr(true);
    setTimeout(() => setCopiedOcr(false), 1800);
  };

  if (!photo) {
    return (
      <aside className="w-80 lg:w-96 h-full bg-white/90 backdrop-blur-2xl border-l border-black/[0.06] p-6 flex flex-col items-center justify-center text-center select-none shrink-0">
        <div className="w-12 h-12 rounded-2xl bg-[#F5F5F7] text-[#86868B] flex items-center justify-center mb-3">
          <Sparkles className="w-5 h-5" />
        </div>
        <p className="text-sm font-medium text-[#1D1D1F] lowercase">nothing selected</p>
        <p className="text-xs text-[#86868B] mt-1 lowercase">
          click a photo to see details about it.
        </p>
      </aside>
    );
  }

  const rs = photo.root_systems;
  const identityTags = photo.tags.filter((t) => t.tag_type === 'identity');
  const categoryTags = photo.tags.filter((t) => t.tag_type === 'category');
  const otherTags = photo.tags.filter(
    (t) => t.tag_type !== 'identity' && t.tag_type !== 'category'
  );

  const handleSaveClusterRename = async (subj: PhotoSubjectInfo) => {
    if (!subjectNameInput.trim()) return;
    await onRenameSubject(subj.subject_id, subjectNameInput.trim(), subj.category);
    setEditingSubjectId(null);
  };

  const handleSavePhotoReassign = async (subj: PhotoSubjectInfo) => {
    if (!subjectNameInput.trim()) return;
    await onReassignPhotoSubject(subj.id, subjectNameInput.trim(), subj.category);
    setReassigningPsId(null);
  };

  const handleAddCustomTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagInput.trim()) return;
    await onAddTag(photo.id, newTagInput.trim());
    setNewTagInput('');
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      await onReanalyzePhoto(photo.id);
    } finally {
      setReanalyzing(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 kb';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} kb`;
    return `${(kb / 1024).toFixed(2)} mb`;
  };

  return (
    <aside className="w-80 lg:w-96 h-full bg-white/95 backdrop-blur-2xl border-l border-black/[0.06] flex flex-col select-none shrink-0 z-20">
      {/* Header */}
      <div className="h-14 px-5 flex items-center justify-between border-b border-black/[0.05]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#0071E3]" />
          <span className="text-sm font-semibold text-[#1D1D1F] lowercase">info</span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-full hover:bg-[#F5F5F7] text-[#86868B] hover:text-[#1D1D1F]"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Image Preview with Interactive Subject Bounding Box */}
        <div className="space-y-2">
          <div className="relative rounded-2xl overflow-hidden bg-[#F5F5F7] border border-black/[0.06] group">
            <img
              src={resolveMediaUrl(photo.preview_url)}
              alt={photo.filename}
              style={{
                transform: photo.rotation ? `rotate(${photo.rotation}deg)` : undefined,
              }}
              className="w-full max-h-60 object-contain mx-auto transition-transform duration-200"
            />

            {showBbox &&
              photo.subjects.map((s) => {
                const [ymin, xmin, ymax, xmax] = s.bbox;
                return (
                  <div
                    key={s.id}
                    style={{
                      top: `${ymin * 100}%`,
                      left: `${xmin * 100}%`,
                      height: `${(ymax - ymin) * 100}%`,
                      width: `${(xmax - xmin) * 100}%`,
                    }}
                    className="absolute border-2 border-[#0071E3] rounded-xl bg-[#0071E3]/10 pointer-events-none transition-all"
                  >
                    <span className="absolute -top-6 left-0 px-2 py-0.5 rounded-md bg-[#0071E3] text-white text-[10px] font-semibold shadow-xs whitespace-nowrap lowercase">
                      {s.display_name} ({s.category}) • {Math.round(s.confidence * 100)}%
                    </span>
                  </div>
                );
              })}

            <button
              onClick={() => onOpenLightbox(photo)}
              className="absolute bottom-2.5 right-2.5 p-2 rounded-full bg-black/50 hover:bg-black/70 text-white backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity"
              title="open fullscreen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {photo.subjects.length > 0 && (
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] text-[#86868B] lowercase">
                {photo.subjects.length} detected
              </span>
              <button
                onClick={() => setShowBbox(!showBbox)}
                className="text-[11px] font-medium text-[#0071E3] hover:underline lowercase"
              >
                {showBbox ? 'hide boxes' : 'show boxes'}
              </button>
            </div>
          )}
        </div>

        {/* Rating, Rotation & Aspect Ratio Strip */}
        <div className="p-3 rounded-2xl bg-[#F5F5F7] border border-black/[0.04] flex items-center justify-between gap-2">
          {/* 5-Star Rating */}
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => {
                  sound.playPop();
                  const newRating = (photo.rating || 0) === star ? 0 : star;
                  if (onSetRating) onSetRating(photo.id, newRating);
                }}
                className="p-0.5 text-neutral-300 hover:text-amber-400 hover:scale-110 transition-all"
                title={`rate ${star} (${star})`}
              >
                <Star
                  className={`w-4 h-4 ${
                    (photo.rating || 0) >= star
                      ? 'text-amber-400 fill-amber-400'
                      : ''
                  }`}
                />
              </button>
            ))}
            {(photo.rating || 0) > 0 && (
              <span className="text-[10px] font-bold text-amber-600 ml-1">
                {photo.rating}★
              </span>
            )}
          </div>

          {/* Rotate buttons & Specs */}
          <div className="flex items-center gap-1.5">
            {photo.width > 0 && photo.height > 0 && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white border border-black/10 text-[#1D1D1F] lowercase">
                {((photo.width * photo.height) / 1000000).toFixed(1)} mp
              </span>
            )}
            {onRotatePhoto && (
              <div className="flex items-center gap-0.5">
                <button
                  onClick={() => {
                    sound.playPop();
                    onRotatePhoto(photo.id, -90);
                  }}
                  className="p-1 rounded-lg hover:bg-black/5 text-[#86868B] hover:text-[#1D1D1F] transition-colors"
                  title="rotate left"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    sound.playPop();
                    onRotatePhoto(photo.id, 90);
                  }}
                  className="p-1 rounded-lg hover:bg-black/5 text-[#86868B] hover:text-[#1D1D1F] transition-colors"
                  title="rotate right (r)"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Dynamic RGB & Luminance Histogram */}
        <Histogram imageUrl={photo.thumbnail_url} />

        {/* ROOTS CARD */}
        {rs && (
          <div className="p-4 rounded-2xl bg-[#F5F5F7]/90 border border-black/[0.06] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold lowercase tracking-wider text-[#1D1D1F] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[#0071E3]" />
                <span>roots</span>
              </span>
              <button
                onClick={() => onSelectNav({ type: 'roots' })}
                className="text-[11px] font-medium text-[#0071E3] hover:underline lowercase"
              >
                tree view
              </button>
            </div>

            {/* 1. Type Root */}
            <div className="p-2.5 rounded-xl bg-white border border-black/[0.04] space-y-1">
              <span className="text-[10px] font-semibold lowercase tracking-wider text-[#0071E3]">
                1. type
              </span>
              <div className="flex flex-wrap items-center gap-1 text-xs font-semibold text-[#1D1D1F]">
                <button
                  onClick={() =>
                    photo.subjects[0]
                      ? onFilterBySubject(photo.subjects[0].subject_id)
                      : onFilterByTag(rs.type_root.category.toLowerCase())
                  }
                  className="px-2 py-0.5 rounded-md bg-[#0071E3]/10 text-[#0071E3] hover:bg-[#0071E3] hover:text-white transition-colors lowercase"
                >
                  {rs.type_root.specific}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'category',
                      category: rs.type_root.category.toLowerCase(),
                      label: `category: ${rs.type_root.category.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-[#F5F5F7] hover:bg-[#E8E8ED] lowercase"
                >
                  {rs.type_root.category}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'super_type',
                      super_type: rs.type_root.super_type,
                      label: `type: ${rs.type_root.super_type.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-[#F5F5F7] hover:bg-[#E8E8ED] lowercase"
                >
                  {rs.type_root.super_type}
                </button>
              </div>
            </div>

            {/* 2. Drive Root */}
            <div className="p-2.5 rounded-xl bg-white border border-black/[0.04] space-y-1">
              <span className="text-[10px] font-semibold lowercase tracking-wider text-emerald-600">
                2. folder
              </span>
              <div className="flex flex-wrap items-center gap-1 text-xs font-semibold text-[#1D1D1F]">
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'drive_hierarchy',
                      drive_root: rs.drive_root.drive,
                      folder_name: rs.drive_root.folder,
                      subfolder_name: rs.drive_root.subfolder,
                      label: `${rs.drive_root.subfolder.toLowerCase()} → ${rs.drive_root.folder.toLowerCase()} → ${rs.drive_root.drive.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-700 hover:bg-emerald-600 hover:text-white transition-colors lowercase"
                >
                  {rs.drive_root.subfolder}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'drive_hierarchy',
                      drive_root: rs.drive_root.drive,
                      folder_name: rs.drive_root.folder,
                      label: `${rs.drive_root.folder.toLowerCase()} → ${rs.drive_root.drive.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-[#F5F5F7] hover:bg-[#E8E8ED] lowercase"
                >
                  {rs.drive_root.folder}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'drive_hierarchy',
                      drive_root: rs.drive_root.drive,
                      label: `drive (${rs.drive_root.drive.toLowerCase()})`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-[#F5F5F7] hover:bg-[#E8E8ED] lowercase"
                >
                  {rs.drive_root.drive}
                </button>
              </div>
            </div>

            {/* 3. Device Root */}
            <div className="p-2.5 rounded-xl bg-white border border-black/[0.04] space-y-1">
              <span className="text-[10px] font-semibold lowercase tracking-wider text-purple-600">
                3. device
              </span>
              <div className="flex flex-wrap items-center gap-1 text-xs font-semibold text-[#1D1D1F]">
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'device_hierarchy',
                      device_name: rs.device_root.device,
                      label: `device: ${rs.device_root.device.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-700 hover:bg-purple-600 hover:text-white transition-colors lowercase"
                >
                  {rs.device_root.device}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'device_hierarchy',
                      device_name: rs.device_root.device,
                      capture_date: rs.device_root.capture_date,
                      label: `${rs.device_root.device.toLowerCase()} • ${rs.device_root.capture_date}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-[#F5F5F7] hover:bg-[#E8E8ED] lowercase"
                >
                  {rs.device_root.date_taken}
                </button>
                <span className="text-[#86868B]">→</span>
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'device_hierarchy',
                      image_type: rs.device_root.image_type,
                      label: `format: ${rs.device_root.image_type.toLowerCase()}`,
                    })
                  }
                  className="px-2 py-0.5 rounded-md bg-purple-600 text-white lowercase"
                >
                  {rs.device_root.image_type}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Identified Subject / Pet Identity Section */}
        {photo.subjects.length > 0 && (
          <div className="space-y-2.5">
            <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
              subjects
            </p>
            {photo.subjects.map((subj) => {
              const isRenamingCluster = editingSubjectId === subj.subject_id;
              const isReassigningPhoto = reassigningPsId === subj.id;

              return (
                <div
                  key={subj.id}
                  className="p-3.5 rounded-2xl bg-white border border-black/[0.08] shadow-2xs space-y-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div
                      onClick={() => onFilterBySubject(subj.subject_id)}
                      className="flex items-center gap-3 cursor-pointer group"
                    >
                      {subj.crop_url && (
                        <img
                          src={resolveMediaUrl(subj.crop_url)}
                          alt={subj.display_name}
                          className="w-11 h-11 rounded-full object-cover ring-2 ring-[#0071E3]/30"
                        />
                      )}
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-bold text-[#1D1D1F] group-hover:text-[#0071E3] lowercase">
                            {subj.display_name}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F5F5F7] text-[#1D1D1F] font-semibold lowercase">
                            {subj.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#86868B] lowercase">
                          {subj.is_named
                            ? `${subj.display_name.toLowerCase()} → ${subj.category.toLowerCase()} → ${(subj.super_type || 'animal').toLowerCase()}`
                            : `unnamed ${subj.category}`}
                        </p>
                      </div>
                    </div>
                  </div>

                  {!isRenamingCluster && !isReassigningPhoto && (
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => {
                          setEditingSubjectId(subj.subject_id);
                          setReassigningPsId(null);
                          setSubjectNameInput(subj.subject_name || '');
                        }}
                        className="flex-1 flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-medium transition-colors lowercase"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>{subj.is_named ? 'rename' : 'name this'}</span>
                      </button>
                      <button
                        onClick={() => {
                          setReassigningPsId(subj.id);
                          setEditingSubjectId(null);
                          setSubjectNameInput('');
                        }}
                        className="px-2.5 py-1.5 rounded-xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-[#1D1D1F] text-xs font-medium transition-colors lowercase"
                        title="different one?"
                      >
                        not {subj.display_name}?
                      </button>
                    </div>
                  )}

                  {(isRenamingCluster || isReassigningPhoto) && (
                    <div className="pt-2 border-t border-black/[0.05] space-y-2">
                      <p className="text-[11px] font-medium text-[#86868B] lowercase">
                        {isRenamingCluster
                          ? `name this ${subj.category}:`
                          : `change name for this photo:`}
                      </p>
                      <div className="flex items-center gap-1.5">
                        <input
                          type="text"
                          value={subjectNameInput}
                          onChange={(e) => setSubjectNameInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              isRenamingCluster
                                ? handleSaveClusterRename(subj)
                                : handleSavePhotoReassign(subj);
                            }
                          }}
                          placeholder="type name..."
                          autoFocus
                          className="flex-1 px-2.5 py-1.5 text-xs font-medium bg-[#F5F5F7] rounded-xl border border-[#0071E3] outline-none lowercase"
                        />
                        <button
                          onClick={() =>
                            isRenamingCluster
                              ? handleSaveClusterRename(subj)
                              : handleSavePhotoReassign(subj)
                          }
                          className="p-1.5 rounded-xl bg-[#0071E3] text-white"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setEditingSubjectId(null);
                            setReassigningPsId(null);
                          }}
                          className="p-1.5 rounded-xl bg-[#F5F5F7] text-[#86868B]"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Hierarchical Tags Section */}
        <div className="space-y-3">
          <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
            tags
          </p>

          {identityTags.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-medium text-[#86868B] lowercase">
                names
              </span>
              <div className="flex flex-wrap gap-1.5">
                {identityTags.map((t) => (
                  <span
                    key={t.id}
                    onClick={() => onFilterByTag(t.name)}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#0071E3] text-white cursor-pointer shadow-2xs lowercase"
                  >
                    <span>#{t.name.toLowerCase()}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {categoryTags.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-medium text-[#86868B] lowercase">
                categories
              </span>
              <div className="flex flex-wrap gap-1.5">
                {categoryTags.map((t) => (
                  <span
                    key={t.id}
                    onClick={() => onFilterByTag(t.name)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F5F5F7] hover:bg-[#E8E8ED] text-[#1D1D1F] cursor-pointer lowercase"
                  >
                    <Tag className="w-3 h-3 text-[#0071E3]" />
                    <span>{t.name.toLowerCase()}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveTag(photo.id, t.id);
                      }}
                      className="ml-0.5 text-[#86868B] hover:text-rose-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {otherTags.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-medium text-[#86868B] lowercase">
                attributes
              </span>
              <div className="flex flex-wrap gap-1.5">
                {otherTags.map((t) => (
                  <span
                    key={t.id}
                    onClick={() => onFilterByTag(t.name)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F5F5F7]/70 hover:bg-[#E8E8ED] text-[#86868B] hover:text-[#1D1D1F] cursor-pointer lowercase"
                  >
                    <span>{t.name.toLowerCase()}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveTag(photo.id, t.id);
                      }}
                      className="ml-0.5 hover:text-rose-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleAddCustomTag} className="flex items-center gap-1.5 pt-1">
            <input
              type="text"
              value={newTagInput}
              onChange={(e) => setNewTagInput(e.target.value)}
              placeholder="add a tag..."
              className="flex-1 px-3 py-1.5 text-xs bg-[#F5F5F7] rounded-xl border border-transparent focus:border-[#0071E3] focus:bg-white outline-none lowercase"
            />
            <button
              type="submit"
              className="p-1.5 rounded-xl bg-[#F5F5F7] hover:bg-[#0071E3] hover:text-white text-[#1D1D1F] transition-colors"
              title="add tag"
            >
              <Plus className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* XMP Sidecar Status & Inspection */}
        <div className="p-3.5 rounded-2xl bg-[#F5F5F7]/80 border border-black/[0.04] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold lowercase tracking-wider text-[#1D1D1F] flex items-center gap-1.5">
              <span>sidecar file</span>
            </span>
            <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full lowercase">
              active
            </span>
          </div>
          <p className="text-[11px] text-[#86868B] leading-relaxed lowercase">
            saved in a <code className="font-mono text-[10px] bg-white px-1 py-0.5 rounded border">.xmp</code> file next to the photo.
          </p>
        </div>

        {/* Detected Faces */}
        {(photo.face_count || 0) > 0 && (
          <div className="p-3.5 rounded-2xl bg-[#007AFF]/5 border border-[#007AFF]/15 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold lowercase tracking-wider text-[#1C1C1E] flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-[#007AFF]" />
                <span>faces found</span>
              </span>
              <span className="text-[10px] font-semibold text-[#007AFF] bg-[#007AFF]/10 px-2 py-0.5 rounded-full lowercase">
                {photo.face_count} {photo.face_count === 1 ? 'face' : 'faces'}
              </span>
            </div>
            <p className="text-[11px] text-[#8E8E93] leading-relaxed lowercase">
              found {photo.face_count} face{photo.face_count === 1 ? '' : 's'} in this image.
            </p>
          </div>
        )}

        {/* Live Text (OCR) Section */}
        {photo.ocr_text && (
          <div className="p-3.5 rounded-2xl bg-amber-500/5 border border-amber-500/15 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold lowercase tracking-wider text-[#1C1C1E] flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-amber-600" />
                <span>text found in photo</span>
              </span>
              <button
                onClick={handleCopyOcr}
                className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-700 bg-amber-500/10 hover:bg-amber-500/20 px-2 py-0.5 rounded-md transition-colors lowercase"
                title="copy text"
              >
                {copiedOcr ? (
                  <>
                    <CheckCheck className="w-3 h-3 text-emerald-600" />
                    <span className="text-emerald-700">copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>copy</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-[11px] text-[#1D1D1F] bg-white/70 p-2 rounded-xl border border-black/[0.04] leading-relaxed font-mono select-text break-words">
              {photo.ocr_text}
            </p>
          </div>
        )}

        {/* Video Game Asset Notice */}
        {photo.is_game_asset && (
          <div className="p-3.5 rounded-2xl bg-purple-500/10 border border-purple-500/20 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold lowercase tracking-wider text-purple-900 flex items-center gap-1.5">
                <Gamepad2 className="w-3.5 h-3.5 text-purple-700" />
                <span>game file</span>
              </span>
              <span className="text-[10px] font-semibold text-purple-700 bg-purple-200/60 px-2 py-0.5 rounded-full lowercase">
                game asset
              </span>
            </div>
            <p className="text-[11px] text-purple-950/80 leading-relaxed lowercase">
              looks like a game screenshot or asset. you can hide these in settings.
            </p>
          </div>
        )}

        {/* Camera Optics Capsule */}
        <div className="p-3.5 rounded-2xl bg-gradient-to-br from-white to-[#F5F5F7] border border-black/[0.06] shadow-2xs space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-black/5 flex items-center justify-center text-[#1D1D1F]">
                <Camera className="w-3.5 h-3.5" />
              </div>
              <div>
                <span className="text-xs font-bold text-[#1D1D1F] lowercase">
                  {photo.camera_model || photo.device_name || 'camera'}
                </span>
                {photo.camera_make && photo.camera_make !== photo.camera_model && (
                  <p className="text-[10px] text-[#86868B] lowercase">{photo.camera_make}</p>
                )}
              </div>
            </div>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-black/5 text-[#1D1D1F] lowercase">
              {photo.image_type.toLowerCase()}
            </span>
          </div>

          {(photo.focal_length || photo.aperture || photo.shutter_speed || photo.iso) && (
            <div className="grid grid-cols-4 gap-1.5 pt-1 text-center font-mono">
              <div className="p-1.5 rounded-xl bg-black/[0.03]">
                <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">lens</span>
                <span className="text-[11px] font-bold text-[#1D1D1F] lowercase">{photo.focal_length || '—'}</span>
              </div>
              <div className="p-1.5 rounded-xl bg-black/[0.03]">
                <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">aperture</span>
                <span className="text-[11px] font-bold text-[#1D1D1F] lowercase">{photo.aperture ? `ƒ/${photo.aperture}` : '—'}</span>
              </div>
              <div className="p-1.5 rounded-xl bg-black/[0.03]">
                <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">shutter</span>
                <span className="text-[11px] font-bold text-[#1D1D1F] lowercase">{photo.shutter_speed ? `${photo.shutter_speed}s` : '—'}</span>
              </div>
              <div className="p-1.5 rounded-xl bg-black/[0.03]">
                <span className="block text-[9px] lowercase tracking-wider text-[#86868B]">iso</span>
                <span className="text-[11px] font-bold text-[#1D1D1F] lowercase">{photo.iso ? `iso ${photo.iso}` : '—'}</span>
              </div>
            </div>
          )}
        </div>

        {/* File & Storage Details */}
        <div className="space-y-2.5 pt-2 border-t border-black/[0.06]">
          <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
            file info
          </p>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[#86868B] flex items-center gap-1.5 lowercase">
                <Calendar className="w-3.5 h-3.5" /> date taken
              </span>
              <span className="font-medium text-[#1D1D1F] lowercase">{photo.date_taken || 'no timestamp'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#86868B] flex items-center gap-1.5 lowercase">
                <HardDrive className="w-3.5 h-3.5" /> size & format
              </span>
              <span className="font-medium text-[#1D1D1F] lowercase">
                {photo.image_type.toLowerCase()} • {photo.width}×{photo.height} ({formatBytes(photo.file_size)})
              </span>
            </div>
            <div className="pt-1">
              <p className="text-[10px] text-[#86868B] break-all bg-[#F5F5F7] p-2 rounded-xl lowercase">
                {photo.path}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button
              onClick={() => onRevealInExplorer(photo.id)}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-xs font-medium text-[#1D1D1F] transition-colors lowercase"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              <span>show file</span>
            </button>
            <button
              onClick={handleReanalyze}
              disabled={reanalyzing}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-[#F5F5F7] hover:bg-[#E8E8ED] text-xs font-medium text-[#1D1D1F] transition-colors lowercase"
              title="re-scan"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reanalyzing ? 'animate-spin' : ''}`} />
              <span>re-scan</span>
            </button>
            <button
              onClick={() => onDeletePhoto(photo.id)}
              className="p-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 transition-colors"
              title="remove"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
