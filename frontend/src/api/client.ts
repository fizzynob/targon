import {
  PhotoItem,
  SubjectItem,
  TagInfo,
  FolderItem,
  ScanStatus,
  SettingsModel,
  LibraryStats,
  DriveQuickFolder,
  ThreeRootTrees,
} from '../types';

export const API_BASE = 'http://127.0.0.1:8420';

export function resolveMediaUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${API_BASE}${url}`;
}

export const api = {
  async getStats(): Promise<LibraryStats> {
    const res = await fetch(`${API_BASE}/api/stats`);
    return res.json();
  },

  async getRoots(exclude_games?: boolean): Promise<ThreeRootTrees> {
    const q = new URLSearchParams();
    if (exclude_games !== undefined) q.set('exclude_games', String(exclude_games));
    const url = q.toString() ? `${API_BASE}/api/roots?${q.toString()}` : `${API_BASE}/api/roots`;
    const res = await fetch(url);
    return res.json();
  },

  async getPhotos(params: {
    search?: string;
    subject_id?: number | null;
    tag?: string | null;
    category?: string | null;
    super_type?: string | null;
    folder_id?: number | null;
    drive_root?: string | null;
    folder_name?: string | null;
    subfolder_name?: string | null;
    device_name?: string | null;
    capture_date?: string | null;
    image_type?: string | null;
    favorites_only?: boolean;
    exclude_games?: boolean;
    min_rating?: number | null;
    orientation?: string | null;
    duplicates_only?: boolean;
    sort_by?: string;
  }): Promise<PhotoItem[]> {
    const q = new URLSearchParams();
    if (params.search) q.set('search', params.search);
    if (params.subject_id != null) q.set('subject_id', String(params.subject_id));
    if (params.tag) q.set('tag', params.tag);
    if (params.category) q.set('category', params.category);
    if (params.super_type) q.set('super_type', params.super_type);
    if (params.folder_id != null) q.set('folder_id', String(params.folder_id));
    if (params.drive_root) q.set('drive_root', params.drive_root);
    if (params.folder_name) q.set('folder_name', params.folder_name);
    if (params.subfolder_name) q.set('subfolder_name', params.subfolder_name);
    if (params.device_name) q.set('device_name', params.device_name);
    if (params.capture_date) q.set('capture_date', params.capture_date);
    if (params.image_type) q.set('image_type', params.image_type);
    if (params.favorites_only) q.set('favorites_only', 'true');
    if (params.exclude_games !== undefined) q.set('exclude_games', String(params.exclude_games));
    if (params.min_rating != null && params.min_rating > 0) q.set('min_rating', String(params.min_rating));
    if (params.orientation) q.set('orientation', params.orientation);
    if (params.duplicates_only) q.set('duplicates_only', 'true');
    if (params.sort_by) q.set('sort_by', params.sort_by);
    q.set('limit', '1000');
    const res = await fetch(`${API_BASE}/api/photos?${q.toString()}`);
    return res.json();
  },

  async toggleFavorite(photoId: number): Promise<{ photo_id: number; is_favorite: boolean }> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/favorite`, { method: 'POST' });
    return res.json();
  },

  async setRating(photoId: number, rating: number): Promise<{ photo_id: number; rating: number }> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating }),
    });
    return res.json();
  },

  async rotatePhoto(photoId: number, degrees = 90): Promise<{ photo_id: number; rotation: number }> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/rotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ degrees }),
    });
    return res.json();
  },

  async batchTag(photoIds: number[], tagName: string): Promise<{ status: string; tagged_count: number }> {
    const res = await fetch(`${API_BASE}/api/photos/batch-tag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photo_ids: photoIds, tag_name: tagName }),
    });
    return res.json();
  },

  async batchRating(photoIds: number[], rating: number): Promise<{ status: string; rated_count: number }> {
    const res = await fetch(`${API_BASE}/api/photos/batch-rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photo_ids: photoIds, rating }),
    });
    return res.json();
  },

  async deletePhoto(photoId: number, deleteFile = false): Promise<{ status: string; photo_id: number }> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}?delete_file=${deleteFile}`, {
      method: 'DELETE',
    });
    return res.json();
  },

  async deletePhotos(photoIds: number[], deleteFiles = false): Promise<{ status: string; count: number }> {
    const res = await fetch(`${API_BASE}/api/photos/batch-delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photo_ids: photoIds, delete_files: deleteFiles }),
    });
    return res.json();
  },

  async clearLibrary(deleteFiles = false): Promise<{ cleared_photos: number; cleared_subjects: number; status: string }> {
    const res = await fetch(`${API_BASE}/api/library/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delete_files: deleteFiles }),
    });
    return res.json();
  },

  async reanalyzeLibrary(): Promise<ScanStatus> {
    const res = await fetch(`${API_BASE}/api/library/reanalyze`, {
      method: 'POST',
    });
    return res.json();
  },

  async addTagToPhoto(photoId: number, name: string, tagType = 'user'): Promise<PhotoItem> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, tag_type: tagType }),
    });
    return res.json();
  },

  async removeTagFromPhoto(photoId: number, tagId: number): Promise<void> {
    await fetch(`${API_BASE}/api/photos/${photoId}/tags/${tagId}`, { method: 'DELETE' });
  },

  async reanalyzePhoto(photoId: number): Promise<PhotoItem> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/reanalyze`, { method: 'POST' });
    return res.json();
  },

  async revealInExplorer(photoId: number): Promise<void> {
    await fetch(`${API_BASE}/api/photos/${photoId}/reveal`, { method: 'POST' });
  },

  async getSubjects(): Promise<SubjectItem[]> {
    const res = await fetch(`${API_BASE}/api/subjects`);
    return res.json();
  },

  async renameSubject(subjectId: number, name: string, category?: string): Promise<SubjectItem> {
    const res = await fetch(`${API_BASE}/api/subjects/${subjectId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, category }),
    });
    return res.json();
  },

  async mergeSubjects(sourceId: number, targetId: number): Promise<SubjectItem> {
    const res = await fetch(`${API_BASE}/api/subjects/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_subject_id: sourceId, target_subject_id: targetId }),
    });
    return res.json();
  },

  async reassignPhotoSubject(psId: number, newName: string, category?: string): Promise<SubjectItem> {
    const res = await fetch(`${API_BASE}/api/photo-subjects/${psId}/reassign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName, category }),
    });
    return res.json();
  },

  async getTags(): Promise<TagInfo[]> {
    const res = await fetch(`${API_BASE}/api/tags`);
    return res.json();
  },

  async getFolders(): Promise<FolderItem[]> {
    const res = await fetch(`${API_BASE}/api/folders`);
    return res.json();
  },

  async removeFolder(folderId: number): Promise<void> {
    await fetch(`${API_BASE}/api/folders/${folderId}`, { method: 'DELETE' });
  },

  async getDrives(): Promise<{ quick_folders: DriveQuickFolder[]; drives: DriveQuickFolder[] }> {
    const res = await fetch(`${API_BASE}/api/drives`);
    return res.json();
  },

  async startScan(folderPath: string, recursive = true): Promise<ScanStatus> {
    const res = await fetch(`${API_BASE}/api/scan/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath, recursive }),
    });
    return res.json();
  },

  async scanDemoLibrary(): Promise<{ status: string; folder_path: string; stats: LibraryStats }> {
    const res = await fetch(`${API_BASE}/api/scan/demo`, { method: 'POST' });
    return res.json();
  },

  async scanPlaceholder300(
    sync = false
  ): Promise<{
    status: string;
    folder_path: string;
    total_generated: number;
    scan_status: ScanStatus;
    stats?: LibraryStats;
  }> {
    const res = await fetch(`${API_BASE}/api/scan/placeholder-300?sync=${sync}`, {
      method: 'POST',
    });
    return res.json();
  },

  async cancelScan(): Promise<ScanStatus> {
    const res = await fetch(`${API_BASE}/api/scan/cancel`, { method: 'POST' });
    return res.json();
  },

  async getScanStatus(): Promise<ScanStatus> {
    const res = await fetch(`${API_BASE}/api/scan/status`);
    return res.json();
  },

  async exportAllXmp(): Promise<{ status: string; count: number }> {
    const res = await fetch(`${API_BASE}/api/xmp/export-all`, { method: 'POST' });
    return res.json();
  },

  async importAllXmp(): Promise<{ status: string; count: number }> {
    const res = await fetch(`${API_BASE}/api/xmp/import-all`, { method: 'POST' });
    return res.json();
  },

  async getPhotoXmp(
    photoId: number
  ): Promise<{ exists: boolean; path: string; content?: string; error?: string }> {
    const res = await fetch(`${API_BASE}/api/photos/${photoId}/xmp`);
    return res.json();
  },

  async getSettings(): Promise<SettingsModel> {
    const res = await fetch(`${API_BASE}/api/settings`);
    return res.json();
  },

  async updateSettings(settings: SettingsModel): Promise<SettingsModel> {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return res.json();
  },
};
