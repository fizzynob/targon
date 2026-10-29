import React, { useState } from 'react';
import { Edit3, Check, X, GitMerge, Sparkles, ArrowRight } from 'lucide-react';
import { SubjectItem } from '../../types';
import { resolveMediaUrl } from '../../api/client';

interface PeopleAndPetsViewProps {
  subjects: SubjectItem[];
  onSelectSubject: (subject: SubjectItem) => void;
  onRenameSubject: (subjectId: number, newName: string) => Promise<void>;
  onMergeSubjects: (sourceId: number, targetId: number) => Promise<void>;
}

export const PeopleAndPetsView: React.FC<PeopleAndPetsViewProps> = ({
  subjects,
  onSelectSubject,
  onRenameSubject,
  onMergeSubjects,
}) => {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [nameInput, setNameInput] = useState('');
  const [mergingSourceId, setMergingSourceId] = useState<number | null>(null);

  const namedSubjects = subjects.filter((s) => s.is_named);
  const unnamedSubjects = subjects.filter((s) => !s.is_named);

  const startRename = (e: React.MouseEvent, subj: SubjectItem) => {
    e.stopPropagation();
    setEditingId(subj.id);
    setNameInput(subj.name || '');
  };

  const saveRename = async (e: React.MouseEvent, subjId: number) => {
    e.stopPropagation();
    if (!nameInput.trim()) return;
    await onRenameSubject(subjId, nameInput.trim());
    setEditingId(null);
  };

  const renderSubjectCard = (subj: SubjectItem) => {
    const isEditing = editingId === subj.id;
    const isMerging = mergingSourceId === subj.id;
    const mergeTargets = subjects.filter(
      (other) => other.id !== subj.id && other.category === subj.category
    );

    return (
      <div
        key={subj.id}
        onClick={() => !isEditing && !isMerging && onSelectSubject(subj)}
        className="group bg-white rounded-3xl p-6 border border-black/[0.06] shadow-apple hover:shadow-appleHover transition-all duration-200 cursor-pointer flex flex-col items-center text-center relative"
      >
        {/* Circular Avatar with Subtle Ring */}
        <div className="relative mb-4">
          {subj.avatar_url ? (
            <img
              src={resolveMediaUrl(subj.avatar_url)}
              alt={subj.display_name}
              className={`w-28 h-28 rounded-full object-cover shadow-md transition-transform duration-300 group-hover:scale-105 ${
                subj.is_named ? 'ring-4 ring-[#0071E3]/20' : 'ring-4 ring-black/[0.06]'
              }`}
            />
          ) : (
            <div className="w-28 h-28 rounded-full bg-[#F5F5F7] flex items-center justify-center text-2xl font-bold text-[#86868B]">
              {subj.display_name[0]}
            </div>
          )}
          <span
            className={`absolute -bottom-1 right-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold lowercase shadow-xs ${
              subj.is_named
                ? 'bg-[#0071E3] text-white'
                : 'bg-white text-[#1D1D1F] border border-black/10'
            }`}
          >
            {subj.category.toLowerCase()}
          </span>
        </div>

        {/* Name or Inline Editor */}
        {isEditing ? (
          <div
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1.5 mt-1 mb-2 w-full justify-center"
          >
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') saveRename(e as unknown as React.MouseEvent, subj.id);
              }}
              placeholder="e.g. blu or marmalade"
              autoFocus
              className="w-36 px-2.5 py-1 text-sm font-semibold bg-[#F5F5F7] rounded-xl border border-[#0071E3] outline-none text-center lowercase"
            />
            <button
              onClick={(e) => saveRename(e, subj.id)}
              className="p-1.5 rounded-lg bg-[#0071E3] text-white"
              title="save name"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setEditingId(null);
              }}
              className="p-1.5 rounded-lg bg-[#F5F5F7] text-[#86868B]"
              title="cancel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="mb-1">
            <h3 className="text-lg font-bold tracking-tight text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors lowercase">
              {subj.display_name.toLowerCase()}
            </h3>
            <p className="text-xs text-[#86868B] mt-0.5">
              {subj.photo_count} {subj.photo_count === 1 ? 'photo' : 'photos'} • tag:{' '}
              <span className="font-medium text-[#1D1D1F]">#{subj.category.toLowerCase()}</span>
            </p>
          </div>
        )}

        {/* Mini Sample Strip */}
        {subj.sample_photos.length > 0 && (
          <div className="flex items-center justify-center gap-1.5 my-3">
            {subj.sample_photos.slice(0, 4).map((url, idx) => (
              <img
                key={idx}
                src={resolveMediaUrl(url)}
                alt=""
                className="w-10 h-10 rounded-lg object-cover border border-black/[0.06]"
              />
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div
          onClick={(e) => e.stopPropagation()}
          className="mt-2 pt-3 border-t border-black/[0.05] w-full flex items-center justify-center gap-2"
        >
          <button
            onClick={(e) => startRename(e, subj)}
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-[#F5F5F7] hover:bg-[#0071E3] hover:text-white text-[#1D1D1F] transition-colors"
          >
            <Edit3 className="w-3 h-3" />
            <span>{subj.is_named ? 'rename' : 'name this'}</span>
          </button>

          {mergeTargets.length > 0 && (
            <button
              onClick={() => setMergingSourceId(isMerging ? null : subj.id)}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-[#F5F5F7] hover:bg-[#E8E8ED] text-[#86868B] hover:text-[#1D1D1F] transition-colors"
              title="combine with another one"
            >
              <GitMerge className="w-3 h-3" />
              <span>combine</span>
            </button>
          )}
        </div>

        {/* Merge Selector Dropdown */}
        {isMerging && (
          <div
            onClick={(e) => e.stopPropagation()}
            className="mt-3 p-3 rounded-2xl bg-[#F5F5F7] w-full text-left space-y-1.5"
          >
            <p className="text-[11px] font-semibold text-[#86868B]">
              combine &ldquo;{subj.display_name.toLowerCase()}&rdquo; with:
            </p>
            {mergeTargets.map((target) => (
              <button
                key={target.id}
                onClick={async () => {
                  await onMergeSubjects(subj.id, target.id);
                  setMergingSourceId(null);
                }}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-white hover:bg-[#0071E3] hover:text-white text-xs font-medium transition-colors"
              >
                <span className="lowercase">{target.display_name.toLowerCase()}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 h-full overflow-y-auto px-10 py-8 space-y-10 bg-[#FBFBFD]">
      {/* Header Explanation Banner */}
      <div className="bg-white rounded-3xl p-7 border border-black/[0.06] shadow-apple flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#0071E3]/10 text-[#0071E3] text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>people & pets</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-[#1D1D1F]">
            people & pets
          </h2>
          <p className="text-sm text-[#86868B] mt-1.5 leading-relaxed">
            groups photos of the same people or pets together. you can give them names or combine them if the app thought they were different.
          </p>
        </div>
      </div>

      {/* Named Subjects */}
      {namedSubjects.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-[#1D1D1F]">named</h3>
            <span className="text-xs text-[#86868B]">{namedSubjects.length} named</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {namedSubjects.map(renderSubjectCard)}
          </div>
        </section>
      )}

      {/* Unnamed Subject Clusters (Discovered by AI) */}
      {unnamedSubjects.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-[#1D1D1F]">
                unnamed
              </h3>
              <p className="text-xs text-[#86868B]">
                photos that look like they might be the same one. click to give them a name.
              </p>
            </div>
            <span className="text-xs text-[#86868B]">{unnamedSubjects.length} groups</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {unnamedSubjects.map(renderSubjectCard)}
          </div>
        </section>
      )}
    </div>
  );
};
