export interface FaceBox {
  bbox: [number, number, number, number];
  confidence: number;
  face_type: 'human_face' | 'pet_face';
  is_portrait?: boolean;
}

export interface TagInfo {
  id: number;
  name: string;
  tag_type: 'identity' | 'category' | 'scene' | 'attribute' | 'user';
  confidence: number;
  source: string;
  count?: number;
}

export interface PhotoSubjectInfo {
  id: number;
  subject_id: number;
  subject_name: string | null;
  display_name: string;
  category: string;
  bbox: [number, number, number, number]; // [ymin, xmin, ymax, xmax]
  confidence: number;
  crop_url: string | null;
  is_named: boolean;
}

export interface PhotoRootSystems {
  type_root: {
    specific: string;
    category: string;
    super_type: string;
    chain: [string, string, string]; // e.g. ["Blu", "Cat", "Animal"]
  };
  drive_root: {
    subfolder: string;
    folder: string;
    drive: string;
    chain: [string, string, string]; // e.g. ["Cats_Blu", "sample_drive_photos", "C:"]
  };
  device_root: {
    device: string;
    date_taken: string;
    capture_date: string;
    image_type: string;
    chain: [string, string, string]; // e.g. ["Apple iPhone 16 Pro", "2026-10-20 14:15", "JPEG"]
  };
}

export interface PhotoItem {
  id: number;
  path: string;
  filename: string;
  folder_id: number | null;
  width: number;
  height: number;
  file_size: number;
  image_type: string;
  drive_root: string;
  folder_name: string;
  subfolder_name: string;
  date_taken: string | null;
  camera_make: string | null;
  camera_model: string | null;
  device_name: string;
  iso: string | null;
  focal_length: string | null;
  aperture: string | null;
  shutter_speed: string | null;
  dominant_color: string;
  is_favorite: boolean;
  is_game_asset?: boolean;
  rating?: number;
  rotation?: number;
  ai_processed: boolean;
  ai_description: string | null;
  ai_engine_used: string;
  face_count?: number;
  face_boxes?: FaceBox[];
  ocr_text?: string | null;
  thumbnail_url: string;
  preview_url: string;
  original_url: string;
  tags: TagInfo[];
  subjects: PhotoSubjectInfo[];
  root_systems: PhotoRootSystems;
  created_at: string | null;
}

export interface SubjectItem {
  id: number;
  name: string | null;
  display_name: string;
  category: string;
  super_type?: string;
  type_chain?: string[];
  avatar_url: string | null;
  photo_count: number;
  is_named: boolean;
  is_favorite: boolean;
  sample_photos: string[];
  created_at: string | null;
}

export interface ThreeRootTrees {
  type_tree: Array<{
    name: string; // SuperType e.g. "Animal"
    count: number;
    categories: Array<{
      name: string; // Category e.g. "Cat"
      count: number;
      individuals: Array<{
        name: string; // Specific e.g. "Blu"
        subject_id: number | null;
        count: number;
      }>;
    }>;
  }>;
  drive_tree: Array<{
    name: string; // Drive e.g. "C:"
    count: number;
    folders: Array<{
      name: string; // Folder e.g. "sample_drive_photos"
      count: number;
      subfolders: Array<{
        name: string; // Subfolder e.g. "Cats_Blu"
        count: number;
      }>;
    }>;
  }>;
  device_tree: Array<{
    name: string; // Device e.g. "Apple iPhone 16 Pro"
    count: number;
    dates: Array<{
      date: string; // e.g. "2026-10-20"
      count: number;
      types: Array<{
        image_type: string; // e.g. "JPEG"
        count: number;
      }>;
    }>;
    image_types: Array<{
      image_type: string;
      count: number;
    }>;
  }>;
}

export interface FolderItem {
  id: number;
  path: string;
  name: string;
  photo_count: number;
  last_scanned: string | null;
  watch_enabled: boolean;
}

export interface ScanStatus {
  status: 'idle' | 'indexing' | 'analyzing' | 'completed' | 'error';
  current_folder: string | null;
  current_file: string | null;
  total_files: number;
  indexed_files: number;
  analyzed_files: number;
  progress_percent: number;
  speed_fps: number;
  error_message: string | null;
  ai_mode: 'local' | 'hybrid' | 'cloud';
}

export interface SettingsModel {
  ai_mode: 'local' | 'hybrid' | 'cloud';
  tag_storage_mode: 'sidecar' | 'database' | 'both';
  gemini_api_key: string;
  gemini_model: string;
  similarity_threshold: number;
  watch_folders: boolean;
  auto_cluster: boolean;
  game_detection?: boolean;
  sound_effects?: boolean;
  low_spec_mode?: boolean;
  scan_threads?: number;
  fast_tagging?: boolean;
  enable_clip_search?: boolean;
  enable_ocr?: boolean;
  enable_face_detection?: boolean;
  enable_scene_analysis?: boolean;
  thumbnail_quality?: 'fast' | 'balanced' | 'high';
  skip_small_images?: boolean;
  default_grid_cols?: number;
  group_by_date_default?: boolean;
  reduce_motion?: boolean;
  show_card_tags?: boolean;
  confirm_before_delete?: boolean;
  ppapi_status?: {
    vault_type: string;
    is_available: boolean;
    has_key: boolean;
    masked_key: string;
    vault_path: string;
  };
}

export interface LibraryStats {
  total_photos: number;
  analyzed_photos: number;
  favorites: number;
  total_subjects: number;
  named_subjects: number;
  total_tags: number;
}

export interface DriveQuickFolder {
  name: string;
  path: string;
  type: 'demo' | 'user' | 'drive';
}

declare global {
  interface Window {
    targonDesktop?: {
      isElectron: boolean;
      minimize: () => Promise<void>;
      maximize: () => Promise<boolean>;
      close: () => Promise<void>;
      selectFolder: () => Promise<string | null>;
    };
  }
}
