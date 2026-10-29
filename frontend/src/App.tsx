import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  PhotoItem,
  SubjectItem,
  TagInfo,
  FolderItem,
  ScanStatus,
  SettingsModel,
  LibraryStats,
  ThreeRootTrees,
} from './types';
import { api } from './api/client';
import { Sidebar, NavMode } from './components/layout/Sidebar';
import { TitleBar } from './components/layout/TitleBar';
import { PhotoGrid } from './components/gallery/PhotoGrid';
import { PeopleAndPetsView } from './components/subjects/PeopleAndPetsView';
import { RootSystemsView } from './components/roots/RootSystemsView';
import { InspectorPanel } from './components/inspector/InspectorPanel';
import { ScanModal } from './components/scanner/ScanModal';
import { SettingsModal } from './components/scanner/SettingsModal';
import { SpotlightModal } from './components/search/SpotlightModal';
import { LightboxModal } from './components/gallery/LightboxModal';
import { ClearLibraryModal } from './components/gallery/ClearLibraryModal';
import { CompareModal } from './components/gallery/CompareModal';
import { KeyboardShortcutsModal } from './components/layout/KeyboardShortcutsModal';
import { sound } from './utils/sound';

function toggleNavMode(current: NavMode, target: NavMode): NavMode {
  if (current.type === target.type) {
    if (target.type === 'all') return target;
    if (target.type === 'favorites' || target.type === 'roots' || target.type === 'people_pets') {
      return { type: 'all' };
    }
    if (
      target.type === 'tag' &&
      current.type === 'tag' &&
      current.tag.toLowerCase() === target.tag.toLowerCase()
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'category' &&
      current.type === 'category' &&
      current.category.toLowerCase() === target.category.toLowerCase()
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'super_type' &&
      current.type === 'super_type' &&
      current.super_type.toLowerCase() === target.super_type.toLowerCase()
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'subject' &&
      current.type === 'subject' &&
      current.subject.id === target.subject.id
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'folder' &&
      current.type === 'folder' &&
      current.folder.id === target.folder.id
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'device_hierarchy' &&
      current.type === 'device_hierarchy' &&
      current.device_name === target.device_name &&
      current.image_type === target.image_type &&
      current.capture_date === target.capture_date
    ) {
      return { type: 'all' };
    }
    if (
      target.type === 'drive_hierarchy' &&
      current.type === 'drive_hierarchy' &&
      current.drive_root === target.drive_root &&
      current.folder_name === target.folder_name &&
      current.subfolder_name === target.subfolder_name
    ) {
      return { type: 'all' };
    }
  }
  return target;
}

