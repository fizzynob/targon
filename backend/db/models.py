from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TagInfo(BaseModel):
    id: int
    name: str
    tag_type: str  # 'identity' | 'category' | 'scene' | 'attribute' | 'user'
    confidence: float = 1.0
    source: str = "ai"


class PhotoSubjectInfo(BaseModel):
    id: int
    subject_id: int
    subject_name: Optional[str] = None
    display_name: str
    category: str
    bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 1.0, 1.0])  # [ymin, xmin, ymax, xmax] normalized 0..1
    confidence: float = 1.0
    crop_url: Optional[str] = None
    is_named: bool = False


class PhotoItem(BaseModel):
    id: int
    path: str
    filename: str
    folder_id: Optional[int] = None
    width: int = 0
    height: int = 0
    file_size: int = 0
    date_taken: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    iso: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    dominant_color: Optional[str] = "#E5E5EA"
    is_favorite: bool = False
    is_game_asset: bool = False
    rating: int = 0
    rotation: int = 0
    ai_processed: bool = False
    ai_description: Optional[str] = None
    ai_engine_used: Optional[str] = "local"
    face_count: int = 0
    face_boxes: List[Dict[str, Any]] = Field(default_factory=list)
    ocr_text: Optional[str] = None
    thumbnail_url: str
    preview_url: str
    original_url: str
    tags: List[TagInfo] = Field(default_factory=list)
    subjects: List[PhotoSubjectInfo] = Field(default_factory=list)
    created_at: Optional[str] = None


class SubjectItem(BaseModel):
    id: int
    name: Optional[str] = None
    display_name: str
    category: str
    avatar_url: Optional[str] = None
    photo_count: int = 0
    is_named: bool = False
    is_favorite: bool = False
    sample_photos: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class FolderItem(BaseModel):
    id: int
    path: str
    name: str
    photo_count: int = 0
    last_scanned: Optional[str] = None
    watch_enabled: bool = True


class ScanStatus(BaseModel):
    status: str  # 'idle' | 'indexing' | 'analyzing' | 'completed' | 'error'
    current_folder: Optional[str] = None
    current_file: Optional[str] = None
    total_files: int = 0
    indexed_files: int = 0
    analyzed_files: int = 0
    progress_percent: float = 0.0
    speed_fps: float = 0.0
    error_message: Optional[str] = None
    ai_mode: str = "local"


class SettingsModel(BaseModel):
    ai_mode: str = "local"  # 'local' | 'hybrid' | 'cloud'
    tag_storage_mode: str = "both"  # 'sidecar' | 'database' | 'both'
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    similarity_threshold: float = 0.76
    watch_folders: bool = True
    auto_cluster: bool = True
    game_detection: bool = True
    sound_effects: bool = True
    low_spec_mode: bool = False
    scan_threads: int = 4
    fast_tagging: bool = True
    enable_clip_search: bool = True
    enable_ocr: bool = True
    enable_face_detection: bool = True
    enable_scene_analysis: bool = True
    thumbnail_quality: str = "balanced"  # 'fast' | 'balanced' | 'high'
    skip_small_images: bool = True
    default_grid_cols: int = 4
    group_by_date_default: bool = True
    reduce_motion: bool = False
    show_card_tags: bool = True
    confirm_before_delete: bool = False
    ppapi_status: Optional[Dict[str, Any]] = None


class RenameSubjectRequest(BaseModel):
    name: str
    category: Optional[str] = None


class MergeSubjectsRequest(BaseModel):
    source_subject_id: int
    target_subject_id: int


class ReassignPhotoSubjectRequest(BaseModel):
    new_name: str
    category: Optional[str] = None


class AddTagRequest(BaseModel):
    name: str
    tag_type: str = "user"


class StartScanRequest(BaseModel):
    folder_path: str
    recursive: bool = True


class BatchDeletePhotosRequest(BaseModel):
    photo_ids: List[int]
    delete_files: bool = False


class ClearLibraryRequest(BaseModel):
    delete_files: bool = False


class SetRatingRequest(BaseModel):
    rating: int = 0


class RotatePhotoRequest(BaseModel):
    degrees: int = 90


class BatchTagRequest(BaseModel):
    photo_ids: List[int]
    tag_name: str
    tag_type: str = "user"


class BatchRatingRequest(BaseModel):
    photo_ids: List[int]
    rating: int = 0

