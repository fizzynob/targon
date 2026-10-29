import os
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

from backend.scanner.metadata import parse_drive_hierarchy, IMAGE_TYPE_LABELS
from backend.scanner.xmp_sidecar import write_xmp_sidecar, read_xmp_sidecar, get_xmp_path
from backend.security.vault import vault


SUPER_TYPE_BY_CATEGORY = {
    "cat": "Animal",
    "dog": "Animal",
    "bird": "Animal",
    "animal": "Animal",
    "wildlife": "Animal",
    "pet": "Animal",
    "feline": "Animal",
    "canine": "Animal",
    "mammal": "Animal",
    "reptile": "Animal",
    "amphibian": "Animal",
    "marine life": "Animal",
    "aquatic": "Animal",
    "insect": "Animal",
    "person": "People",
    "people": "People",
    "portrait": "People",
    "selfie": "People",
    "group photo": "People",
    "mountain": "Nature",
    "lakeside": "Nature",
    "seashore": "Nature",
    "valley": "Nature",
    "cliff": "Nature",
    "beach": "Nature",
    "ocean": "Nature",
    "coast": "Nature",
    "nature": "Nature",
    "landscape": "Nature",
    "botanical": "Nature",
    "snow": "Nature",
    "water": "Nature",
    "sky": "Nature",
    "architecture": "Architecture & Places",
    "structure": "Architecture & Places",
    "building": "Architecture & Places",
    "castle": "Architecture & Places",
    "character art": "Art & Media",
    "historical art": "Art & Media",
    "artwork": "Art & Media",
    "illustration": "Art & Media",
    "food": "Lifestyle",
    "apparel": "Lifestyle",
    "fashion": "Lifestyle",
    "sports & recreation": "Lifestyle",
    "indoor": "Interior",
    "interior": "Interior",
    "vehicle": "Transport",
    "transport": "Transport",
    "electronics": "Technology",
    "technology": "Technology",
    "instrument": "Technology",
    "audio": "Technology",
    "equipment": "Technology",
    "document": "Documents & Text",
    "media & print": "Documents & Text",
    "screenshot": "Documents & Text",
}


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent / ".targon_cache"
            base_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(base_dir / "targon_library.db")
        self.db_path = db_path
        self._lock = threading.RLock()
        self._settings_cache: Optional[Dict[str, Any]] = None
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA cache_size=-32000;")
        conn.execute("PRAGMA mmap_size=134217728;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS folders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        watch_enabled INTEGER DEFAULT 1,
                        last_scanned TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS photos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT UNIQUE NOT NULL,
                        filename TEXT NOT NULL,
                        folder_id INTEGER,
                        file_hash TEXT,
                        width INTEGER DEFAULT 0,
                        height INTEGER DEFAULT 0,
                        file_size INTEGER DEFAULT 0,
                        image_type TEXT DEFAULT 'JPEG',
                        drive_root TEXT DEFAULT 'C:',
                        folder_name TEXT DEFAULT 'Root',
                        subfolder_name TEXT DEFAULT 'Root',
                        date_taken TEXT,
                        camera_make TEXT,
                        camera_model TEXT,
                        device_name TEXT DEFAULT 'Unknown Device',
                        iso TEXT,
                        focal_length TEXT,
                        aperture TEXT,
                        shutter_speed TEXT,
                        dominant_color TEXT DEFAULT '#E5E5EA',
                        thumbnail_path TEXT,
                        preview_path TEXT,
                        is_favorite INTEGER DEFAULT 0,
                        ai_processed INTEGER DEFAULT 0,
                        ai_description TEXT,
                        ai_engine_used TEXT DEFAULT 'local',
                        scene_embedding TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
                    );

                    CREATE TABLE IF NOT EXISTS subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        display_name TEXT NOT NULL,
                        category TEXT NOT NULL DEFAULT 'pet',
                        avatar_path TEXT,
                        centroid_vector TEXT,
                        is_named INTEGER DEFAULT 0,
                        is_favorite INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS photo_subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        photo_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        bbox_ymin REAL DEFAULT 0.0,
                        bbox_xmin REAL DEFAULT 0.0,
                        bbox_ymax REAL DEFAULT 1.0,
                        bbox_xmax REAL DEFAULT 1.0,
                        confidence REAL DEFAULT 1.0,
                        embedding_vector TEXT,
                        crop_path TEXT,
                        FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        tag_type TEXT NOT NULL DEFAULT 'category',
                        UNIQUE(name, tag_type)
                    );

                    CREATE TABLE IF NOT EXISTS photo_tags (
                        photo_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source TEXT DEFAULT 'ai',
                        PRIMARY KEY (photo_id, tag_id),
                        FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_photos_folder ON photos(folder_id);
                    CREATE INDEX IF NOT EXISTS idx_photos_hash ON photos(file_hash);
                    CREATE INDEX IF NOT EXISTS idx_photo_subjects_photo ON photo_subjects(photo_id);
                    CREATE INDEX IF NOT EXISTS idx_photo_subjects_subject ON photo_subjects(subject_id);
                    CREATE INDEX IF NOT EXISTS idx_photo_tags_photo ON photo_tags(photo_id);
                    CREATE INDEX IF NOT EXISTS idx_photo_tags_tag ON photo_tags(tag_id);
                    """
                )

                # Safe schema migration for any existing database
                existing_cols = {
                    r["name"] for r in conn.execute("PRAGMA table_info(photos)").fetchall()
                }
                migrations = [
                    ("image_type", "TEXT DEFAULT 'JPEG'"),
                    ("drive_root", "TEXT DEFAULT 'C:'"),
                    ("folder_name", "TEXT DEFAULT 'Root'"),
                    ("subfolder_name", "TEXT DEFAULT 'Root'"),
                    ("device_name", "TEXT DEFAULT 'Unknown Device'"),
                    ("face_count", "INTEGER DEFAULT 0"),
                    ("face_boxes", "TEXT"),
                    ("ocr_text", "TEXT"),
                    ("is_game_asset", "INTEGER DEFAULT 0"),
                    ("rating", "INTEGER DEFAULT 0"),
                    ("rotation", "INTEGER DEFAULT 0"),
                ]
                for col_name, col_def in migrations:
                    if col_name not in existing_cols:
                        conn.execute(f"ALTER TABLE photos ADD COLUMN {col_name} {col_def}")

                defaults = {
                    "ai_mode": "local",
                    "tag_storage_mode": "both",
                    "gemini_model": "gemini-2.5-flash",
                    "similarity_threshold": "0.76",
                    "watch_folders": "true",
                    "auto_cluster": "true",
                    "game_detection": "1",
                    "sound_effects": "1",
                    "low_spec_mode": "false",
                    "scan_threads": "4",
                    "fast_tagging": "true",
                    "enable_clip_search": "true",
                    "enable_ocr": "true",
                    "enable_face_detection": "true",
                    "enable_scene_analysis": "true",
                    "thumbnail_quality": "balanced",
                    "skip_small_images": "true",
                    "default_grid_cols": "4",
                    "group_by_date_default": "true",
                    "reduce_motion": "false",
                    "show_card_tags": "true",
                    "confirm_before_delete": "false",
                }
                for k, v in defaults.items():
                    conn.execute(
                        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                        (k, v),
                    )
                conn.commit()
            finally:
                conn.close()

    # --- Settings (Integrated with Windows PPAPI / DPAPI Vault) ---
    def get_settings(self) -> Dict[str, Any]:
        with self._lock:
            if self._settings_cache is not None:
                return dict(self._settings_cache)
            conn = self._get_conn()
            try:
                rows = conn.execute("SELECT key, value FROM settings").fetchall()
                raw = {r["key"]: r["value"] for r in rows}
                ppapi_key = vault.get_gemini_api_key()
                res = {
                    "ai_mode": raw.get("ai_mode", "local"),
                    "tag_storage_mode": raw.get("tag_storage_mode", "both"),
                    "gemini_api_key": ppapi_key,
                    "gemini_model": raw.get("gemini_model", "gemini-2.5-flash"),
                    "similarity_threshold": float(raw.get("similarity_threshold", 0.76)),
                    "watch_folders": raw.get("watch_folders", "true").lower() in ("1", "true"),
                    "auto_cluster": raw.get("auto_cluster", "true").lower() in ("1", "true"),
                    "game_detection": raw.get("game_detection", "1").lower() in ("1", "true"),
                    "sound_effects": raw.get("sound_effects", "1").lower() in ("1", "true"),
                    "low_spec_mode": raw.get("low_spec_mode", "false").lower() in ("1", "true"),
                    "scan_threads": max(1, min(8, int(raw.get("scan_threads", 4)))),
                    "fast_tagging": raw.get("fast_tagging", "true").lower() in ("1", "true"),
                    "enable_clip_search": raw.get("enable_clip_search", "true").lower() in ("1", "true"),
                    "enable_ocr": raw.get("enable_ocr", "true").lower() in ("1", "true"),
                    "enable_face_detection": raw.get("enable_face_detection", "true").lower() in ("1", "true"),
                    "enable_scene_analysis": raw.get("enable_scene_analysis", "true").lower() in ("1", "true"),
                    "thumbnail_quality": raw.get("thumbnail_quality", "balanced"),
                    "skip_small_images": raw.get("skip_small_images", "true").lower() in ("1", "true"),
                    "default_grid_cols": max(2, min(6, int(raw.get("default_grid_cols", 4)))),
                    "group_by_date_default": raw.get("group_by_date_default", "true").lower() in ("1", "true"),
                    "reduce_motion": raw.get("reduce_motion", "false").lower() in ("1", "true"),
                    "show_card_tags": raw.get("show_card_tags", "true").lower() in ("1", "true"),
                    "confirm_before_delete": raw.get("confirm_before_delete", "false").lower() in ("1", "true"),
                    "ppapi_status": vault.get_status(),
                }
                self._settings_cache = res
                return dict(res)
            finally:
                conn.close()

    def update_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Always intercept and protect Gemini API Key in the local PPAPI/DPAPI vault
        if "gemini_api_key" in data:
            new_key = str(data["gemini_api_key"]).strip()
            vault.save_gemini_api_key(new_key)
            data = {k: v for k, v in data.items() if k != "gemini_api_key"}

        with self._lock:
            self._settings_cache = None
            conn = self._get_conn()
            try:
                for k, v in data.items():
                    if k == "ppapi_status" or v is None:
                        continue
                    val_str = str(v).lower() if isinstance(v, bool) else str(v)
                    conn.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (k, val_str),
                    )
                conn.commit()
            finally:
                conn.close()
        return self.get_settings()

    # --- Folders ---
    def upsert_folder(self, folder_path: str, watch_enabled: bool = True) -> int:
        norm_path = str(Path(folder_path).resolve())
        name = Path(norm_path).name or norm_path
        now = datetime.now().isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO folders (path, name, watch_enabled, last_scanned)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET last_scanned=excluded.last_scanned
                    """,
                    (norm_path, name, 1 if watch_enabled else 0, now),
                )
                conn.commit()
                row = conn.execute("SELECT id FROM folders WHERE path = ?", (norm_path,)).fetchone()
                return row["id"]
            finally:
                conn.close()

    def get_folders(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    """
                    SELECT f.*, COUNT(p.id) as photo_count
                    FROM folders f
                    LEFT JOIN photos p ON p.folder_id = f.id
                    GROUP BY f.id
                    ORDER BY f.created_at DESC
                    """
                ).fetchall()
                return [
                    {
                        "id": r["id"],
                        "path": r["path"],
                        "name": r["name"],
                        "photo_count": r["photo_count"],
                        "last_scanned": r["last_scanned"],
                        "watch_enabled": bool(r["watch_enabled"]),
                    }
                    for r in rows
                ]
            finally:
                conn.close()

    def delete_folder(self, folder_id: int):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
                conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
                conn.execute(
                    "DELETE FROM subjects WHERE id NOT IN (SELECT DISTINCT subject_id FROM photo_subjects)"
                )
                conn.commit()
            finally:
                conn.close()

    # --- Photos ---
    def get_photo_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        norm_path = str(Path(path).resolve())
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM photos WHERE path = ?", (norm_path,)).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def upsert_photo(self, photo_data: Dict[str, Any]) -> int:
        norm_path = str(Path(photo_data["path"]).resolve())
        ext = Path(norm_path).suffix.lower()
        img_type = photo_data.get("image_type") or IMAGE_TYPE_LABELS.get(ext, "JPEG")
        drive_info = parse_drive_hierarchy(norm_path)
        is_game = int(bool(photo_data.get("is_game_asset", 0)))

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO photos (
                        path, filename, folder_id, file_hash, width, height, file_size,
                        image_type, drive_root, folder_name, subfolder_name,
                        date_taken, camera_make, camera_model, device_name,
                        iso, focal_length, aperture, shutter_speed,
                        dominant_color, thumbnail_path, preview_path, is_game_asset
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        file_hash=excluded.file_hash,
                        width=excluded.width,
                        height=excluded.height,
                        file_size=excluded.file_size,
                        image_type=excluded.image_type,
                        drive_root=excluded.drive_root,
                        folder_name=excluded.folder_name,
                        subfolder_name=excluded.subfolder_name,
                        date_taken=excluded.date_taken,
                        camera_make=excluded.camera_make,
                        camera_model=excluded.camera_model,
                        device_name=excluded.device_name,
                        thumbnail_path=excluded.thumbnail_path,
                        preview_path=excluded.preview_path,
                        dominant_color=excluded.dominant_color,
                        is_game_asset=excluded.is_game_asset
                    """,
                    (
                        norm_path,
                        photo_data.get("filename", Path(norm_path).name),
                        photo_data.get("folder_id"),
                        photo_data.get("file_hash"),
                        photo_data.get("width", 0),
                        photo_data.get("height", 0),
                        photo_data.get("file_size", 0),
                        img_type,
                        photo_data.get("drive_root") or drive_info["drive_root"],
                        photo_data.get("folder_name") or drive_info["folder_name"],
                        photo_data.get("subfolder_name") or drive_info["subfolder_name"],
                        photo_data.get("date_taken"),
                        photo_data.get("camera_make"),
                        photo_data.get("camera_model"),
                        photo_data.get("device_name") or "Unknown Device",
                        photo_data.get("iso"),
                        photo_data.get("focal_length"),
                        photo_data.get("aperture"),
                        photo_data.get("shutter_speed"),
                        photo_data.get("dominant_color", "#E5E5EA"),
                        photo_data.get("thumbnail_path"),
                        photo_data.get("preview_path"),
                        is_game,
                    ),
                )
                conn.commit()
                row = conn.execute("SELECT id FROM photos WHERE path = ?", (norm_path,)).fetchone()
                return row["id"]
            finally:
                conn.close()

    def mark_photo_ai_processed(
        self,
        photo_id: int,
        description: Optional[str] = None,
        engine_used: str = "local",
        scene_embedding: Optional[List[float]] = None,
        face_count: int = 0,
        face_boxes: Optional[List[Dict[str, Any]]] = None,
        ocr_text: Optional[str] = None,
        sync_xmp: bool = True,
    ):
        emb_json = json.dumps(scene_embedding, default=float) if scene_embedding is not None else None
        faces_json = json.dumps(face_boxes, default=float) if face_boxes is not None else None
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    UPDATE photos
                    SET ai_processed = 1,
                        ai_description = COALESCE(?, ai_description),
                        ai_engine_used = ?,
                        scene_embedding = COALESCE(?, scene_embedding),
                        face_count = ?,
                        face_boxes = COALESCE(?, face_boxes),
                        ocr_text = COALESCE(?, ocr_text)
                    WHERE id = ?
                    """,
                    (description, engine_used, emb_json, face_count, faces_json, ocr_text, photo_id),
                )
                conn.commit()
            finally:
                conn.close()
        if sync_xmp:
            self.sync_photo_xmp_sidecar(photo_id)

    def delete_photo(self, photo_id: int, delete_file: bool = False) -> bool:
        """
        Deletes a single photo from Targon's database, including its tag associations,
        subject links, and cached thumbnails. If delete_file=True, also removes the source file.
        """
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT path, thumbnail_path, preview_path FROM photos WHERE id = ?",
                    (photo_id,),
                ).fetchone()
                if not row:
                    return False

                file_path = row["path"]
                thumb_path = row["thumbnail_path"]
                prev_path = row["preview_path"]

                conn.execute("DELETE FROM photo_subjects WHERE photo_id = ?", (photo_id,))
                conn.execute("DELETE FROM photo_tags WHERE photo_id = ?", (photo_id,))
                conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
                conn.commit()

                # Remove cached previews/thumbnails
                for p in (thumb_path, prev_path):
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass

                if delete_file and file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                return True
            finally:
                conn.close()

    def delete_photos(self, photo_ids: List[int], delete_file: bool = False) -> int:
        """Deletes a batch of photos."""
        deleted = 0
        for pid in photo_ids:
            if self.delete_photo(pid, delete_file=delete_file):
                deleted += 1
        return deleted

    def clear_library(self, delete_files: bool = False) -> Dict[str, Any]:
        """
        Clears all indexed photos, subjects, and tags from Targon.
        Source files on the user's drives remain completely untouched unless delete_files=True.
        """
        with self._lock:
            conn = self._get_conn()
            try:
                photo_count = conn.execute("SELECT COUNT(*) as c FROM photos").fetchone()["c"]
                subject_count = conn.execute("SELECT COUNT(*) as c FROM subjects").fetchone()["c"]

                if delete_files:
                    rows = conn.execute("SELECT path FROM photos").fetchall()
                    for r in rows:
                        fp = r["path"]
                        if fp and os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except Exception:
                                pass

                # Remove thumbnail caches
                thumb_rows = conn.execute("SELECT thumbnail_path, preview_path FROM photos").fetchall()
                for tr in thumb_rows:
                    for p in (tr["thumbnail_path"], tr["preview_path"]):
                        if p and os.path.exists(p):
                            try:
                                os.remove(p)
                            except Exception:
                                pass

                # Purge database tables
                conn.execute("DELETE FROM photo_subjects")
                conn.execute("DELETE FROM photo_tags")
                conn.execute("DELETE FROM photos")
                conn.execute("DELETE FROM subjects")
                conn.execute("DELETE FROM tags")
                conn.execute("DELETE FROM folders")
                conn.commit()

                return {
                    "cleared_photos": photo_count,
                    "cleared_subjects": subject_count,
                    "status": "success",
                }
            finally:
                conn.close()

    def reset_ai_analysis(self) -> List[Dict[str, Any]]:
        """
        Resets AI-generated tags and unnamed subject clusters across all photos so they can be
        freshly re-analyzed with the latest neural recognition pipeline.
        """
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM photo_tags WHERE source = 'ai'")
                conn.execute("DELETE FROM photo_subjects")
                conn.execute("DELETE FROM subjects WHERE is_named = 0")
                conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM photo_tags)")
                conn.execute("UPDATE photos SET ai_processed = 0, ai_description = NULL")
                rows = conn.execute("SELECT id, path, file_hash FROM photos").fetchall()
                conn.commit()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def toggle_favorite_photo(self, photo_id: int) -> bool:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT is_favorite FROM photos WHERE id = ?", (photo_id,)).fetchone()
                if not row:
                    return False
                new_val = 0 if row["is_favorite"] else 1
                conn.execute("UPDATE photos SET is_favorite = ? WHERE id = ?", (new_val, photo_id))
                conn.commit()
                return bool(new_val)
            finally:
                conn.close()

    def set_photo_rating(self, photo_id: int, rating: int) -> int:
        clamped = max(0, min(5, int(rating)))
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("UPDATE photos SET rating = ? WHERE id = ?", (clamped, photo_id))
                conn.commit()
                return clamped
            finally:
                conn.close()

    def rotate_photo(self, photo_id: int, degrees: int = 90) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT COALESCE(rotation, 0) as rot FROM photos WHERE id = ?", (photo_id,)).fetchone()
                if not row:
                    return 0
                current = int(row["rot"] or 0)
                new_rot = (current + int(degrees)) % 360
                conn.execute("UPDATE photos SET rotation = ? WHERE id = ?", (new_rot, photo_id))
                conn.commit()
                return new_rot
            finally:
                conn.close()

    def batch_add_tag(self, photo_ids: List[int], tag_name: str, tag_type: str = "user") -> int:
        clean_name = tag_name.strip()
        if not clean_name or not photo_ids:
            return 0
        count = 0
        for pid in photo_ids:
            self.add_photo_tag(pid, clean_name, tag_type=tag_type, confidence=1.0, source="user")
            count += 1
        return count

    def batch_set_rating(self, photo_ids: List[int], rating: int) -> int:
        clamped = max(0, min(5, int(rating)))
        if not photo_ids:
            return 0
        with self._lock:
            conn = self._get_conn()
            try:
                ph = ",".join(["?"] * len(photo_ids))
                conn.execute(f"UPDATE photos SET rating = ? WHERE id IN ({ph})", [clamped] + photo_ids)
                conn.commit()
                return len(photo_ids)
            finally:
                conn.close()

    # --- Tags ---
    def add_photo_tag(
        self,
        photo_id: int,
        tag_name: str,
        tag_type: str = "category",
        confidence: float = 1.0,
        source: str = "ai",
        sync_xmp: bool = True,
    ):
        clean_name = tag_name.strip()
        if not clean_name:
            return
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO tags (name, tag_type) VALUES (?, ?)",
                    (clean_name, tag_type),
                )
                tag_row = conn.execute(
                    "SELECT id FROM tags WHERE name = ? AND tag_type = ?",
                    (clean_name, tag_type),
                ).fetchone()
                if tag_row:
                    conn.execute(
                        """
                        INSERT INTO photo_tags (photo_id, tag_id, confidence, source)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(photo_id, tag_id) DO UPDATE SET
                            confidence = MAX(photo_tags.confidence, excluded.confidence)
                        """,
                        (photo_id, tag_row["id"], confidence, source),
                    )
                conn.commit()
            finally:
                conn.close()
        if sync_xmp:
            self.sync_photo_xmp_sidecar(photo_id)

    def add_photo_tags_batch(
        self,
        photo_id: int,
        tags_list: List[Any],
        sync_xmp: bool = False,
    ):
        """
        Inserts multiple tags for a photo in a single transaction.
        Each item in tags_list can be (tag_name, tag_type, confidence) or (tag_name, tag_type, confidence, source).
        """
        if not tags_list:
            return
        with self._lock:
            conn = self._get_conn()
            try:
                for item in tags_list:
                    if len(item) == 4:
                        raw_name, tag_type, conf, source = item
                    else:
                        raw_name, tag_type, conf = item
                        source = "ai"
                    clean_name = str(raw_name).strip()
                    if not clean_name:
                        continue
                    conn.execute(
                        "INSERT OR IGNORE INTO tags (name, tag_type) VALUES (?, ?)",
                        (clean_name, tag_type),
                    )
                    tag_row = conn.execute(
                        "SELECT id FROM tags WHERE name = ? AND tag_type = ?",
                        (clean_name, tag_type),
                    ).fetchone()
                    if tag_row:
                        conn.execute(
                            """
                            INSERT INTO photo_tags (photo_id, tag_id, confidence, source)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(photo_id, tag_id) DO UPDATE SET
                                confidence = MAX(photo_tags.confidence, excluded.confidence)
                            """,
                            (photo_id, tag_row["id"], float(conf), source),
                        )
                conn.commit()
            finally:
                conn.close()
        if sync_xmp:
            self.sync_photo_xmp_sidecar(photo_id)

    def remove_photo_tag(self, photo_id: int, tag_id: int):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "DELETE FROM photo_tags WHERE photo_id = ? AND tag_id = ?",
                    (photo_id, tag_id),
                )
                conn.commit()
            finally:
                conn.close()
        self.sync_photo_xmp_sidecar(photo_id)

    def sync_photo_xmp_sidecar(self, photo_id: int):
        settings = self.get_settings()
        mode = settings.get("tag_storage_mode", "both")
        if mode not in ("sidecar", "both"):
            return
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
                if not row:
                    return
                r_dict = dict(row)
                tag_rows = conn.execute(
                    """
                    SELECT t.name, t.tag_type, pt.confidence, pt.source
                    FROM photo_tags pt
                    JOIN tags t ON t.id = pt.tag_id
                    WHERE pt.photo_id = ?
                    """,
                    (photo_id,),
                ).fetchall()
                tags = [dict(t) for t in tag_rows]

                subj_rows = conn.execute(
                    """
                    SELECT ps.*, s.name as subject_name, s.display_name, s.category, s.is_named
                    FROM photo_subjects ps
                    JOIN subjects s ON s.id = ps.subject_id
                    WHERE ps.photo_id = ?
                    """,
                    (photo_id,),
                ).fetchall()
                subjects = [dict(s) for s in subj_rows]
            finally:
                conn.close()

        root_systems = self._build_photo_root_systems(r_dict, subjects, tags)
        try:
            write_xmp_sidecar(
                image_path=r_dict["path"],
                description=r_dict.get("ai_description"),
                tags=tags,
                root_systems=root_systems,
            )
        except Exception:
            pass

    def export_all_xmp_sidecars(self) -> int:
        """Exports tags for every photo in the library to standard .xmp sidecar files on disk."""
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute("SELECT id FROM photos").fetchall()
                photo_ids = [r["id"] for r in rows]
            finally:
                conn.close()

        count = 0
        for pid in photo_ids:
            try:
                self.sync_photo_xmp_sidecar(pid)
                count += 1
            except Exception:
                pass
        return count

    def import_all_xmp_sidecars(self) -> int:
        """Reads tags from any existing .xmp sidecars on disk and syncs them into the database."""
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute("SELECT id, path FROM photos").fetchall()
                photo_data = [(r["id"], r["path"]) for r in rows]
            finally:
                conn.close()

        count = 0
        for pid, path in photo_data:
            xmp_info = read_xmp_sidecar(path)
            if xmp_info and xmp_info.get("tags"):
                for t_name in xmp_info["tags"]:
                    self.add_photo_tag(
                        pid, t_name, tag_type="user", confidence=1.0, source="xmp"
                    )
                count += 1
        return count

    def get_all_tags(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    """
                    SELECT t.id, t.name, t.tag_type, COUNT(pt.photo_id) as count
                    FROM tags t
                    JOIN photo_tags pt ON pt.tag_id = t.id
                    GROUP BY t.id
                    HAVING count > 0
                    ORDER BY
                        CASE t.tag_type
                            WHEN 'identity' THEN 1
                            WHEN 'category' THEN 2
                            WHEN 'scene' THEN 3
                            WHEN 'attribute' THEN 4
                            ELSE 5
                        END,
                        count DESC,
                        t.name ASC
                    """
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    # --- Subjects & Pet Re-Identification ---
    def get_all_subjects_with_vectors(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    """
                    SELECT s.*, COUNT(DISTINCT ps.photo_id) as photo_count
                    FROM subjects s
                    LEFT JOIN photo_subjects ps ON ps.subject_id = s.id
                    GROUP BY s.id
                    ORDER BY s.is_named DESC, photo_count DESC, s.id ASC
                    """
                ).fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if d.get("centroid_vector"):
                        try:
                            d["centroid"] = np.array(json.loads(d["centroid_vector"]), dtype=np.float32)
                        except Exception:
                            d["centroid"] = None
                    else:
                        d["centroid"] = None
                    result.append(d)
                return result
            finally:
                conn.close()

    def create_subject(
        self,
        category: str,
        centroid_vector: List[float],
        avatar_path: Optional[str] = None,
        name: Optional[str] = None,
    ) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                if name:
                    display_name = name
                    is_named = 1
                else:
                    cat_label = category.capitalize()
                    cnt_row = conn.execute(
                        "SELECT COUNT(*) as c FROM subjects WHERE category = ?", (category,)
                    ).fetchone()
                    idx = (cnt_row["c"] if cnt_row else 0) + 1
                    display_name = f"Unnamed {cat_label} #{idx}"
                    is_named = 0

                conn.execute(
                    """
                    INSERT INTO subjects (name, display_name, category, avatar_path, centroid_vector, is_named)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        display_name,
                        category,
                        avatar_path,
                        json.dumps(centroid_vector),
                        is_named,
                    ),
                )
                conn.commit()
                return conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            finally:
                conn.close()

    def link_photo_subject(
        self,
        photo_id: int,
        subject_id: int,
        bbox: List[float],
        confidence: float,
        embedding_vector: List[float],
        crop_path: Optional[str] = None,
    ) -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "DELETE FROM photo_subjects WHERE photo_id = ? AND subject_id = ?",
                    (photo_id, subject_id),
                )
                conn.execute(
                    """
                    INSERT INTO photo_subjects (
                        photo_id, subject_id, bbox_ymin, bbox_xmin, bbox_ymax, bbox_xmax,
                        confidence, embedding_vector, crop_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        photo_id,
                        subject_id,
                        float(bbox[0]),
                        float(bbox[1]),
                        float(bbox[2]),
                        float(bbox[3]),
                        float(confidence),
                        json.dumps(embedding_vector),
                        crop_path,
                    ),
                )
                ps_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

                if crop_path:
                    conn.execute(
                        "UPDATE subjects SET avatar_path = COALESCE(avatar_path, ?) WHERE id = ?",
                        (crop_path, subject_id),
                    )

                subj_row = conn.execute(
                    "SELECT name, category, is_named FROM subjects WHERE id = ?", (subject_id,)
                ).fetchone()
                conn.commit()
            finally:
                conn.close()

        batch_tags = []
        if subj_row and subj_row["is_named"] and subj_row["name"]:
            batch_tags.append((subj_row["name"], "identity", confidence, "subject"))
        if subj_row and subj_row["category"]:
            cat_lower = subj_row["category"].lower()
            batch_tags.append((cat_lower, "category", confidence, "ai"))
            super_type = SUPER_TYPE_BY_CATEGORY.get(cat_lower, "Animal").lower()
            batch_tags.append((super_type, "category", confidence, "ai"))
        if batch_tags:
            self.add_photo_tags_batch(photo_id, batch_tags, sync_xmp=False)
        self._recompute_subject_centroid(subject_id)
        return ps_id

    def _recompute_subject_centroid(self, subject_id: int):
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT embedding_vector FROM photo_subjects WHERE subject_id = ?",
                    (subject_id,),
                ).fetchall()
                vectors = []
                for r in rows:
                    if r["embedding_vector"]:
                        try:
                            v = np.array(json.loads(r["embedding_vector"]), dtype=np.float32)
                            norm = np.linalg.norm(v)
                            if norm > 1e-6:
                                vectors.append(v / norm)
                        except Exception:
                            pass
                if vectors:
                    mean_vec = np.mean(vectors, axis=0)
                    norm = np.linalg.norm(mean_vec)
                    if norm > 1e-6:
                        mean_vec = mean_vec / norm
                    conn.execute(
                        "UPDATE subjects SET centroid_vector = ? WHERE id = ?",
                        (json.dumps(mean_vec.tolist()), subject_id),
                    )
                    conn.commit()
            finally:
                conn.close()

    def rename_subject(
        self, subject_id: int, new_name: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        clean_name = new_name.strip()
        if not clean_name:
            return None

        with self._lock:
            conn = self._get_conn()
            try:
                old_subj = conn.execute(
                    "SELECT * FROM subjects WHERE id = ?", (subject_id,)
                ).fetchone()
                if not old_subj:
                    return None

                existing = conn.execute(
                    "SELECT id FROM subjects WHERE LOWER(name) = LOWER(?) AND id != ?",
                    (clean_name, subject_id),
                ).fetchone()

                if existing:
                    target_id = existing["id"]
                    conn.close()
                    return self.merge_subjects(subject_id, target_id)

                old_name = old_subj["name"]
                cat = category.lower() if category else old_subj["category"]

                conn.execute(
                    """
                    UPDATE subjects
                    SET name = ?, display_name = ?, category = ?, is_named = 1
                    WHERE id = ?
                    """,
                    (clean_name, clean_name, cat, subject_id),
                )

                if old_name and old_name.lower() != clean_name.lower():
                    old_tag = conn.execute(
                        "SELECT id FROM tags WHERE LOWER(name) = LOWER(?) AND tag_type = 'identity'",
                        (old_name,),
                    ).fetchone()
                    if old_tag:
                        conn.execute(
                            """
                            DELETE FROM photo_tags
                            WHERE tag_id = ? AND photo_id IN (
                                SELECT photo_id FROM photo_subjects WHERE subject_id = ?
                            )
                            """,
                            (old_tag["id"], subject_id),
                        )

                photo_rows = conn.execute(
                    "SELECT photo_id, confidence FROM photo_subjects WHERE subject_id = ?",
                    (subject_id,),
                ).fetchall()
                conn.commit()
            finally:
                if conn:
                    conn.close()

        super_type = SUPER_TYPE_BY_CATEGORY.get(cat, "Animal").lower()
        for pr in photo_rows:
            self.add_photo_tag(
                pr["photo_id"],
                clean_name,
                tag_type="identity",
                confidence=pr["confidence"],
                source="subject",
            )
            self.add_photo_tag(
                pr["photo_id"],
                cat,
                tag_type="category",
                confidence=pr["confidence"],
                source="ai",
            )
            self.add_photo_tag(
                pr["photo_id"],
                super_type,
                tag_type="category",
                confidence=pr["confidence"],
                source="ai",
            )

        return self.get_subject_by_id(subject_id)

    def merge_subjects(self, source_id: int, target_id: int) -> Optional[Dict[str, Any]]:
        if source_id == target_id:
            return self.get_subject_by_id(target_id)

        with self._lock:
            conn = self._get_conn()
            try:
                source = conn.execute("SELECT * FROM subjects WHERE id = ?", (source_id,)).fetchone()
                target = conn.execute("SELECT * FROM subjects WHERE id = ?", (target_id,)).fetchone()
                if not source or not target:
                    return None

                source_links = conn.execute(
                    "SELECT * FROM photo_subjects WHERE subject_id = ?", (source_id,)
                ).fetchall()
                for link in source_links:
                    existing_on_photo = conn.execute(
                        "SELECT id FROM photo_subjects WHERE photo_id = ? AND subject_id = ?",
                        (link["photo_id"], target_id),
                    ).fetchone()
                    if existing_on_photo:
                        conn.execute("DELETE FROM photo_subjects WHERE id = ?", (link["id"],))
                    else:
                        conn.execute(
                            "UPDATE photo_subjects SET subject_id = ? WHERE id = ?",
                            (target_id, link["id"]),
                        )

                conn.execute("DELETE FROM subjects WHERE id = ?", (source_id,))
                conn.commit()
            finally:
                conn.close()

        self._recompute_subject_centroid(target_id)
        target_subj = self.get_subject_by_id(target_id)
        if target_subj and target_subj.get("name"):
            self.rename_subject(target_id, target_subj["name"], target_subj["category"])
        return self.get_subject_by_id(target_id)

    def reassign_photo_subject(
        self, photo_subject_id: int, new_name: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        clean_name = new_name.strip()
        if not clean_name:
            return None

        with self._lock:
            conn = self._get_conn()
            try:
                ps = conn.execute(
                    "SELECT * FROM photo_subjects WHERE id = ?", (photo_subject_id,)
                ).fetchone()
                if not ps:
                    return None

                old_subject_id = ps["subject_id"]
                photo_id = ps["photo_id"]
                old_subj = conn.execute(
                    "SELECT * FROM subjects WHERE id = ?", (old_subject_id,)
                ).fetchone()
                cat = (category or (old_subj["category"] if old_subj else "cat")).lower()

                target_subj = conn.execute(
                    "SELECT * FROM subjects WHERE LOWER(name) = LOWER(?)", (clean_name,)
                ).fetchone()

                emb_vec = json.loads(ps["embedding_vector"]) if ps["embedding_vector"] else []
            finally:
                conn.close()

        if target_subj:
            new_subject_id = target_subj["id"]
        else:
            new_subject_id = self.create_subject(
                category=cat,
                centroid_vector=emb_vec,
                avatar_path=ps["crop_path"],
                name=clean_name,
            )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "UPDATE photo_subjects SET subject_id = ? WHERE id = ?",
                    (new_subject_id, photo_subject_id),
                )
                if old_subj and old_subj["name"]:
                    old_tag = conn.execute(
                        "SELECT id FROM tags WHERE LOWER(name) = LOWER(?) AND tag_type = 'identity'",
                        (old_subj["name"],),
                    ).fetchone()
                    if old_tag:
                        conn.execute(
                            "DELETE FROM photo_tags WHERE photo_id = ? AND tag_id = ?",
                            (photo_id, old_tag["id"]),
                        )

                rem = conn.execute(
                    "SELECT COUNT(*) as c FROM photo_subjects WHERE subject_id = ?",
                    (old_subject_id,),
                ).fetchone()
                if rem and rem["c"] == 0:
                    conn.execute("DELETE FROM subjects WHERE id = ?", (old_subject_id,))
                conn.commit()
            finally:
                conn.close()

        self.add_photo_tag(
            photo_id, clean_name, tag_type="identity", confidence=1.0, source="user"
        )
        self.add_photo_tag(
            photo_id, cat, tag_type="category", confidence=1.0, source="user"
        )
        self._recompute_subject_centroid(old_subject_id)
        self._recompute_subject_centroid(new_subject_id)
        return self.get_subject_by_id(new_subject_id)

    def get_subject_by_id(self, subject_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                r = conn.execute(
                    """
                    SELECT s.*, COUNT(DISTINCT ps.photo_id) as photo_count
                    FROM subjects s
                    LEFT JOIN photo_subjects ps ON ps.subject_id = s.id
                    WHERE s.id = ?
                    GROUP BY s.id
                    """,
                    (subject_id,),
                ).fetchone()
                if not r:
                    return None
                sample_rows = conn.execute(
                    """
                    SELECT p.id FROM photos p
                    JOIN photo_subjects ps ON ps.photo_id = p.id
                    WHERE ps.subject_id = ?
                    LIMIT 4
                    """,
                    (subject_id,),
                ).fetchall()
                cat_lower = r["category"].lower()
                super_type = SUPER_TYPE_BY_CATEGORY.get(cat_lower, "Animal")
                return {
                    "id": r["id"],
                    "name": r["name"],
                    "display_name": r["display_name"],
                    "category": r["category"],
                    "super_type": super_type,
                    "type_chain": [r["display_name"], r["category"].capitalize(), super_type],
                    "avatar_url": f"/api/subjects/{r['id']}/avatar" if r["avatar_path"] else None,
                    "photo_count": r["photo_count"],
                    "is_named": bool(r["is_named"]),
                    "is_favorite": bool(r["is_favorite"]),
                    "sample_photos": [f"/api/photos/{sr['id']}/thumbnail" for sr in sample_rows],
                    "created_at": r["created_at"],
                }
            finally:
                conn.close()

    def get_subjects(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    """
                    SELECT s.*, COUNT(DISTINCT ps.photo_id) as photo_count
                    FROM subjects s
                    JOIN photo_subjects ps ON ps.subject_id = s.id
                    GROUP BY s.id
                    HAVING photo_count > 0
                    ORDER BY s.is_named DESC, photo_count DESC, s.id ASC
                    """
                ).fetchall()
                result = []
                for r in rows:
                    sample_rows = conn.execute(
                        """
                        SELECT p.id FROM photos p
                        JOIN photo_subjects ps ON ps.photo_id = p.id
                        WHERE ps.subject_id = ?
                        ORDER BY ps.confidence DESC
                        LIMIT 4
                        """,
                        (r["id"],),
                    ).fetchall()
                    cat_lower = r["category"].lower()
                    super_type = SUPER_TYPE_BY_CATEGORY.get(cat_lower, "Animal")
                    result.append(
                        {
                            "id": r["id"],
                            "name": r["name"],
                            "display_name": r["display_name"],
                            "category": r["category"],
                            "super_type": super_type,
                            "type_chain": [r["display_name"], r["category"].capitalize(), super_type],
                            "avatar_url": f"/api/subjects/{r['id']}/avatar" if r["avatar_path"] else (
                                f"/api/photos/{sample_rows[0]['id']}/thumbnail" if sample_rows else None
                            ),
                            "photo_count": r["photo_count"],
                            "is_named": bool(r["is_named"]),
                            "is_favorite": bool(r["is_favorite"]),
                            "sample_photos": [f"/api/photos/{sr['id']}/thumbnail" for sr in sample_rows],
                            "created_at": r["created_at"],
                        }
                    )
                return result
            finally:
                conn.close()

    @staticmethod
    def _build_photo_root_systems(
        photo_row: Dict[str, Any],
        subjects: List[Dict[str, Any]],
        tags: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Builds the 3 Root System hierarchies for a photo:
          1. Type:   Specific (e.g. Blu) -> Category (e.g. Cat) -> SuperType (e.g. Animal)
          2. Drive:  Subfolder -> Folder -> Drive
          3. Device: EXIF Device -> EXIF Time -> Image Type
        """
        # 1. Type Root Hierarchy
        if subjects:
            primary_subj = subjects[0]
            specific_label = primary_subj["display_name"]
            cat_label = primary_subj["category"].capitalize()
            super_label = SUPER_TYPE_BY_CATEGORY.get(primary_subj["category"].lower(), "Animal")
            type_chain = [specific_label, cat_label, super_label]
        else:
            cat_tags = [
                t["name"].lower()
                for t in tags
                if t["tag_type"] == "category" and t["name"].lower() != "object"
            ]
            generic_scene_words = {
                "nature",
                "landscape",
                "outdoor",
                "indoor",
                "low light",
                "bright lighting",
                "high contrast",
                "warm lighting",
                "golden hour",
                "sunset",
                "medieval",
                "rural life",
                "maritime",
                "urban",
                "illustration",
                "character portrait",
                "artwork",
                "structure",
                "technology",
                "transport",
                "animal",
                "pet",
                "feline",
                "canine",
                "people",
                "object",
            }
            if "nature" in cat_tags or "landscape" in cat_tags or "mountain" in cat_tags or "beach" in cat_tags:
                super_label = "Nature"
                if "mountain" in cat_tags:
                    cat_label = "Mountain"
                elif "beach" in cat_tags:
                    cat_label = "Beach"
                elif "botanical" in cat_tags:
                    cat_label = "Botanical"
                else:
                    cat_label = "Landscape"
                specific_tags = [
                    t["name"].title()
                    for t in tags
                    if t["name"].lower() not in generic_scene_words
                    and t["name"].lower() != cat_label.lower()
                ]
                specific_label = specific_tags[0] if specific_tags else "Natural Scenery"
            elif cat_tags:
                # Prefer specific sub-category over broad parent category
                preferred_cats = [
                    c for c in cat_tags if c not in ("artwork", "structure", "technology", "transport", "animal", "people")
                ]
                chosen_cat = preferred_cats[0] if preferred_cats else cat_tags[0]
                cat_label = chosen_cat.title()
                super_label = SUPER_TYPE_BY_CATEGORY.get(chosen_cat, "Art & Media")
                specific_tags = [
                    t["name"].title()
                    for t in tags
                    if t["name"].lower() not in generic_scene_words
                    and t["name"].lower() != chosen_cat
                    and t["name"].lower() != super_label.lower()
                ]
                specific_label = specific_tags[0] if specific_tags else f"{cat_label} Scene"
            else:
                super_label = "Art & Media"
                cat_label = "Photography"
                specific_tags = [
                    t["name"].title()
                    for t in tags
                    if t["name"].lower() not in generic_scene_words
                ]
                specific_label = specific_tags[0] if specific_tags else "Captured Image"
            type_chain = [specific_label, cat_label, super_label]

        # 2. Drive Root Hierarchy (Subfolder -> Folder -> Drive)
        drive_name = photo_row.get("drive_root") or "C:"
        folder_name = photo_row.get("folder_name") or "Root"
        subfolder_name = photo_row.get("subfolder_name") or "Root"
        drive_chain = [subfolder_name, folder_name, drive_name]

        # 3. Device Root Hierarchy (EXIF Device + Capture Time -> Image Type)
        device_name = photo_row.get("device_name") or "Unknown Device"
        date_taken = photo_row.get("date_taken") or "Unknown Time"
        capture_date = date_taken[:10] if len(date_taken) >= 10 else date_taken
        capture_time_short = date_taken[:16] if len(date_taken) >= 16 else date_taken
        image_type = (photo_row.get("image_type") or "JPEG").upper()
        device_chain = [device_name, capture_time_short, image_type]

        return {
            "type_root": {
                "specific": specific_label,
                "category": cat_label,
                "super_type": super_label,
                "chain": type_chain,
            },
            "drive_root": {
                "subfolder": subfolder_name,
                "folder": folder_name,
                "drive": drive_name,
                "chain": drive_chain,
            },
            "device_root": {
                "device": device_name,
                "date_taken": date_taken,
                "capture_date": capture_date,
                "image_type": image_type,
                "chain": device_chain,
            },
        }

    # --- Querying Photos ---
    def query_photos(
        self,
        search: Optional[str] = None,
        subject_id: Optional[int] = None,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        super_type: Optional[str] = None,
        folder_id: Optional[int] = None,
        drive_root: Optional[str] = None,
        folder_name: Optional[str] = None,
        subfolder_name: Optional[str] = None,
        device_name: Optional[str] = None,
        capture_date: Optional[str] = None,
        image_type: Optional[str] = None,
        favorites_only: bool = False,
        exclude_games: Optional[bool] = None,
        min_rating: Optional[int] = None,
        orientation: Optional[str] = None,
        duplicates_only: bool = False,
        sort_by: str = "date_desc",
        limit: int = 500,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                where_clauses = ["1=1"]
                params: List[Any] = []

                if favorites_only:
                    where_clauses.append("p.is_favorite = 1")

                if min_rating is not None and int(min_rating) > 0:
                    where_clauses.append("COALESCE(p.rating, 0) >= ?")
                    params.append(int(min_rating))

                if exclude_games is True:
                    where_clauses.append("COALESCE(p.is_game_asset, 0) = 0")
                elif exclude_games is None:
                    g_row = conn.execute("SELECT value FROM settings WHERE key = 'game_detection'").fetchone()
                    if g_row and str(g_row["value"]).lower() in ("1", "true"):
                        where_clauses.append("COALESCE(p.is_game_asset, 0) = 0")

                if folder_id is not None:
                    where_clauses.append("p.folder_id = ?")
                    params.append(folder_id)

                if drive_root:
                    where_clauses.append("LOWER(p.drive_root) = LOWER(?)")
                    params.append(drive_root.strip())

                if folder_name:
                    where_clauses.append("LOWER(p.folder_name) = LOWER(?)")
                    params.append(folder_name.strip())

                if subfolder_name:
                    where_clauses.append("LOWER(p.subfolder_name) = LOWER(?)")
                    params.append(subfolder_name.strip())

                if device_name:
                    where_clauses.append("LOWER(p.device_name) = LOWER(?)")
                    params.append(device_name.strip())

                if capture_date:
                    where_clauses.append("p.date_taken LIKE ?")
                    params.append(f"{capture_date.strip()}%")

                if image_type:
                    where_clauses.append("UPPER(p.image_type) = UPPER(?)")
                    params.append(image_type.strip())

                if orientation:
                    ori = orientation.lower().strip()
                    if ori == "landscape":
                        where_clauses.append("COALESCE(p.width, 0) > COALESCE(p.height, 0)")
                    elif ori == "portrait":
                        where_clauses.append("COALESCE(p.height, 0) > COALESCE(p.width, 0)")
                    elif ori == "square":
                        where_clauses.append("COALESCE(p.width, 0) = COALESCE(p.height, 0) AND COALESCE(p.width, 0) > 0")

                if duplicates_only:
                    where_clauses.append("""(
                        p.file_hash IN (SELECT file_hash FROM photos WHERE file_hash IS NOT NULL AND file_hash != '' GROUP BY file_hash HAVING COUNT(*) > 1)
                        OR EXISTS (
                            SELECT 1 FROM photos p2 
                            WHERE p2.id != p.id 
                              AND p2.folder_id = p.folder_id 
                              AND p2.date_taken IS NOT NULL 
                              AND p.date_taken IS NOT NULL 
                              AND SUBSTR(p2.date_taken, 1, 16) = SUBSTR(p.date_taken, 1, 16)
                        )
                    )""")

                if subject_id is not None:
                    where_clauses.append(
                        "p.id IN (SELECT photo_id FROM photo_subjects WHERE subject_id = ?)"
                    )
                    params.append(subject_id)

                if tag:
                    where_clauses.append(
                        """
                        p.id IN (
                            SELECT pt.photo_id FROM photo_tags pt
                            JOIN tags t ON t.id = pt.tag_id
                            WHERE LOWER(t.name) = LOWER(?)
                        )
                        """
                    )
                    params.append(tag.strip())

                if category:
                    where_clauses.append(
                        """
                        (
                            p.id IN (
                                SELECT pt.photo_id FROM photo_tags pt
                                JOIN tags t ON t.id = pt.tag_id
                                WHERE LOWER(t.name) = LOWER(?)
                            )
                            OR p.id IN (
                                SELECT ps.photo_id FROM photo_subjects ps
                                JOIN subjects s ON s.id = ps.subject_id
                                WHERE LOWER(s.category) = LOWER(?)
                            )
                        )
                        """
                    )
                    params.extend([category.strip(), category.strip()])

                if super_type:
                    st_lower = super_type.strip().lower()
                    matching_cats = [
                        k for k, v in SUPER_TYPE_BY_CATEGORY.items() if v.lower() == st_lower
                    ]
                    matching_cats.append(st_lower)
                    cat_ph = ",".join(["?"] * len(matching_cats))
                    where_clauses.append(
                        f"""
                        (
                            p.id IN (
                                SELECT pt.photo_id FROM photo_tags pt
                                JOIN tags t ON t.id = pt.tag_id
                                WHERE LOWER(t.name) IN ({cat_ph})
                            )
                            OR p.id IN (
                                SELECT ps.photo_id FROM photo_subjects ps
                                JOIN subjects s ON s.id = ps.subject_id
                                WHERE LOWER(s.category) IN ({cat_ph})
                            )
                        )
                        """
                    )
                    params.extend(matching_cats + matching_cats)

                if search and search.strip():
                    raw_search = search.strip()
                    tokens = [tok.strip().lower() for tok in raw_search.split() if tok.strip()]
                    semantic_clause = ""
                    # Natural language semantic search with CLIP for multi-word queries (e.g. "cat on sofa", "sunset beach")
                    # Single tokens (e.g. "Blu") remain strict exact-entity searches so names are never polluted by color words
                    if len(tokens) > 1:
                        try:
                            from backend.ai.clip_engine import clip_engine
                            if clip_engine.is_ready:
                                q_embed = clip_engine.embed_text([raw_search])
                                if q_embed is not None and len(q_embed) > 0:
                                    q_vec = q_embed[0]
                                    emb_rows = conn.execute(
                                        "SELECT id, scene_embedding FROM photos WHERE scene_embedding IS NOT NULL"
                                    ).fetchall()
                                    sem_matched = []
                                    for er in emb_rows:
                                        try:
                                            s_raw = json.loads(er["scene_embedding"])
                                            if len(s_raw) == 512:
                                                sim = float(np.dot(np.array(s_raw, dtype=np.float32), q_vec))
                                                if sim >= 0.25:
                                                    sem_matched.append((er["id"], sim))
                                        except Exception:
                                            pass
                                    if sem_matched:
                                        sem_matched.sort(key=lambda x: x[1], reverse=True)
                                        top_ids_str = ",".join(str(x[0]) for x in sem_matched[:80])
                                        semantic_clause = f"OR p.id IN ({top_ids_str})"
                        except Exception:
                            pass

                    for tok in tokens:
                        clean_tok = tok.lstrip("#")
                        like_pat = f"%{clean_tok}%"
                        where_clauses.append(
                            f"""
                            (
                                LOWER(p.filename) LIKE ?
                                OR LOWER(COALESCE(p.ai_description, '')) LIKE ?
                                OR LOWER(COALESCE(p.ocr_text, '')) LIKE ?
                                OR LOWER(COALESCE(p.device_name, '')) LIKE ?
                                OR LOWER(COALESCE(p.image_type, '')) LIKE ?
                                OR LOWER(COALESCE(p.subfolder_name, '')) LIKE ?
                                OR LOWER(COALESCE(p.folder_name, '')) LIKE ?
                                OR p.id IN (
                                    SELECT pt.photo_id FROM photo_tags pt
                                    JOIN tags t ON t.id = pt.tag_id
                                    WHERE LOWER(t.name) = ?
                                       OR LOWER(t.name) LIKE ?
                                       OR LOWER(t.name) LIKE ?
                                       OR LOWER(t.name) LIKE ?
                                )
                                OR p.id IN (
                                    SELECT ps.photo_id FROM photo_subjects ps
                                    JOIN subjects s ON s.id = ps.subject_id
                                    WHERE LOWER(COALESCE(s.name, '')) = ?
                                       OR LOWER(s.display_name) = ?
                                       OR LOWER(s.category) = ?
                                       OR LOWER(s.display_name) LIKE ?
                                )
                                {semantic_clause}
                            )
                            """
                        )
                        params.extend([
                            like_pat,
                            like_pat,
                            like_pat,
                            like_pat,
                            like_pat,
                            like_pat,
                            like_pat,
                            clean_tok,
                            f"{clean_tok} %",
                            f"% {clean_tok}",
                            f"% {clean_tok} %",
                            clean_tok,
                            clean_tok,
                            clean_tok,
                            like_pat,
                        ])

                sort_map = {
                    "date_desc": "COALESCE(p.date_taken, p.created_at) DESC, p.id DESC",
                    "date_asc": "COALESCE(p.date_taken, p.created_at) ASC, p.id ASC",
                    "name_asc": "p.filename COLLATE NOCASE ASC, p.id ASC",
                    "name_desc": "p.filename COLLATE NOCASE DESC, p.id DESC",
                    "size_desc": "p.file_size DESC, p.id DESC",
                    "size_asc": "p.file_size ASC, p.id ASC",
                    "rating_desc": "COALESCE(p.rating, 0) DESC, COALESCE(p.date_taken, p.created_at) DESC",
                }
                order_clause = sort_map.get(sort_by, sort_map["date_desc"])

                where_sql = " AND ".join(where_clauses)
                sql = f"""
                    SELECT p.*
                    FROM photos p
                    WHERE {where_sql}
                    ORDER BY {order_clause}
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                photo_rows = conn.execute(sql, params).fetchall()

                if not photo_rows:
                    return []

                photo_ids = [r["id"] for r in photo_rows]
                placeholders = ",".join(["?"] * len(photo_ids))

                tag_rows = conn.execute(
                    f"""
                    SELECT pt.photo_id, t.id, t.name, t.tag_type, pt.confidence, pt.source
                    FROM photo_tags pt
                    JOIN tags t ON t.id = pt.tag_id
                    WHERE pt.photo_id IN ({placeholders})
                    ORDER BY
                        CASE t.tag_type
                            WHEN 'identity' THEN 1
                            WHEN 'category' THEN 2
                            WHEN 'scene' THEN 3
                            ELSE 4
                        END,
                        pt.confidence DESC
                    """,
                    photo_ids,
                ).fetchall()

                tags_by_photo: Dict[int, List[Dict[str, Any]]] = {pid: [] for pid in photo_ids}
                for tr in tag_rows:
                    tags_by_photo[tr["photo_id"]].append(
                        {
                            "id": tr["id"],
                            "name": tr["name"],
                            "tag_type": tr["tag_type"],
                            "confidence": round(float(tr["confidence"]), 3),
                            "source": tr["source"],
                        }
                    )

                subj_rows = conn.execute(
                    f"""
                    SELECT ps.id as ps_id, ps.photo_id, ps.subject_id,
                           ps.bbox_ymin, ps.bbox_xmin, ps.bbox_ymax, ps.bbox_xmax,
                           ps.confidence, ps.crop_path,
                           s.name as subject_name, s.display_name, s.category, s.is_named
                    FROM photo_subjects ps
                    JOIN subjects s ON s.id = ps.subject_id
                    WHERE ps.photo_id IN ({placeholders})
                    ORDER BY ps.confidence DESC
                    """,
                    photo_ids,
                ).fetchall()

                subjects_by_photo: Dict[int, List[Dict[str, Any]]] = {pid: [] for pid in photo_ids}
                for sr in subj_rows:
                    subjects_by_photo[sr["photo_id"]].append(
                        {
                            "id": sr["ps_id"],
                            "subject_id": sr["subject_id"],
                            "subject_name": sr["subject_name"],
                            "display_name": sr["display_name"],
                            "category": sr["category"],
                            "bbox": [
                                sr["bbox_ymin"],
                                sr["bbox_xmin"],
                                sr["bbox_ymax"],
                                sr["bbox_xmax"],
                            ],
                            "confidence": round(float(sr["confidence"]), 3),
                            "crop_url": f"/api/photo-subjects/{sr['ps_id']}/crop" if sr["crop_path"] else None,
                            "is_named": bool(sr["is_named"]),
                        }
                    )

                items = []
                for r in photo_rows:
                    pid = r["id"]
                    r_dict = dict(r)
                    p_tags = tags_by_photo.get(pid, [])
                    p_subjs = subjects_by_photo.get(pid, [])
                    root_systems = self._build_photo_root_systems(r_dict, p_subjs, p_tags)

                    items.append(
                        {
                            "id": pid,
                            "path": r["path"],
                            "filename": r["filename"],
                            "folder_id": r["folder_id"],
                            "width": r["width"],
                            "height": r["height"],
                            "file_size": r["file_size"],
                            "image_type": r_dict.get("image_type") or "JPEG",
                            "drive_root": r_dict.get("drive_root") or "C:",
                            "folder_name": r_dict.get("folder_name") or "Root",
                            "subfolder_name": r_dict.get("subfolder_name") or "Root",
                            "date_taken": r["date_taken"],
                            "camera_make": r["camera_make"],
                            "camera_model": r["camera_model"],
                            "device_name": r_dict.get("device_name") or "Unknown Device",
                            "iso": r["iso"],
                            "focal_length": r["focal_length"],
                            "aperture": r["aperture"],
                            "shutter_speed": r["shutter_speed"],
                            "dominant_color": r["dominant_color"] or "#E5E5EA",
                            "is_favorite": bool(r["is_favorite"]),
                            "is_game_asset": bool(r_dict.get("is_game_asset") or 0),
                            "rating": int(r_dict.get("rating") or 0),
                            "rotation": int(r_dict.get("rotation") or 0),
                            "ai_processed": bool(r["ai_processed"]),
                            "ai_description": r["ai_description"],
                            "ai_engine_used": r["ai_engine_used"] or "local",
                            "face_count": int(r_dict.get("face_count") or 0),
                            "face_boxes": json.loads(r_dict.get("face_boxes") or "[]") if r_dict.get("face_boxes") else [],
                            "ocr_text": r_dict.get("ocr_text") or None,
                            "thumbnail_url": f"/api/photos/{pid}/thumbnail",
                            "preview_url": f"/api/photos/{pid}/preview",
                            "original_url": f"/api/photos/{pid}/original",
                            "tags": p_tags,
                            "subjects": p_subjs,
                            "root_systems": root_systems,
                            "created_at": r["created_at"],
                        }
                    )
                return items
            finally:
                conn.close()

    def get_three_root_trees(self, exclude_games: Optional[bool] = None) -> Dict[str, Any]:
        """
        Aggregates the entire photo library into the 3 Root Systems:
          1. type_tree:   SuperType (e.g. Animal) -> Category (e.g. Cat) -> Identity (e.g. Blu)
          2. drive_tree:  Drive (e.g. C:) -> Folder -> Subfolder
          3. device_tree: Device (EXIF Make/Model) -> Capture Date/Time -> Image Type (JPEG, PNG, WEBP)
        """
        all_photos = self.query_photos(limit=5000, exclude_games=exclude_games)

        type_map: Dict[str, Dict[str, Any]] = {}
        drive_map: Dict[str, Dict[str, Any]] = {}
        device_map: Dict[str, Dict[str, Any]] = {}

        for p in all_photos:
            rs = p["root_systems"]

            # 1. Type Root
            tr = rs["type_root"]
            st = tr["super_type"]
            cat = tr["category"]
            spec = tr["specific"]
            subj_id = p["subjects"][0]["subject_id"] if p["subjects"] else None

            if st not in type_map:
                type_map[st] = {"name": st, "count": 0, "categories": {}}
            type_map[st]["count"] += 1

            if cat not in type_map[st]["categories"]:
                type_map[st]["categories"][cat] = {"name": cat, "count": 0, "individuals": {}}
            type_map[st]["categories"][cat]["count"] += 1

            if spec not in type_map[st]["categories"][cat]["individuals"]:
                type_map[st]["categories"][cat]["individuals"][spec] = {
                    "name": spec,
                    "subject_id": subj_id,
                    "count": 0,
                }
            type_map[st]["categories"][cat]["individuals"][spec]["count"] += 1

            # 2. Drive Root (Drive -> Folder -> Subfolder)
            dr = rs["drive_root"]
            drv = dr["drive"]
            fld = dr["folder"]
            sub = dr["subfolder"]

            if drv not in drive_map:
                drive_map[drv] = {"name": drv, "count": 0, "folders": {}}
            drive_map[drv]["count"] += 1

            if fld not in drive_map[drv]["folders"]:
                drive_map[drv]["folders"][fld] = {"name": fld, "count": 0, "subfolders": {}}
            drive_map[drv]["folders"][fld]["count"] += 1

            if sub not in drive_map[drv]["folders"][fld]["subfolders"]:
                drive_map[drv]["folders"][fld]["subfolders"][sub] = {"name": sub, "count": 0}
            drive_map[drv]["folders"][fld]["subfolders"][sub]["count"] += 1

            # 3. Device Root (Device -> Capture Date/Time -> Image Type)
            dev_r = rs["device_root"]
            dev = dev_r["device"]
            c_date = dev_r["capture_date"]
            i_type = dev_r["image_type"]

            if dev not in device_map:
                device_map[dev] = {"name": dev, "count": 0, "dates": {}, "image_types": {}}
            device_map[dev]["count"] += 1
            device_map[dev]["image_types"][i_type] = (
                device_map[dev]["image_types"].get(i_type, 0) + 1
            )

            if c_date not in device_map[dev]["dates"]:
                device_map[dev]["dates"][c_date] = {"date": c_date, "count": 0, "types": {}}
            device_map[dev]["dates"][c_date]["count"] += 1
            device_map[dev]["dates"][c_date]["types"][i_type] = (
                device_map[dev]["dates"][c_date]["types"].get(i_type, 0) + 1
            )

        # Convert nested dicts to sorted lists for clean UI rendering
        type_tree = []
        for st_name, st_data in sorted(type_map.items(), key=lambda x: -x[1]["count"]):
            cats = []
            for c_name, c_data in sorted(st_data["categories"].items(), key=lambda x: -x[1]["count"]):
                indivs = sorted(c_data["individuals"].values(), key=lambda x: -x["count"])
                cats.append({"name": c_name, "count": c_data["count"], "individuals": indivs})
            type_tree.append({"name": st_name, "count": st_data["count"], "categories": cats})

        drive_tree = []
        for d_name, d_data in sorted(drive_map.items()):
            flds = []
            for f_name, f_data in sorted(d_data["folders"].items(), key=lambda x: -x[1]["count"]):
                subs = sorted(f_data["subfolders"].values(), key=lambda x: -x["count"])
                flds.append({"name": f_name, "count": f_data["count"], "subfolders": subs})
            drive_tree.append({"name": d_name, "count": d_data["count"], "folders": flds})

        device_tree = []
        for dev_name, dev_data in sorted(device_map.items(), key=lambda x: -x[1]["count"]):
            dates = []
            for dt_name, dt_data in sorted(dev_data["dates"].items(), key=lambda x: x[0], reverse=True):
                types_list = [
                    {"image_type": k, "count": v}
                    for k, v in sorted(dt_data["types"].items(), key=lambda x: -x[1])
                ]
                dates.append({"date": dt_name, "count": dt_data["count"], "types": types_list})
            dev_types = [
                {"image_type": k, "count": v}
                for k, v in sorted(dev_data["image_types"].items(), key=lambda x: -x[1])
            ]
            device_tree.append(
                {
                    "name": dev_name,
                    "count": dev_data["count"],
                    "dates": dates,
                    "image_types": dev_types,
                }
            )

        return {
            "type_tree": type_tree,
            "drive_tree": drive_tree,
            "device_tree": device_tree,
        }

    def get_library_stats(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            try:
                total_photos = conn.execute("SELECT COUNT(*) as c FROM photos").fetchone()["c"]
                analyzed_photos = conn.execute(
                    "SELECT COUNT(*) as c FROM photos WHERE ai_processed = 1"
                ).fetchone()["c"]
                favorites = conn.execute(
                    "SELECT COUNT(*) as c FROM photos WHERE is_favorite = 1"
                ).fetchone()["c"]
                total_subjects = conn.execute(
                    "SELECT COUNT(DISTINCT subject_id) as c FROM photo_subjects"
                ).fetchone()["c"]
                named_subjects = conn.execute(
                    """
                    SELECT COUNT(DISTINCT s.id) as c
                    FROM subjects s
                    JOIN photo_subjects ps ON ps.subject_id = s.id
                    WHERE s.is_named = 1
                    """
                ).fetchone()["c"]
                total_tags = conn.execute(
                    "SELECT COUNT(DISTINCT tag_id) as c FROM photo_tags"
                ).fetchone()["c"]
                return {
                    "total_photos": total_photos,
                    "analyzed_photos": analyzed_photos,
                    "favorites": favorites,
                    "total_subjects": total_subjects,
                    "named_subjects": named_subjects,
                    "total_tags": total_tags,
                }
            finally:
                conn.close()