export const App: React.FC = () => {
  const [navMode, setNavMode] = useState<NavMode>({ type: 'all' });
  const [searchQuery, setSearchQuery] = useState('');
  const [gridCols, setGridCols] = useState(4);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [excludeGames, setExcludeGames] = useState(true);

  // Industry-grade curation states
  const [sortBy, setSortBy] = useState<string>('date_desc');
  const [minRating, setMinRating] = useState<number | null>(null);
  const [groupByDate, setGroupByDate] = useState<boolean>(true);
  const [comparePhotos, setComparePhotos] = useState<[PhotoItem, PhotoItem] | null>(null);
  const [shortcutsModalOpen, setShortcutsModalOpen] = useState<boolean>(false);
  const [duplicatesOnly, setDuplicatesOnly] = useState<boolean>(false);
  const [orientationFilter, setOrientationFilter] = useState<string | null>(null);

  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoItem | null>(null);
  const [lightboxPhoto, setLightboxPhoto] = useState<PhotoItem | null>(null);
  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [tags, setTags] = useState<TagInfo[]>([]);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [roots, setRoots] = useState<ThreeRootTrees>({
    type_tree: [],
    drive_tree: [],
    device_tree: [],
  });

  const [stats, setStats] = useState<LibraryStats>({
    total_photos: 0,
    analyzed_photos: 0,
    favorites: 0,
    total_subjects: 0,
    named_subjects: 0,
    total_tags: 0,
  });

  const [scanStatus, setScanStatus] = useState<ScanStatus>({
    status: 'idle',
    current_folder: null,
    current_file: null,
    total_files: 0,
    indexed_files: 0,
    analyzed_files: 0,
    progress_percent: 0,
    speed_fps: 0,
    error_message: null,
    ai_mode: 'local',
  });

  const [settings, setSettings] = useState<SettingsModel>({
    ai_mode: 'local',
    tag_storage_mode: 'both',
    gemini_api_key: '',
    gemini_model: 'gemini-2.5-flash',
    similarity_threshold: 0.76,
    watch_folders: true,
    auto_cluster: true,
    game_detection: true,
    sound_effects: true,
    low_spec_mode: false,
    scan_threads: 4,
    fast_tagging: true,
    enable_clip_search: true,
    enable_ocr: true,
    enable_face_detection: true,
    enable_scene_analysis: true,
    thumbnail_quality: 'balanced',
    skip_small_images: true,
    default_grid_cols: 4,
    group_by_date_default: true,
    reduce_motion: false,
    show_card_tags: true,
    confirm_before_delete: false,
  });

  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [spotlightOpen, setSpotlightOpen] = useState(false);
  const [clearLibraryModalOpen, setClearLibraryModalOpen] = useState(false);
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<Set<number>>(new Set());
  const scanPollTickRef = useRef<number>(0);

  const handleSelectNav = useCallback((mode: NavMode) => {
    sound.playPop();
    setNavMode((prev) => toggleNavMode(prev, mode));
    setSearchQuery('');
  }, []);

  const fetchLibraryData = useCallback(async () => {
    try {
      const params: Parameters<typeof api.getPhotos>[0] = {};

      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      if (navMode.type === 'favorites') {
        params.favorites_only = true;
      } else if (navMode.type === 'subject') {
        params.subject_id = navMode.subject.id;
      } else if (navMode.type === 'category') {
        params.category = navMode.category;
      } else if (navMode.type === 'super_type') {
        params.super_type = navMode.super_type;
      } else if (navMode.type === 'drive_hierarchy') {
        params.drive_root = navMode.drive_root;
        params.folder_name = navMode.folder_name;
        params.subfolder_name = navMode.subfolder_name;
      } else if (navMode.type === 'device_hierarchy') {
        params.device_name = navMode.device_name;
        params.capture_date = navMode.capture_date;
        params.image_type = navMode.image_type;
      } else if (navMode.type === 'tag') {
        params.tag = navMode.tag;
      } else if (navMode.type === 'folder') {
        params.folder_id = navMode.folder.id;
      }

      if (excludeGames) {
        params.exclude_games = true;
      } else {
        params.exclude_games = false;
      }

      params.sort_by = sortBy;
      if (minRating !== null && minRating > 0) {
        params.min_rating = minRating;
      }
      if (duplicatesOnly) {
        params.duplicates_only = true;
      }
      if (orientationFilter) {
        params.orientation = orientationFilter;
      }

      const [photoList, subjectList, tagList, folderList, statData, rootData] =
        await Promise.all([
          api.getPhotos(params),
          api.getSubjects(),
          api.getTags(),
          api.getFolders(),
          api.getStats(),
          api.getRoots(excludeGames),
        ]);

      setPhotos(photoList);
      setSubjects(subjectList);
      setTags(tagList);
      setFolders(folderList);
      setStats(statData);
      setRoots(rootData);

      setSelectedPhoto((prev) => {
        if (!prev) return photoList[0] || null;
        const updated = photoList.find((p) => p.id === prev.id);
        return updated || photoList[0] || null;
      });
    } catch (e) {
      // Backend might still be warming up
    }
  }, [navMode, searchQuery, excludeGames, sortBy, minRating, duplicatesOnly, orientationFilter]);

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        if (s.game_detection !== undefined) {
          setExcludeGames(s.game_detection !== false);
        }
        if (s.default_grid_cols !== undefined) {
          setGridCols(s.default_grid_cols);
        }
        if (s.group_by_date_default !== undefined) {
          setGroupByDate(s.group_by_date_default !== false);
        }
        sound.enabled = s.sound_effects !== false;
      })
      .catch(() => {});
    fetchLibraryData();
  }, [fetchLibraryData]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const s = await api.getScanStatus();
        scanPollTickRef.current += 1;
        const tick = scanPollTickRef.current;
        setScanStatus((prev) => {
          const wasScanning = prev.status === 'indexing' || prev.status === 'analyzing';
          const isNowScanning = s.status === 'indexing' || s.status === 'analyzing';
          const isNowDone = s.status === 'completed' || s.status === 'idle';
          if (wasScanning && isNowDone) {
            sound.playSuccess();
            fetchLibraryData();
          } else if (isNowScanning && tick % 3 === 0) {
            fetchLibraryData();
          }
          return s;
        });
      } catch (e) {}
    }, 850);
    return () => clearInterval(interval);
  }, [fetchLibraryData]);

  const handleToggleFavorite = async (e: React.MouseEvent, photoId: number) => {
    e.stopPropagation();
    await api.toggleFavorite(photoId);
    await fetchLibraryData();
  };

  const handleSetPhotoRating = async (photoId: number, rating: number) => {
    sound.playPop();
    await api.setRating(photoId, rating);
    await fetchLibraryData();
  };

  const handleRotatePhoto = async (photoId: number, degrees = 90) => {
    sound.playPop();
    await api.rotatePhoto(photoId, degrees);
    await fetchLibraryData();
  };

  const handleBatchTag = async (tagName: string) => {
    if (selectedPhotoIds.size === 0) return;
    sound.playPop();
    await api.batchTag(Array.from(selectedPhotoIds), tagName);
    await fetchLibraryData();
  };

  const handleBatchRating = async (rating: number) => {
    if (selectedPhotoIds.size === 0) return;
    sound.playPop();
    await api.batchRating(Array.from(selectedPhotoIds), rating);
    await fetchLibraryData();
  };

  const handleBatchRotate = async () => {
    if (selectedPhotoIds.size === 0) return;
    sound.playPop();
    for (const pid of Array.from(selectedPhotoIds)) {
      await api.rotatePhoto(pid, 90);
    }
    await fetchLibraryData();
  };

  const handleOpenCompare = () => {
    if (selectedPhotoIds.size >= 2) {
      const selectedList = photos.filter((p) => selectedPhotoIds.has(p.id));
      if (selectedList.length >= 2) {
        sound.playPop();
        setComparePhotos([selectedList[0], selectedList[1]]);
        return;
      }
    }
    if (selectedPhoto && photos.length >= 2) {
      const other = photos.find((p) => p.id !== selectedPhoto.id) || photos[1];
      sound.playPop();
      setComparePhotos([selectedPhoto, other]);
    }
  };

  const handleRenameSubject = async (
    subjectId: number,
    newName: string,
    category?: string
  ) => {
    const updatedSubj = await api.renameSubject(subjectId, newName, category);
    await fetchLibraryData();
    if (navMode.type === 'subject' && navMode.subject.id === subjectId && updatedSubj) {
      setNavMode({ type: 'subject', subject: updatedSubj });
    }
  };

  const handleMergeSubjects = async (sourceId: number, targetId: number) => {
    await api.mergeSubjects(sourceId, targetId);
    await fetchLibraryData();
  };

  const handleReassignPhotoSubject = async (
    psId: number,
    newName: string,
    category?: string
  ) => {
    await api.reassignPhotoSubject(psId, newName, category);
    await fetchLibraryData();
  };

  const handleAddTag = async (photoId: number, tagName: string) => {
    await api.addTagToPhoto(photoId, tagName);
    await fetchLibraryData();
  };

  const handleRemoveTag = async (photoId: number, tagId: number) => {
    await api.removeTagFromPhoto(photoId, tagId);
    await fetchLibraryData();
  };

  const handleReanalyzePhoto = async (photoId: number) => {
    await api.reanalyzePhoto(photoId);
    await fetchLibraryData();
  };

  const handleTogglePhotoSelection = (photoId: number, isMulti: boolean) => {
    setSelectedPhotoIds((prev) => {
      const next = new Set(isMulti ? prev : []);
      if (next.has(photoId)) {
        next.delete(photoId);
      } else {
        next.add(photoId);
      }
      return next;
    });
  };

  const handleSelectRange = (rangeIds: number[]) => {
    sound.playPop();
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      rangeIds.forEach((id) => next.add(id));
      return next;
    });
  };

  const handleClearSelection = () => {
    sound.playPop();
    setSelectedPhotoIds(new Set());
  };

  const handleDeselectGameAssets = () => {
    sound.playPop();
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      for (const p of photos) {
        if (p.is_game_asset) {
          next.delete(p.id);
        }
      }
      return next;
    });
  };

  const handleExportXmp = async () => {
    try {
      await api.exportAllXmp();
    } catch {}
  };

  const handleDeletePhoto = async (photoId: number) => {
    if (settings.confirm_before_delete && !window.confirm('remove this photo from your library?')) {
      return;
    }
    sound.playDelete();
    await api.deletePhoto(photoId, false);
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      next.delete(photoId);
      return next;
    });
    await fetchLibraryData();
  };

  const handleBatchDeletePhotos = async () => {
    if (selectedPhotoIds.size === 0) return;
    if (
      settings.confirm_before_delete &&
      !window.confirm(`remove ${selectedPhotoIds.size} selected photos from your library?`)
    ) {
      return;
    }
    sound.playDelete();
    const ids = Array.from(selectedPhotoIds);
    await api.deletePhotos(ids, false);
    setSelectedPhotoIds(new Set());
    await fetchLibraryData();
  };

  const handleBatchFavoritePhotos = async () => {
    if (selectedPhotoIds.size === 0) return;
    sound.playFavorite();
    const ids = Array.from(selectedPhotoIds);
    for (const pid of ids) {
      await api.toggleFavorite(pid);
    }
    await fetchLibraryData();
  };

  const handleConfirmClearLibrary = async (deleteFiles: boolean) => {
    sound.playDelete();
    await api.clearLibrary(deleteFiles);
    setSelectedPhotoIds(new Set());
    setSelectedPhoto(null);
    await fetchLibraryData();
  };

  const handleReanalyzeLibrary = async () => {
    sound.playPop();
    const st = await api.reanalyzeLibrary();
    setScanStatus(st);
  };

  const handleStartScan = async (folderPath: string, recursive: boolean) => {
    sound.playPop();
    const st = await api.startScan(folderPath, recursive);
    setScanStatus(st);
  };

  const handleScanDemo = async () => {
    sound.playPop();
    await api.scanDemoLibrary();
    await fetchLibraryData();
    setScanModalOpen(false);
  };

  const handleScanPlaceholder300 = async () => {
    sound.playPop();
    const res = await api.scanPlaceholder300(false);
    if (res.scan_status) {
      setScanStatus(res.scan_status);
    }
    setNavMode({ type: 'all' });
    setSearchQuery('');
    await fetchLibraryData();
  };

  const handleSaveSettings = async (newSettings: SettingsModel) => {
    const saved = await api.updateSettings(newSettings);
    setSettings(saved);
    if (saved.game_detection !== undefined) {
      setExcludeGames(saved.game_detection !== false);
    }
    if (saved.default_grid_cols !== undefined) {
      setGridCols(saved.default_grid_cols);
    }
    if (saved.group_by_date_default !== undefined) {
      setGroupByDate(saved.group_by_date_default !== false);
    }
    sound.enabled = saved.sound_effects !== false;
  };

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return;
      }

      // Spotlight: Cmd+K / Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSpotlightOpen((prev) => !prev);
        return;
      }

      // Inspector: Cmd+I / Ctrl+I or I
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'i') {
        e.preventDefault();
        setInspectorOpen((prev) => !prev);
        return;
      }
      if (e.key.toLowerCase() === 'i' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setInspectorOpen((prev) => !prev);
        return;
      }

      // Shortcuts Sheet: ?
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        sound.playPop();
        setShortcutsModalOpen((prev) => !prev);
        return;
      }

      // Compare Mode: C
      if (e.key.toLowerCase() === 'c' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        handleOpenCompare();
        return;
      }

      // Rotate: R
      if (e.key.toLowerCase() === 'r' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (selectedPhotoIds.size > 0) {
          handleBatchRotate();
        } else if (selectedPhoto) {
          handleRotatePhoto(selectedPhoto.id, 90);
        }
        return;
      }

      // Number keys 0-5: Instant Star Rating
      if (['0', '1', '2', '3', '4', '5'].includes(e.key) && !e.metaKey && !e.ctrlKey) {
        const rating = parseInt(e.key, 10);
        if (selectedPhotoIds.size > 0) {
          e.preventDefault();
          handleBatchRating(rating);
        } else if (selectedPhoto) {
          e.preventDefault();
          handleSetPhotoRating(selectedPhoto.id, rating);
        }
        return;
      }

      // Select All: Cmd+A / Ctrl+A
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'a') {
        e.preventDefault();
        setSelectedPhotoIds(new Set(photos.map((p) => p.id)));
        sound.playPop();
        return;
      }

      // Favorite toggle: F
      if (e.key.toLowerCase() === 'f' && !e.metaKey && !e.ctrlKey) {
        if (selectedPhotoIds.size > 0) {
          e.preventDefault();
          handleBatchFavoritePhotos();
        } else if (selectedPhoto) {
          e.preventDefault();
          api.toggleFavorite(selectedPhoto.id).then(() => {
            sound.playFavorite();
            fetchLibraryData();
          });
        }
        return;
      }

      // Quick Look: Spacebar
      if (e.code === 'Space') {
        e.preventDefault();
        if (lightboxPhoto) {
          setLightboxPhoto(null);
        } else if (selectedPhoto) {
          sound.playPop();
          setLightboxPhoto(selectedPhoto);
        }
        return;
      }

      // Arrow navigation
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        if (photos.length === 0) return;
        const currentActive = lightboxPhoto || selectedPhoto || photos[0];
        const idx = photos.findIndex((p) => p.id === currentActive.id);
        if (idx !== -1) {
          const nextIdx =
            e.key === 'ArrowRight'
              ? Math.min(photos.length - 1, idx + 1)
              : Math.max(0, idx - 1);
          const nextPhoto = photos[nextIdx];
          setSelectedPhoto(nextPhoto);
          if (lightboxPhoto) {
            setLightboxPhoto(nextPhoto);
          }
        }
        return;
      }

      // Delete: Backspace or Delete
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedPhotoIds.size > 0) {
          e.preventDefault();
          handleBatchDeletePhotos();
        } else if (selectedPhoto && !lightboxPhoto) {
          e.preventDefault();
          handleDeletePhoto(selectedPhoto.id);
        }
        return;
      }

      // Escape: Deselect or Close
      if (e.key === 'Escape') {
        if (lightboxPhoto) {
          setLightboxPhoto(null);
          return;
        }
        if (comparePhotos) {
          setComparePhotos(null);
          return;
        }
        if (shortcutsModalOpen) {
          setShortcutsModalOpen(false);
          return;
        }
        if (spotlightOpen) {
          setSpotlightOpen(false);
          return;
        }
        if (selectedPhotoIds.size > 0) {
          setSelectedPhotoIds(new Set());
          sound.playPop();
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [photos, selectedPhoto, lightboxPhoto, selectedPhotoIds, spotlightOpen, comparePhotos, shortcutsModalOpen, fetchLibraryData]);

  const getActiveViewTitle = () => {
    if (searchQuery.trim()) return `search: "${searchQuery.toLowerCase()}"`;
    switch (navMode.type) {
      case 'all':
        return 'all photos';
      case 'roots':
        return 'roots (type • folder • camera)';
      case 'favorites':
        return 'favorites';
      case 'people_pets':
        return 'people & pets';
      case 'subject':
        return `${navMode.subject.display_name.toLowerCase()} → ${navMode.subject.category.toLowerCase()} → ${(navMode.subject.super_type || 'animal').toLowerCase()}`;
      case 'category':
        return navMode.label.toLowerCase();
      case 'super_type':
        return navMode.label.toLowerCase();
      case 'drive_hierarchy':
        return navMode.label.toLowerCase();
      case 'device_hierarchy':
        return navMode.label.toLowerCase();
      case 'tag':
        return `#${navMode.tag.toLowerCase()}`;
      case 'folder':
        return navMode.folder.name.toLowerCase();
    }
  };

  const activeSubject =
    navMode.type === 'subject'
      ? subjects.find((s) => s.id === navMode.subject.id) || navMode.subject
      : null;

  const hasActiveFilter = navMode.type !== 'all' || Boolean(searchQuery.trim());

  return (
    <div className="w-screen h-screen flex overflow-hidden bg-[#FBFBFD] text-[#1D1D1F]">
      {/* Left Apple Frosted Glass Sidebar */}
      <Sidebar
        navMode={navMode}
        onSelectNav={handleSelectNav}
        subjects={subjects}
        tags={tags}
        folders={folders}
        roots={roots}
        stats={stats}
        onOpenScanModal={() => setScanModalOpen(true)}
        onOpenSettingsModal={() => setSettingsModalOpen(true)}
        onOpenClearLibrary={() => setClearLibraryModalOpen(true)}
        onReanalyzeLibrary={handleReanalyzeLibrary}
      />

      {/* Main Content Column */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <TitleBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onOpenSpotlight={() => setSpotlightOpen(true)}
          gridCols={gridCols}
          onGridColsChange={setGridCols}
          onOpenScanModal={() => setScanModalOpen(true)}
          onOpenSettingsModal={() => setSettingsModalOpen(true)}
          inspectorOpen={inspectorOpen}
          onToggleInspector={() => setInspectorOpen(!inspectorOpen)}
          scanStatus={scanStatus}
          settings={settings}
          activeViewTitle={getActiveViewTitle()}
          photoCount={photos.length}
          sortBy={sortBy}
          onSortByChange={(val) => setSortBy(val)}
          groupByDate={groupByDate}
          onToggleGroupByDate={() => setGroupByDate((prev) => !prev)}
          onOpenShortcutsModal={() => setShortcutsModalOpen(true)}
          onOpenCompare={handleOpenCompare}
          canCompare={selectedPhotoIds.size === 2 || (photos.length >= 2 && selectedPhoto !== null)}
        />

        {/* Workspace Area */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {navMode.type === 'roots' ? (
            <RootSystemsView
              roots={roots}
              subjects={subjects}
              onSelectNav={handleSelectNav}
            />
          ) : navMode.type === 'people_pets' ? (
            <PeopleAndPetsView
              subjects={subjects}
              onSelectSubject={(subj) => handleSelectNav({ type: 'subject', subject: subj })}
              onRenameSubject={handleRenameSubject}
              onMergeSubjects={handleMergeSubjects}
            />
          ) : (
            <PhotoGrid
              photos={photos}
              subjects={subjects}
              selectedPhoto={selectedPhoto}
              onSelectPhoto={(photo) => {
                setSelectedPhoto(photo);
                if (!inspectorOpen) setInspectorOpen(true);
              }}
              selectedPhotoIds={selectedPhotoIds}
              onTogglePhotoSelection={handleTogglePhotoSelection}
              onSelectRange={handleSelectRange}
              onClearSelection={handleClearSelection}
              onBatchFavorite={handleBatchFavoritePhotos}
              onBatchDelete={handleBatchDeletePhotos}
              onOpenLightbox={(photo) => setLightboxPhoto(photo)}
              onToggleFavorite={handleToggleFavorite}
              onSelectSubject={(subj) => handleSelectNav({ type: 'subject', subject: subj })}
              onSelectCategory={(cat, label) =>
                handleSelectNav({ type: 'category', category: cat, label })
              }
              onSelectTag={(t) => handleSelectNav({ type: 'tag', tag: t })}
              onResetFilter={() => {
                sound.playPop();
                setMinRating(null);
                setDuplicatesOnly(false);
                setOrientationFilter(null);
                setNavMode({ type: 'all' });
                setSearchQuery('');
              }}
              onRenameSubject={handleRenameSubject}
              onOpenScanModal={() => setScanModalOpen(true)}
              onLoadDemoLibrary={handleScanDemo}
              gridCols={gridCols}
              activeSubject={activeSubject}
              hasActiveFilter={hasActiveFilter}
              excludeGames={excludeGames}
              onToggleExcludeGames={() => setExcludeGames((prev) => !prev)}
              onDeselectGameAssets={handleDeselectGameAssets}
              onExportXmp={handleExportXmp}
              activeTag={navMode.type === 'tag' ? navMode.tag : null}
              activeCategory={navMode.type === 'category' ? navMode.category : null}
              isFavoritesView={navMode.type === 'favorites'}
              onToggleFavoritesView={() =>
                handleSelectNav({ type: 'favorites' })
              }
              groupByDate={groupByDate}
              minRating={minRating}
              onToggleMinRating={(rating) =>
                setMinRating((prev) => (prev === rating ? null : rating))
              }
              onOpenCompare={handleOpenCompare}
              onBatchTag={handleBatchTag}
              onBatchRating={handleBatchRating}
              onBatchRotate={handleBatchRotate}
              onRotatePhoto={handleRotatePhoto}
              onSetRating={handleSetPhotoRating}
              onRevealInExplorer={(id) => api.revealInExplorer(id)}
              onDeletePhoto={handleDeletePhoto}
              duplicatesOnly={duplicatesOnly}
              onToggleDuplicatesOnly={() => setDuplicatesOnly((prev) => !prev)}
              orientationFilter={orientationFilter}
              onSetOrientationFilter={(ori) => setOrientationFilter(ori)}
              reduceMotion={Boolean(settings.reduce_motion || settings.low_spec_mode)}
              showCardTags={settings.show_card_tags !== false}
            />
          )}

          {inspectorOpen && navMode.type !== 'people_pets' && navMode.type !== 'roots' && (
            <InspectorPanel
              photo={selectedPhoto}
              onClose={() => setInspectorOpen(false)}
              onOpenLightbox={(p) => setLightboxPhoto(p)}
              onRenameSubject={handleRenameSubject}
              onReassignPhotoSubject={handleReassignPhotoSubject}
              onAddTag={handleAddTag}
              onRemoveTag={handleRemoveTag}
              onReanalyzePhoto={handleReanalyzePhoto}
              onRevealInExplorer={(id) => api.revealInExplorer(id)}
              onDeletePhoto={handleDeletePhoto}
              onFilterBySubject={(subjId) => {
                const found = subjects.find((s) => s.id === subjId);
                if (found) handleSelectNav({ type: 'subject', subject: found });
              }}
              onFilterByTag={(tagName) => handleSelectNav({ type: 'tag', tag: tagName })}
              onSelectNav={handleSelectNav}
              onSetRating={handleSetPhotoRating}
              onRotatePhoto={handleRotatePhoto}
            />
          )}
        </div>
      </div>

      {/* Modals & Overlays */}
      <ScanModal
        isOpen={scanModalOpen}
        onClose={() => setScanModalOpen(false)}
        scanStatus={scanStatus}
        onStartScan={handleStartScan}
        onCancelScan={async () => {
          const st = await api.cancelScan();
          setScanStatus(st);
        }}
        onScanDemo={handleScanDemo}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        settings={settings}
        onSaveSettings={handleSaveSettings}
        onOpenClearLibrary={() => setClearLibraryModalOpen(true)}
        onScanPlaceholder300={handleScanPlaceholder300}
      />

      <ClearLibraryModal
        isOpen={clearLibraryModalOpen}
        onClose={() => setClearLibraryModalOpen(false)}
        onConfirmClear={handleConfirmClearLibrary}
        photoCount={photos.length}
      />

      <SpotlightModal
        isOpen={spotlightOpen}
        onClose={() => setSpotlightOpen(false)}
        subjects={subjects}
        tags={tags}
        onSelectSubject={(subj) => handleSelectNav({ type: 'subject', subject: subj })}
        onSelectTag={(t) => handleSelectNav({ type: 'tag', tag: t })}
        onRunSearch={(q) => {
          setNavMode({ type: 'all' });
          setSearchQuery(q);
        }}
      />

      {lightboxPhoto && (
        <LightboxModal
          photo={lightboxPhoto}
          photos={photos}
          onClose={() => setLightboxPhoto(null)}
          onSelectPhoto={(p) => setLightboxPhoto(p)}
          onToggleFavorite={handleToggleFavorite}
          onSetRating={handleSetPhotoRating}
          onRotatePhoto={handleRotatePhoto}
          onDeletePhoto={handleDeletePhoto}
          onRevealInExplorer={(id) => api.revealInExplorer(id)}
        />
      )}

      <CompareModal
        photos={comparePhotos}
        onClose={() => setComparePhotos(null)}
        onToggleFavorite={handleToggleFavorite}
        onSetRating={handleSetPhotoRating}
      />

      <KeyboardShortcutsModal
        isOpen={shortcutsModalOpen}
        onClose={() => setShortcutsModalOpen(false)}
      />
    </div>
  );
};

export default App;
