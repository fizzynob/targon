import React, { useState, useEffect } from 'react';
import {
  X,
  Cpu,
  Sparkles,
  Cloud,
  Check,
  Sliders,
  FileText,
  Database,
  ArrowLeftRight,
  Download,
  Upload,
  ShieldCheck,
  Trash2,
  Gamepad2,
  Volume2,
  Zap,
  Gauge,
  Image as ImageIcon,
  Eye,
  ScanFace,
  Type,
  Sun,
  Search,
  FolderSync,
  FlaskConical,
  LayoutGrid,
  AlertCircle,
} from 'lucide-react';
import { SettingsModel } from '../../types';
import { api } from '../../api/client';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: SettingsModel;
  onSaveSettings: (newSettings: SettingsModel) => Promise<void>;
  onOpenClearLibrary: () => void;
  onScanPlaceholder300?: () => Promise<void>;
}

type SettingsTab = 'general' | 'scanning' | 'storage' | 'testing';

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  onOpenClearLibrary,
  onScanPlaceholder300,
}) => {
  const [form, setForm] = useState<SettingsModel>(settings);
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');
  const [saving, setSaving] = useState(false);
  const [xmpMsg, setXmpMsg] = useState<string | null>(null);
  const [generating300, setGenerating300] = useState(false);
  const [placeholderMsg, setPlaceholderMsg] = useState<string | null>(null);

  useEffect(() => {
    setForm(settings);
    setPlaceholderMsg(null);
  }, [settings, isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSaveSettings(form);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const handleTrigger300Placeholders = async () => {
    if (generating300) return;
    setGenerating300(true);
    setPlaceholderMsg('making 300 test photos and starting scan...');
    try {
      await onSaveSettings(form);
      if (onScanPlaceholder300) {
        await onScanPlaceholder300();
      } else {
        await api.scanPlaceholder300(false);
      }
      setPlaceholderMsg('added 300 placeholder photos — scanning now.');
      setTimeout(() => {
        onClose();
      }, 350);
    } catch {
      setPlaceholderMsg('could not create placeholder photos.');
    } finally {
      setGenerating300(false);
    }
  };

  const handleExportXmp = async () => {
    setXmpMsg('writing sidecars...');
    try {
      const res = await api.exportAllXmp();
      setXmpMsg(`wrote ${res.count} sidecar files.`);
    } catch {
      setXmpMsg('export failed.');
    }
  };

  const handleImportXmp = async () => {
    setXmpMsg('reading sidecars...');
    try {
      const res = await api.importAllXmp();
      setXmpMsg(`synced from ${res.count} sidecar files.`);
    } catch {
      setXmpMsg('sync failed.');
    }
  };

  const renderToggleRow = (opts: {
    icon: React.ReactNode;
    title: string;
    badge?: string;
    badgeColor?: string;
    desc: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
  }) => (
    <div className="p-3.5 rounded-2xl bg-[#F5F5F7] flex items-center justify-between gap-4 border border-black/[0.04]">
      <div className="space-y-0.5 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          {opts.icon}
          <span className="text-xs font-bold text-[#1D1D1F] lowercase">{opts.title}</span>
          {opts.badge && (
            <span
              className={`text-[9px] font-semibold px-2 py-0.5 rounded-full lowercase ${
                opts.badgeColor || 'bg-[#0071E3]/10 text-[#0071E3]'
              }`}
            >
              {opts.badge}
            </span>
          )}
        </div>
        <p className="text-[11px] text-[#86868B] leading-relaxed lowercase">{opts.desc}</p>
      </div>
      <label className="relative inline-flex items-center cursor-pointer shrink-0">
        <input
          type="checkbox"
          checked={opts.checked}
          onChange={(e) => opts.onChange(e.target.checked)}
          className="sr-only peer"
        />
        <div className="w-11 h-6 bg-black/15 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0071E3]" />
      </label>
    </div>
  );

  const storageOptions: Array<{
    id: 'sidecar' | 'database' | 'both';
    title: string;
    badge: string;
    desc: string;
    icon: React.ReactNode;
  }> = [
    {
      id: 'sidecar',
      title: 'sidecar files (.xmp)',
      badge: 'in folder',
      desc: 'saves little .xmp text files right next to each photo so other apps can read your tags.',
      icon: <FileText className="w-4 h-4 text-[#0071E3]" />,
    },
    {
      id: 'database',
      title: 'database only',
      badge: 'clean folders',
      desc: 'keeps tags inside the app without adding extra files to your photo folders.',
      icon: <Database className="w-4 h-4 text-[#0071E3]" />,
    },
    {
      id: 'both',
      title: 'both',
      badge: 'recommended',
      desc: 'saves in the app and also writes .xmp files next to your photos.',
      icon: <ArrowLeftRight className="w-4 h-4 text-[#0071E3]" />,
    },
  ];

  const modes: Array<{
    id: 'local' | 'hybrid' | 'cloud';
    title: string;
    badge: string;
    desc: string;
    icon: React.ReactNode;
  }> = [
    {
      id: 'local',
      title: 'offline only',
      badge: 'local',
      desc: "runs on your computer. doesn't send anything anywhere and doesn't need internet.",
      icon: <Cpu className="w-5 h-5 text-[#0071E3]" />,
    },
    {
      id: 'hybrid',
      title: 'hybrid',
      badge: 'needs key',
      desc: "mostly runs locally, but asks google's model if you want more details.",
      icon: <Sparkles className="w-5 h-5 text-[#0071E3]" />,
    },
    {
      id: 'cloud',
      title: 'cloud',
      badge: 'online',
      desc: "sends photos to google's model to tag things.",
      icon: <Cloud className="w-5 h-5 text-[#0071E3]" />,
    },
  ];

  const renderPlaceholder300Card = () => (
    <div className="p-4 rounded-2xl bg-[#0071E3]/[0.06] border border-[#0071E3]/20 space-y-2.5">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-[#0071E3]" />
            <span className="text-xs font-bold text-[#1D1D1F] lowercase">
              test scanning (300 placeholder photos)
            </span>
            <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#0071E3] text-white lowercase">
              300 total
            </span>
          </div>
          <p className="text-[11px] text-[#86868B] leading-relaxed lowercase">
            creates 300 test pictures across different folders and scans them right away so you can see how fast it runs.
          </p>
        </div>
        <button
          type="button"
          disabled={generating300}
          onClick={handleTrigger300Placeholders}
          className="shrink-0 px-3.5 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] disabled:opacity-50 text-white text-xs font-semibold transition-all shadow-xs lowercase"
        >
          {generating300 ? 'adding 300...' : 'add 300 placeholder photos'}
        </button>
      </div>
      {placeholderMsg && (
        <p className="text-[11px] text-[#0071E3] font-medium lowercase">{placeholderMsg}</p>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4 select-none">
      <form
        onSubmit={handleSave}
        className="w-full max-w-2xl bg-white rounded-3xl shadow-appleModal border border-black/[0.08] overflow-hidden flex flex-col max-h-[88vh]"
      >
        {/* Header */}
        <div className="px-7 py-5 border-b border-black/[0.06] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#1D1D1F] lowercase">settings</h3>
              <p className="text-xs text-[#86868B] lowercase">
                speed, scanning, appearance, and test tools
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#F5F5F7] text-[#86868B] hover:text-[#1D1D1F]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Category Tabs */}
        <div className="px-7 pt-3 pb-2 bg-[#F5F5F7]/60 border-b border-black/[0.06] flex items-center gap-1.5 overflow-x-auto shrink-0">
          {(
            [
              { id: 'general', label: 'general & speed' },
              { id: 'scanning', label: 'scanning & tags' },
              { id: 'storage', label: 'storage & files' },
              { id: 'testing', label: 'testing & reset' },
            ] as Array<{ id: SettingsTab; label: string }>
          ).map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all lowercase ${
                activeTab === t.id
                  ? 'bg-[#0071E3] text-white shadow-2xs'
                  : 'text-[#86868B] hover:text-[#1D1D1F] hover:bg-black/[0.04]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="p-7 space-y-5 overflow-y-auto flex-1">
          {activeTab === 'general' && (
            <>
              {/* Quick 300 Placeholder Test Action right at the top of General & Speed */}
              {renderPlaceholder300Card()}

              {/* Low Spec Mode */}
              {renderToggleRow({
                icon: <Gauge className="w-4 h-4 text-[#0071E3]" />,
                title: 'low spec mode',
                badge: 'potato friendly',
                badgeColor: 'bg-emerald-50 text-emerald-700 border border-emerald-200/50',
                desc: 'turns off heavy models and extra effects so the app runs fast and light on older computers.',
                checked: Boolean(form.low_spec_mode),
                onChange: (checked) =>
                  setForm({
                    ...form,
                    low_spec_mode: checked,
                    reduce_motion: checked ? true : form.reduce_motion,
                    fast_tagging: checked ? true : form.fast_tagging,
                    thumbnail_quality: checked ? 'fast' : form.thumbnail_quality,
                  }),
              })}

              {/* Fast Tagging */}
              {renderToggleRow({
                icon: <Zap className="w-4 h-4 text-[#0071E3]" />,
                title: 'fast item tagging',
                badge: 'high img/s',
                desc: 'uses a single pass when tagging items so folders finish scanning way faster.',
                checked: form.fast_tagging !== false,
                onChange: (checked) => setForm({ ...form, fast_tagging: checked }),
              })}

              {/* Parallel Scan Workers Slider */}
              <div className="p-4 rounded-2xl bg-[#F5F5F7] space-y-2 border border-black/[0.04]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#0071E3]" />
                    <label className="text-xs font-bold text-[#1D1D1F] lowercase">
                      scan workers (photos at once)
                    </label>
                  </div>
                  <span className="text-xs font-bold text-[#0071E3] lowercase">
                    {form.scan_threads ?? 4} {(form.scan_threads ?? 4) === 1 ? 'worker' : 'workers'}
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={8}
                  step={1}
                  value={form.scan_threads ?? 4}
                  onChange={(e) =>
                    setForm({ ...form, scan_threads: parseInt(e.target.value, 10) })
                  }
                  className="w-full accent-[#0071E3] cursor-pointer"
                />
                <p className="text-[11px] text-[#86868B] lowercase">
                  higher scans folders faster. set to 1 or 2 if your pc feels slow while scanning.
                </p>
              </div>

              {/* Thumbnail Quality */}
              <div className="p-4 rounded-2xl bg-[#F5F5F7] space-y-2.5 border border-black/[0.04]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ImageIcon className="w-4 h-4 text-[#0071E3]" />
                    <span className="text-xs font-bold text-[#1D1D1F] lowercase">
                      preview quality
                    </span>
                  </div>
                  <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-black/[0.06]">
                    {(['fast', 'balanced', 'high'] as const).map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setForm({ ...form, thumbnail_quality: q })}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all lowercase ${
                          (form.thumbnail_quality || 'balanced') === q
                            ? 'bg-[#0071E3] text-white'
                            : 'text-[#86868B] hover:text-[#1D1D1F]'
                        }`}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-[#86868B] lowercase">
                  fast makes smaller thumbnails so big folders load quickly and use less disk space.
                </p>
              </div>

              {/* Default Grid Columns */}
              <div className="p-4 rounded-2xl bg-[#F5F5F7] space-y-2.5 border border-black/[0.04]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <LayoutGrid className="w-4 h-4 text-[#0071E3]" />
                    <span className="text-xs font-bold text-[#1D1D1F] lowercase">
                      default grid size
                    </span>
                  </div>
                  <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-black/[0.06]">
                    {[2, 3, 4, 5, 6].map((cols) => (
                      <button
                        key={cols}
                        type="button"
                        onClick={() => setForm({ ...form, default_grid_cols: cols })}
                        className={`w-7 py-1 rounded-lg text-[11px] font-semibold transition-all lowercase ${
                          (form.default_grid_cols || 4) === cols
                            ? 'bg-[#0071E3] text-white'
                            : 'text-[#86868B] hover:text-[#1D1D1F]'
                        }`}
                      >
                        {cols}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-[#86868B] lowercase">
                  how many pictures to show per row in the photo grid.
                </p>
              </div>

              {/* Reduce Animations */}
              {renderToggleRow({
                icon: <Eye className="w-4 h-4 text-[#0071E3]" />,
                title: 'reduce animations',
                badge: 'saves gpu',
                desc: 'turns off hover zoom and blur effects so scrolling stays smooth.',
                checked: Boolean(form.reduce_motion),
                onChange: (checked) => setForm({ ...form, reduce_motion: checked }),
              })}

              {/* Group by Month by Default */}
              {renderToggleRow({
                icon: <LayoutGrid className="w-4 h-4 text-[#0071E3]" />,
                title: 'group photos by month',
                desc: 'organizes the grid under month and year headers by default.',
                checked: form.group_by_date_default !== false,
                onChange: (checked) => setForm({ ...form, group_by_date_default: checked }),
              })}

              {/* Show Card Labels */}
              {renderToggleRow({
                icon: <Type className="w-4 h-4 text-[#0071E3]" />,
                title: 'show labels under photos',
                desc: 'shows the filename or subject name bar underneath each thumbnail.',
                checked: form.show_card_tags !== false,
                onChange: (checked) => setForm({ ...form, show_card_tags: checked }),
              })}

              {/* Sound Effects */}
              {renderToggleRow({
                icon: <Volume2 className="w-4 h-4 text-[#0071E3]" />,
                title: 'sound effects',
                badge: 'audio',
                desc: 'plays subtle clicks and sounds when you click things.',
                checked: form.sound_effects !== false,
                onChange: (checked) => setForm({ ...form, sound_effects: checked }),
              })}

              {/* Confirm Before Delete */}
              {renderToggleRow({
                icon: <AlertCircle className="w-4 h-4 text-[#0071E3]" />,
                title: 'ask before removing photos',
                desc: 'shows a confirmation prompt before removing selected photos from the app.',
                checked: Boolean(form.confirm_before_delete),
                onChange: (checked) => setForm({ ...form, confirm_before_delete: checked }),
              })}
            </>
          )}

          {activeTab === 'scanning' && (
            <>
              {/* 3-Mode Selector */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold lowercase tracking-wider text-[#86868B]">
                  how to analyze photos
                </label>
                <div className="space-y-2.5">
                  {modes.map((m) => {
                    const selected = form.ai_mode === m.id;
                    return (
                      <div
                        key={m.id}
                        onClick={() => setForm({ ...form, ai_mode: m.id })}
                        className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-start gap-3.5 ${
                          selected
                            ? 'bg-[#0071E3]/[0.05] border-[#0071E3] ring-2 ring-[#0071E3]/15'
                            : 'bg-[#F5F5F7]/60 border-black/[0.06] hover:bg-[#F5F5F7]'
                        }`}
                      >
                        <div className="mt-0.5">{m.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-sm font-bold text-[#1D1D1F] lowercase">
                              {m.title}
                            </span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full lowercase ${
                                selected
                                  ? 'bg-[#0071E3] text-white'
                                  : 'bg-black/[0.06] text-[#86868B]'
                              }`}
                            >
                              {m.badge}
                            </span>
                          </div>
                          <p className="text-xs text-[#86868B] mt-1 leading-relaxed lowercase">
                            {m.desc}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Gemini API Key Input */}
              {(form.ai_mode === 'hybrid' || form.ai_mode === 'cloud') && (
                <div className="p-4 rounded-2xl bg-[#F5F5F7] space-y-3 border border-black/[0.04]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-xs font-semibold text-[#1C1C1E] lowercase">
                        gemini api key (optional)
                      </label>
                      <p className="text-[11px] text-[#8E8E93] mt-0.5 lowercase">
                        if you want to use the cloud model. saved on your pc with windows protection.
                      </p>
                    </div>
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-semibold border border-emerald-200/50 lowercase">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>protected</span>
                    </div>
                  </div>
                  <input
                    type="password"
                    value={form.gemini_api_key}
                    onChange={(e) => setForm({ ...form, gemini_api_key: e.target.value })}
                    placeholder={
                      form.ppapi_status?.has_key
                        ? `saved key active (${form.ppapi_status.masked_key})`
                        : 'paste key here...'
                    }
                    className="w-full px-3.5 py-2 text-xs bg-white rounded-xl border border-black/10 focus:border-[#007AFF] outline-none font-mono lowercase"
                  />
                  {form.ppapi_status?.has_key && (
                    <p className="text-[10px] text-emerald-600 font-medium lowercase">
                      ✓ key saved ({form.ppapi_status.masked_key})
                    </p>
                  )}
                </div>
              )}

              {/* Subject Differentiation Threshold Slider */}
              <div className="p-4 rounded-2xl bg-[#F5F5F7] space-y-2 border border-black/[0.04]">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-[#1D1D1F] lowercase">
                    how strict to group similar things
                  </label>
                  <span className="text-xs font-bold text-[#0071E3]">
                    {Math.round(form.similarity_threshold * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0.55}
                  max={0.9}
                  step={0.01}
                  value={form.similarity_threshold}
                  onChange={(e) =>
                    setForm({ ...form, similarity_threshold: parseFloat(e.target.value) })
                  }
                  className="w-full accent-[#0071E3] cursor-pointer"
                />
                <p className="text-[11px] text-[#86868B] lowercase">
                  higher means it will be pickier before thinking two things or pets are the same.
                </p>
              </div>

              {/* Group Similar Faces & Pets */}
              {renderToggleRow({
                icon: <ScanFace className="w-4 h-4 text-[#0071E3]" />,
                title: 'group similar people & pets',
                desc: 'puts photos of the same person or pet into their own group automatically.',
                checked: form.auto_cluster !== false,
                onChange: (checked) => setForm({ ...form, auto_cluster: checked }),
              })}

              {/* Find Faces */}
              {renderToggleRow({
                icon: <ScanFace className="w-4 h-4 text-[#0071E3]" />,
                title: 'find faces',
                desc: 'looks for human and pet faces inside photos. turn off for faster scans.',
                checked: form.enable_face_detection !== false,
                onChange: (checked) => setForm({ ...form, enable_face_detection: checked }),
              })}

              {/* Read Text in Photos (OCR) */}
              {renderToggleRow({
                icon: <Type className="w-4 h-4 text-[#0071E3]" />,
                title: 'read text in photos',
                desc: 'reads words on signs, menus, and receipts so you can search for them.',
                checked: form.enable_ocr !== false,
                onChange: (checked) => setForm({ ...form, enable_ocr: checked }),
              })}

              {/* Lighting & Color Tags */}
              {renderToggleRow({
                icon: <Sun className="w-4 h-4 text-[#0071E3]" />,
                title: 'lighting & color tags',
                desc: 'adds simple tags like sunset, night, bright lighting, or black and white.',
                checked: form.enable_scene_analysis !== false,
                onChange: (checked) => setForm({ ...form, enable_scene_analysis: checked }),
              })}

              {/* Extra Phrase Search Model (CLIP) */}
              {renderToggleRow({
                icon: <Search className="w-4 h-4 text-[#0071E3]" />,
                title: 'extra phrase search model',
                badge: form.low_spec_mode ? 'paused in low spec' : 'accurate',
                desc: 'runs a bigger local model for detailed tags and phrase search. turn off on slower pcs.',
                checked: form.enable_clip_search !== false && !form.low_spec_mode,
                onChange: (checked) => setForm({ ...form, enable_clip_search: checked }),
              })}

              {/* Video Game Asset Detection */}
              {renderToggleRow({
                icon: <Gamepad2 className="w-4 h-4 text-[#0071E3]" />,
                title: 'filter out game screenshots',
                badge: 'filter',
                badgeColor: 'bg-emerald-50 text-emerald-700 border border-emerald-200/50',
                desc: "tries to hide game screenshots, textures, and ui icons so they don't get mixed in with normal photos.",
                checked: form.game_detection !== false,
                onChange: (checked) => setForm({ ...form, game_detection: checked }),
              })}

              {/* Skip Tiny Icons */}
              {renderToggleRow({
                icon: <ImageIcon className="w-4 h-4 text-[#0071E3]" />,
                title: 'ignore tiny icons (<48px)',
                desc: 'skips tiny app thumbnails and small web icons when scanning folders.',
                checked: form.skip_small_images !== false,
                onChange: (checked) => setForm({ ...form, skip_small_images: checked }),
              })}

              {/* Watch Folders */}
              {renderToggleRow({
                icon: <FolderSync className="w-4 h-4 text-[#0071E3]" />,
                title: 'watch folders for new photos',
                desc: 'automatically picks up new files dropped into folders you already scanned.',
                checked: form.watch_folders !== false,
                onChange: (checked) => setForm({ ...form, watch_folders: checked }),
              })}
            </>
          )}

          {activeTab === 'storage' && (
            <>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold lowercase tracking-wider text-[#86868B]">
                    where tags go
                  </label>
                  <p className="text-[11px] text-[#86868B] mt-0.5 lowercase">
                    choose how tags get saved.
                  </p>
                </div>

                <div className="space-y-2">
                  {storageOptions.map((opt) => {
                    const selected = (form.tag_storage_mode || 'both') === opt.id;
                    return (
                      <div
                        key={opt.id}
                        onClick={() => setForm({ ...form, tag_storage_mode: opt.id })}
                        className={`p-3.5 rounded-2xl border cursor-pointer transition-all flex items-start gap-3 ${
                          selected
                            ? 'bg-[#0071E3]/[0.05] border-[#0071E3] ring-2 ring-[#0071E3]/15'
                            : 'bg-[#F5F5F7]/60 border-black/[0.06] hover:bg-[#F5F5F7]'
                        }`}
                      >
                        <div className="mt-0.5">{opt.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-[#1D1D1F] lowercase">
                              {opt.title}
                            </span>
                            <span
                              className={`text-[9px] font-semibold px-2 py-0.5 rounded-full lowercase ${
                                selected
                                  ? 'bg-[#0071E3] text-white'
                                  : 'bg-black/[0.06] text-[#86868B]'
                              }`}
                            >
                              {opt.badge}
                            </span>
                          </div>
                          <p className="text-[11px] text-[#86868B] mt-0.5 leading-relaxed lowercase">
                            {opt.desc}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* XMP Sidecar Batch Sync Controls */}
                <div className="p-4 rounded-2xl bg-[#F5F5F7] flex flex-col gap-2.5 border border-black/[0.04]">
                  <span className="text-xs font-bold text-[#1D1D1F] lowercase">
                    sync sidecar files
                  </span>
                  <p className="text-[11px] text-[#86868B] lowercase">
                    write your current tags to .xmp files on disk or pull tags back in from existing .xmp files.
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleExportXmp}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-black/[0.05] text-xs font-medium text-[#1D1D1F] border border-black/10 transition-colors lowercase"
                    >
                      <Download className="w-3.5 h-3.5 text-[#0071E3]" />
                      <span>write all .xmp files</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleImportXmp}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-black/[0.05] text-xs font-medium text-[#1D1D1F] border border-black/10 transition-colors lowercase"
                    >
                      <Upload className="w-3.5 h-3.5 text-[#0071E3]" />
                      <span>read from .xmp files</span>
                    </button>
                  </div>
                  {xmpMsg && (
                    <p className="text-[10px] text-[#0071E3] font-medium text-center lowercase">
                      {xmpMsg}
                    </p>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'testing' && (
            <>
              {/* 300 Placeholder Photos Benchmark Generator */}
              {renderPlaceholder300Card()}

              {/* Library Maintenance & Reset */}
              <div className="p-4 rounded-2xl bg-rose-50/50 border border-rose-200/50 space-y-2">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-bold text-rose-700 flex items-center gap-1.5 lowercase">
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>clear library</span>
                    </span>
                    <p className="text-[11px] text-[#8E8E93] mt-0.5 lowercase">
                      removes all photos from the app. doesn't delete your actual files.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onOpenClearLibrary();
                    }}
                    className="px-3.5 py-2 rounded-xl bg-white text-rose-600 hover:bg-rose-50 text-xs font-semibold border border-rose-200 transition-colors shadow-2xs lowercase shrink-0"
                  >
                    clear library...
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-7 py-4 bg-[#F5F5F7]/70 border-t border-black/[0.06] flex items-center justify-between gap-3 shrink-0">
          <button
            type="button"
            disabled={generating300}
            onClick={handleTrigger300Placeholders}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#0071E3]/10 hover:bg-[#0071E3]/15 text-[#0071E3] text-xs font-semibold transition-colors disabled:opacity-50 lowercase"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>{generating300 ? 'adding 300 photos...' : 'add 300 test photos'}</span>
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full text-xs font-semibold text-[#86868B] hover:text-[#1D1D1F] lowercase"
            >
              cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-semibold shadow-xs lowercase"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{saving ? 'saving...' : 'save'}</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
