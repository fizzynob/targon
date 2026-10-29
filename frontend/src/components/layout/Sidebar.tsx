import React from 'react';
import {
  Images,
  Heart,
  Users,
  HardDrive,
  SlidersHorizontal,
  Plus,
  Sparkles,
  Layers,
  Camera,
  FolderOpen,
  FileImage,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import {
  SubjectItem,
  TagInfo,
  FolderItem,
  LibraryStats,
  ThreeRootTrees,
} from '../../types';
import { resolveMediaUrl } from '../../api/client';
import targonLogo from '../../assets/logo.png';
import { TARGON_LOGO_DATA_URI } from '../../assets/logo_data_uri';

export type NavMode =
  | { type: 'all' }
  | { type: 'roots' }
  | { type: 'favorites' }
  | { type: 'people_pets' }
  | { type: 'subject'; subject: SubjectItem }
  | { type: 'category'; category: string; label: string }
  | { type: 'super_type'; super_type: string; label: string }
  | {
      type: 'drive_hierarchy';
      drive_root?: string;
      folder_name?: string;
      subfolder_name?: string;
      label: string;
    }
  | {
      type: 'device_hierarchy';
      device_name?: string;
      capture_date?: string;
      image_type?: string;
      label: string;
    }
  | { type: 'tag'; tag: string }
  | { type: 'folder'; folder: FolderItem };

interface SidebarProps {
  navMode: NavMode;
  onSelectNav: (mode: NavMode) => void;
  subjects: SubjectItem[];
  tags: TagInfo[];
  folders: FolderItem[];
  roots: ThreeRootTrees;
  stats: LibraryStats;
  onOpenScanModal: () => void;
  onOpenSettingsModal: () => void;
  onOpenClearLibrary: () => void;
  onReanalyzeLibrary?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  navMode,
  onSelectNav,
  subjects,
  roots,
  stats,
  onOpenScanModal,
  onOpenSettingsModal,
  onOpenClearLibrary,
  onReanalyzeLibrary,
}) => {
  const isElectron = Boolean(window.targonDesktop?.isElectron);

  const navBtnClass = (active: boolean) =>
    `w-full flex items-center justify-between px-3 py-2 rounded-xl text-[13px] font-medium transition-all duration-150 ${
      active
        ? 'bg-[#0071E3] text-white shadow-xs'
        : 'text-[#1D1D1F]/85 hover:bg-black/[0.05] hover:text-[#1D1D1F]'
    }`;

  return (
    <aside className="w-64 h-full bg-[#F5F5F7]/90 backdrop-blur-2xl border-r border-black/[0.06] flex flex-col select-none shrink-0 z-30">
      {/* Top Brand + Optional Window Traffic Lights */}
      <div className="h-16 px-5 flex items-center justify-between app-drag-region border-b border-black/[0.04]">
        <div className="flex items-center gap-2.5 app-no-drag">
          {isElectron && (
            <div className="flex items-center gap-2 mr-2">
              <button
                onClick={() => window.targonDesktop?.close()}
                className="w-3 h-3 rounded-full bg-[#FF5F57] border border-black/10 hover:opacity-80"
                title="Close"
              />
              <button
                onClick={() => window.targonDesktop?.minimize()}
                className="w-3 h-3 rounded-full bg-[#FEBC2E] border border-black/10 hover:opacity-80"
                title="Minimize"
              />
              <button
                onClick={() => window.targonDesktop?.maximize()}
                className="w-3 h-3 rounded-full bg-[#28C840] border border-black/10 hover:opacity-80"
                title="Maximize"
              />
            </div>
          )}
          <div className="w-8 h-8 rounded-xl bg-white border border-black/[0.08] p-1 flex items-center justify-center shadow-xs overflow-hidden shrink-0">
            <img
              src={targonLogo}
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = TARGON_LOGO_DATA_URI;
              }}
              alt="targon"
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <span className="text-[15px] font-semibold tracking-tight text-[#1D1D1F] lowercase">
              targon
            </span>
            <span className="ml-1.5 text-[10px] font-medium lowercase px-1.5 py-0.5 rounded bg-black/[0.06] text-[#86868B]">
              local
            </span>
          </div>
        </div>
      </div>

      {/* Scrollable Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-6">
        {/* Library Overview */}
        <div>
          <p className="px-3 mb-1.5 text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
            library
          </p>
          <div className="space-y-0.5">
            <button
              onClick={() => onSelectNav({ type: 'all' })}
              className={navBtnClass(navMode.type === 'all')}
            >
              <span className="flex items-center gap-2.5 lowercase">
                <Images className="w-4 h-4 opacity-85" />
                <span>all photos</span>
              </span>
              <span className="text-[11px] opacity-75">{stats.total_photos}</span>
            </button>

            <button
              onClick={() => onSelectNav({ type: 'roots' })}
              className={navBtnClass(navMode.type === 'roots')}
            >
              <span className="flex items-center gap-2.5 lowercase">
                <Layers className="w-4 h-4 opacity-85" />
                <span>roots</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-black/[0.06] lowercase">
                type • folder • camera
              </span>
            </button>

            <button
              onClick={() => onSelectNav({ type: 'people_pets' })}
              className={navBtnClass(navMode.type === 'people_pets')}
            >
              <span className="flex items-center gap-2.5 lowercase">
                <Users className="w-4 h-4 opacity-85" />
                <span>people & pets</span>
              </span>
              <span className="text-[11px] opacity-75">{subjects.length}</span>
            </button>

            <button
              onClick={() => onSelectNav({ type: 'favorites' })}
              className={navBtnClass(navMode.type === 'favorites')}
            >
              <span className="flex items-center gap-2.5 lowercase">
                <Heart className="w-4 h-4 opacity-85" />
                <span>favorites</span>
              </span>
              <span className="text-[11px] opacity-75">{stats.favorites}</span>
            </button>
          </div>
        </div>

        {/* ROOT 1: TYPE */}
        <div>
          <div className="px-3 mb-2 flex items-center justify-between">
            <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
              1. type
            </p>
            <span className="text-[10px] text-[#86868B] lowercase">what's inside</span>
          </div>

          <div className="space-y-1">
            {subjects.map((subj) => {
              const isActive = navMode.type === 'subject' && navMode.subject.id === subj.id;
              const superLabel = (subj.super_type || 'animal').toLowerCase();
              return (
                <button
                  key={subj.id}
                  onClick={() => onSelectNav({ type: 'subject', subject: subj })}
                  className={navBtnClass(isActive)}
                  title={`${subj.display_name} → ${subj.category} → ${superLabel}`}
                >
                  <span className="flex items-center gap-2 min-w-0">
                    {subj.avatar_url ? (
                      <img
                        src={resolveMediaUrl(subj.avatar_url)}
                        alt={subj.display_name}
                        className="w-5 h-5 rounded-full object-cover ring-1 ring-black/10 shrink-0"
                      />
                    ) : (
                      <div className="w-5 h-5 rounded-full bg-black/10 flex items-center justify-center text-[10px] font-bold shrink-0">
                        {subj.display_name ? subj.display_name[0].toLowerCase() : '?'}
                      </div>
                    )}
                    <span className="truncate font-semibold lowercase">{subj.display_name}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full truncate lowercase ${
                        isActive
                          ? 'bg-white/20 text-white'
                          : 'bg-black/[0.06] text-[#86868B]'
                      }`}
                    >
                      {subj.category} → {superLabel}
                    </span>
                  </span>
                  <span className="text-[11px] opacity-75 ml-1">{subj.photo_count}</span>
                </button>
              );
            })}

            {(roots?.type_tree || []).map((st) => {
              const active =
                navMode.type === 'super_type' && navMode.super_type === st.name;
              return (
                <button
                  key={st.name}
                  onClick={() =>
                    onSelectNav({
                      type: 'super_type',
                      super_type: st.name,
                      label: `type: ${st.name.toLowerCase()}`,
                    })
                  }
                  className={navBtnClass(active)}
                >
                  <span className="flex items-center gap-2 lowercase">
                    <Sparkles className="w-3.5 h-3.5 opacity-80" />
                    <span>all {st.name.toLowerCase()}</span>
                  </span>
                  <span className="text-[11px] opacity-75">{st.count}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ROOT 2: DRIVE */}
        <div>
          <div className="px-3 mb-1.5 flex items-center justify-between">
            <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
              2. folders
            </p>
            <button
              onClick={onOpenScanModal}
              className="p-0.5 rounded hover:bg-black/10 text-[#0071E3]"
              title="scan a folder"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-1">
            {(roots?.drive_tree || []).map((drv) =>
              (drv?.folders || []).map((fld) =>
                (fld?.subfolders || []).map((sub) => {
                  const isActive =
                    navMode.type === 'drive_hierarchy' &&
                    navMode.drive_root === drv.name &&
                    navMode.folder_name === fld.name &&
                    navMode.subfolder_name === sub.name;
                  return (
                    <button
                      key={`${drv.name}-${fld.name}-${sub.name}`}
                      onClick={() =>
                        onSelectNav({
                          type: 'drive_hierarchy',
                          drive_root: drv.name,
                          folder_name: fld.name,
                          subfolder_name: sub.name,
                          label: `${sub.name.toLowerCase()} → ${fld.name.toLowerCase()} → ${drv.name.toLowerCase()}`,
                        })
                      }
                      className={navBtnClass(isActive)}
                      title={`${sub.name} → ${fld.name} → ${drv.name}`}
                    >
                      <span className="flex items-center gap-2 min-w-0 lowercase">
                        <FolderOpen className="w-3.5 h-3.5 shrink-0 opacity-80" />
                        <span className="truncate text-xs">
                          {sub.name}{' '}
                          <span className="opacity-60 text-[10px]">
                            → {fld.name} → {drv.name}
                          </span>
                        </span>
                      </span>
                      <span className="text-[11px] opacity-75 ml-1">{sub.count}</span>
                    </button>
                  );
                })
              )
            )}
            {(roots?.drive_tree || []).map((drv) => {
              const active =
                navMode.type === 'drive_hierarchy' &&
                navMode.drive_root === drv.name &&
                !navMode.folder_name;
              return (
                <button
                  key={drv.name}
                  onClick={() =>
                    onSelectNav({
                      type: 'drive_hierarchy',
                      drive_root: drv.name,
                      label: `drive (${drv.name.toLowerCase()})`,
                    })
                  }
                  className={navBtnClass(active)}
                >
                  <span className="flex items-center gap-2 lowercase">
                    <HardDrive className="w-3.5 h-3.5 opacity-80" />
                    <span>drive ({drv.name.toLowerCase()})</span>
                  </span>
                  <span className="text-[11px] opacity-75">{drv.count}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ROOT 3: DEVICE */}
        <div>
          <div className="px-3 mb-1.5 flex items-center justify-between">
            <p className="text-[11px] font-semibold lowercase tracking-wider text-[#86868B]">
              3. devices
            </p>
            <span className="text-[10px] text-[#86868B] lowercase">what took it</span>
          </div>
          <div className="space-y-1">
            {(roots?.device_tree || []).map((dev) => {
              const isActive =
                navMode.type === 'device_hierarchy' &&
                navMode.device_name === dev.name &&
                !navMode.image_type;
              const formats = (dev?.image_types || []).map((t) => t.image_type.toLowerCase()).join('/');
              return (
                <button
                  key={dev.name}
                  onClick={() =>
                    onSelectNav({
                      type: 'device_hierarchy',
                      device_name: dev.name,
                      label: `device: ${dev.name.toLowerCase()} (${formats})`,
                    })
                  }
                  className={navBtnClass(isActive)}
                  title={`${dev.name} (${formats})`}
                >
                  <span className="flex items-center gap-2 min-w-0 lowercase">
                    <Camera className="w-3.5 h-3.5 shrink-0 opacity-80" />
                    <span className="truncate text-xs">{dev.name.toLowerCase()}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full shrink-0 lowercase ${
                        isActive
                          ? 'bg-white/20 text-white'
                          : 'bg-black/[0.06] text-[#86868B]'
                      }`}
                    >
                      {formats}
                    </span>
                  </span>
                  <span className="text-[11px] opacity-75 ml-1">{dev.count}</span>
                </button>
              );
            })}

            {/* Quick Format Filters (jpeg, png, webp) */}
            <div className="pt-1 flex flex-wrap gap-1.5 px-1">
              {['jpeg', 'png', 'webp'].map((fmt) => {
                const active =
                  navMode.type === 'device_hierarchy' &&
                  (navMode.image_type || '').toLowerCase() === fmt &&
                  !navMode.device_name;
                return (
                  <button
                    key={fmt}
                    onClick={() =>
                      onSelectNav({
                        type: 'device_hierarchy',
                        image_type: fmt.toUpperCase(),
                        label: `format: ${fmt}`,
                      })
                    }
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-all lowercase ${
                      active
                        ? 'bg-[#0071E3] text-white'
                        : 'bg-white/80 text-[#1D1D1F] border border-black/[0.06] hover:bg-white'
                    }`}
                  >
                    <FileImage className="w-2.5 h-2.5 opacity-70" />
                    <span>{fmt}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Settings & Library Maintenance Footer */}
      <div className="p-3 border-t border-black/[0.06] space-y-1">
        {onReanalyzeLibrary && stats.total_photos > 0 && (
          <button
            onClick={onReanalyzeLibrary}
            className="w-full flex items-center justify-between px-3 py-1.5 rounded-xl text-xs font-medium text-[#1C1C1E]/80 hover:bg-black/[0.05] transition-colors lowercase"
            title="re-scan all photos"
          >
            <span className="flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 text-[#007AFF]" />
              <span>re-scan photos</span>
            </span>
            <span className="text-[10px] text-[#8E8E93]">scan</span>
          </button>
        )}
        <button
          onClick={onOpenSettingsModal}
          className="w-full flex items-center justify-between px-3 py-1.5 rounded-xl text-xs font-medium text-[#1C1C1E]/80 hover:bg-black/[0.05] transition-colors lowercase"
        >
          <span className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#007AFF]" />
            <span>settings</span>
          </span>
          <span className="text-[10px] text-[#8E8E93]">local</span>
        </button>
        <button
          onClick={onOpenClearLibrary}
          className="w-full flex items-center justify-between px-3 py-1.5 rounded-xl text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors lowercase"
        >
          <span className="flex items-center gap-2">
            <Trash2 className="w-3.5 h-3.5 text-rose-500" />
            <span>clear library</span>
          </span>
          <span className="text-[10px] text-rose-400">reset</span>
        </button>
      </div>
    </aside>
  );
};
