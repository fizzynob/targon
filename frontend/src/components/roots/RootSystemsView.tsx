import React from 'react';
import {
  Sparkles,
  HardDrive,
  Camera,
  ChevronRight,
  Folder,
  FolderOpen,
  Clock,
  FileImage,
  Layers,
} from 'lucide-react';
import { ThreeRootTrees, SubjectItem } from '../../types';
import { NavMode } from '../layout/Sidebar';

interface RootSystemsViewProps {
  roots: ThreeRootTrees;
  subjects: SubjectItem[];
  onSelectNav: (mode: NavMode) => void;
}

export const RootSystemsView: React.FC<RootSystemsViewProps> = ({
  roots,
  subjects,
  onSelectNav,
}) => {
  return (
    <div className="flex-1 h-full overflow-y-auto px-10 py-8 space-y-8 bg-[#FBFBFD] select-none">
      {/* Hero Banner */}
      <div className="bg-white rounded-3xl p-7 border border-black/[0.06] shadow-apple">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#0071E3]/10 text-[#0071E3] text-xs font-semibold mb-3 lowercase">
          <Layers className="w-3.5 h-3.5" />
          <span>browse by</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#1D1D1F] lowercase">
          what's in it • where it is • what took it
        </h2>
        <p className="text-sm text-[#86868B] mt-1.5 max-w-3xl leading-relaxed lowercase">
          photos are grouped in three ways: by what's in the picture, where it's stored on your computer, and the camera that took it. click anything to see matching photos.
        </p>
      </div>

      {/* 3-Column Root System Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-7 pb-10">
        {/* ROOT 1: TYPE */}
        <div className="bg-white rounded-3xl p-6 border border-black/[0.06] shadow-apple flex flex-col gap-5">
          <div className="flex items-center justify-between pb-4 border-b border-black/[0.05]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#1D1D1F] lowercase">1. what's inside</h3>
                <p className="text-[11px] text-[#86868B] lowercase">subject and category</p>
              </div>
            </div>
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#F5F5F7] text-[#1D1D1F] lowercase">
              e.g. cat → animal
            </span>
          </div>

          <div className="space-y-4">
            {(roots?.type_tree || []).map((superNode) => (
              <div
                key={superNode.name}
                className="p-4 rounded-2xl bg-[#F5F5F7]/70 border border-black/[0.04] space-y-3"
              >
                {/* Super-Type Level */}
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'super_type',
                      super_type: superNode.name,
                      label: `type: ${superNode.name.toLowerCase()}`,
                    })
                  }
                  className="w-full flex items-center justify-between text-left group"
                >
                  <span className="text-sm font-bold text-[#1D1D1F] group-hover:text-[#0071E3] flex items-center gap-1.5 lowercase">
                    <span>{superNode.name}</span>
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-black/[0.06] text-[#86868B] lowercase">
                      group
                    </span>
                  </span>
                  <span className="text-xs font-semibold text-[#86868B] lowercase">
                    {superNode.count} photos
                  </span>
                </button>

                {/* Category Level */}
                <div className="pl-3 border-l-2 border-[#0071E3]/25 space-y-2.5">
                  {(superNode.categories || []).map((catNode) => (
                    <div key={catNode.name} className="space-y-1.5">
                      <button
                        onClick={() =>
                          onSelectNav({
                            type: 'category',
                            category: catNode.name.toLowerCase(),
                            label: `category: ${catNode.name.toLowerCase()}`,
                          })
                        }
                        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-white hover:bg-[#0071E3]/10 text-xs font-semibold text-[#1D1D1F] transition-colors lowercase"
                      >
                        <span className="flex items-center gap-1.5">
                          <ChevronRight className="w-3.5 h-3.5 text-[#0071E3]" />
                          <span>{catNode.name}</span>
                        </span>
                        <span className="text-[11px] text-[#86868B]">{catNode.count}</span>
                      </button>

                      {/* Specific Identity Level */}
                      <div className="pl-4 flex flex-wrap gap-1.5">
                        {(catNode.individuals || []).map((ind) => (
                          <button
                            key={ind.name}
                            onClick={() => {
                              if (ind.subject_id != null) {
                                const found = subjects.find((s) => s.id === ind.subject_id);
                                if (found) {
                                  onSelectNav({ type: 'subject', subject: found });
                                  return;
                                }
                              }
                              onSelectNav({
                                type: 'category',
                                category: catNode.name.toLowerCase(),
                                label: `${ind.name.toLowerCase()} → ${catNode.name.toLowerCase()} → ${superNode.name.toLowerCase()}`,
                              });
                            }}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-[11px] font-semibold shadow-2xs transition-transform hover:scale-105 lowercase"
                            title={`${ind.name} → ${catNode.name} → ${superNode.name}`}
                          >
                            <span>{ind.name}</span>
                            <span className="opacity-75 text-[10px]">({ind.count})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ROOT 2: DRIVE */}
        <div className="bg-white rounded-3xl p-6 border border-black/[0.06] shadow-apple flex flex-col gap-5">
          <div className="flex items-center justify-between pb-4 border-b border-black/[0.05]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                <HardDrive className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#1D1D1F] lowercase">2. where it is</h3>
                <p className="text-[11px] text-[#86868B] lowercase">folders on disk</p>
              </div>
            </div>
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#F5F5F7] text-[#1D1D1F] lowercase">
              folders
            </span>
          </div>

          <div className="space-y-4">
            {(roots?.drive_tree || []).map((drv) => (
              <div
                key={drv.name}
                className="p-4 rounded-2xl bg-[#F5F5F7]/70 border border-black/[0.04] space-y-3"
              >
                {/* Drive Root Level */}
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'drive_hierarchy',
                      drive_root: drv.name,
                      label: `drive (${drv.name.toLowerCase()})`,
                    })
                  }
                  className="w-full flex items-center justify-between text-left group"
                >
                  <span className="text-sm font-bold text-[#1D1D1F] group-hover:text-emerald-600 flex items-center gap-2 lowercase">
                    <HardDrive className="w-4 h-4 text-emerald-600" />
                    <span>drive ({drv.name.toLowerCase()})</span>
                  </span>
                  <span className="text-xs font-semibold text-[#86868B] lowercase">
                    {drv.count} photos
                  </span>
                </button>

                {/* Folder Level */}
                <div className="pl-3 border-l-2 border-emerald-500/30 space-y-2.5">
                  {(drv.folders || []).map((fld) => (
                    <div key={fld.name} className="space-y-1.5">
                      <button
                        onClick={() =>
                          onSelectNav({
                            type: 'drive_hierarchy',
                            drive_root: drv.name,
                            folder_name: fld.name,
                            label: `${fld.name.toLowerCase()} → ${drv.name.toLowerCase()}`,
                          })
                        }
                        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-white hover:bg-emerald-500/10 text-xs font-semibold text-[#1D1D1F] transition-colors lowercase"
                      >
                        <span className="flex items-center gap-1.5">
                          <Folder className="w-3.5 h-3.5 text-emerald-600" />
                          <span>folder: {fld.name}</span>
                        </span>
                        <span className="text-[11px] text-[#86868B]">{fld.count}</span>
                      </button>

                      {/* Subfolder Level */}
                      <div className="pl-4 flex flex-wrap gap-1.5">
                        {(fld.subfolders || []).map((sub) => (
                          <button
                            key={sub.name}
                            onClick={() =>
                              onSelectNav({
                                type: 'drive_hierarchy',
                                drive_root: drv.name,
                                folder_name: fld.name,
                                subfolder_name: sub.name,
                                label: `${sub.name.toLowerCase()} → ${fld.name.toLowerCase()} → ${drv.name.toLowerCase()}`,
                              })
                            }
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold shadow-2xs transition-transform hover:scale-105 lowercase"
                            title={`${sub.name} → ${fld.name} → ${drv.name}`}
                          >
                            <FolderOpen className="w-3 h-3" />
                            <span>{sub.name}</span>
                            <span className="opacity-75 text-[10px]">({sub.count})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ROOT 3: DEVICE */}
        <div className="bg-white rounded-3xl p-6 border border-black/[0.06] shadow-apple flex flex-col gap-5">
          <div className="flex items-center justify-between pb-4 border-b border-black/[0.05]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-purple-500/10 text-purple-600 flex items-center justify-center">
                <Camera className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#1D1D1F] lowercase">3. what took it</h3>
                <p className="text-[11px] text-[#86868B] lowercase">camera and format</p>
              </div>
            </div>
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#F5F5F7] text-[#1D1D1F] lowercase">
              cameras
            </span>
          </div>

          <div className="space-y-4">
            {(roots?.device_tree || []).map((dev) => (
              <div
                key={dev.name}
                className="p-4 rounded-2xl bg-[#F5F5F7]/70 border border-black/[0.04] space-y-3"
              >
                {/* Device Make/Model Level */}
                <button
                  onClick={() =>
                    onSelectNav({
                      type: 'device_hierarchy',
                      device_name: dev.name,
                      label: `device: ${dev.name.toLowerCase()}`,
                    })
                  }
                  className="w-full flex items-center justify-between text-left group"
                >
                  <span className="text-sm font-bold text-[#1D1D1F] group-hover:text-purple-600 flex items-center gap-2 lowercase">
                    <Camera className="w-4 h-4 text-purple-600" />
                    <span>{dev.name.toLowerCase()}</span>
                  </span>
                  <span className="text-xs font-semibold text-[#86868B] lowercase">
                    {dev.count} photos
                  </span>
                </button>

                {/* Dates & Formats */}
                <div className="pl-3 border-l-2 border-purple-500/30 space-y-2">
                  {(dev.dates || []).map((dt) => (
                    <div
                      key={dt.date}
                      className="flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-white text-xs"
                    >
                      <button
                        onClick={() =>
                          onSelectNav({
                            type: 'device_hierarchy',
                            device_name: dev.name,
                            capture_date: dt.date,
                            label: `${dev.name.toLowerCase()} • ${dt.date}`,
                          })
                        }
                        className="flex items-center gap-1.5 font-semibold text-[#1D1D1F] hover:text-purple-600 lowercase"
                      >
                        <Clock className="w-3.5 h-3.5 text-purple-600" />
                        <span>{dt.date}</span>
                      </button>

                      {/* Format Badges */}
                      <div className="flex items-center gap-1">
                        {(dt.types || []).map((tp) => (
                          <button
                            key={tp.image_type}
                            onClick={() =>
                              onSelectNav({
                                type: 'device_hierarchy',
                                device_name: dev.name,
                                capture_date: dt.date,
                                image_type: tp.image_type,
                                label: `${dev.name.toLowerCase()} → ${dt.date} → ${tp.image_type.toLowerCase()}`,
                              })
                            }
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-600 hover:bg-purple-700 text-white text-[10px] font-semibold lowercase"
                          >
                            <FileImage className="w-2.5 h-2.5" />
                            <span>{tp.image_type.toLowerCase()}</span>
                            <span className="opacity-75">({tp.count})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
