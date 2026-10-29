import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.db.database import Database
from backend.scanner.metadata import extract_image_metadata
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.xmp_sidecar import read_xmp_sidecar, write_xmp_sidecar
from backend.ai.engine import AIEngine


SUPPORTED_EXTENSIONS: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}


class PhotoWatchHandler(FileSystemEventHandler):
    def __init__(self, scanner: "DriveScanner", folder_id: int):
        super().__init__()
        self.scanner = scanner
        self.folder_id = folder_id

    def on_created(self, event):
        if event.is_directory:
            return
        ext = Path(event.src_path).suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            # Slight delay to allow file write to finish
            threading.Timer(
                0.8,
                self.scanner.index_and_analyze_single_file,
                args=(event.src_path, self.folder_id),
            ).start()


class DriveScanner:
    """
    Scans folders and drives for images, extracts metadata & WebP thumbnails,
    runs the AI neural network pipeline, and watches folders for new photos.
    """

    def __init__(self, db: Database, thumbnailer: Thumbnailer, ai_engine: AIEngine):
        self.db = db
        self.thumbnailer = thumbnailer
        self.ai_engine = ai_engine
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._scan_thread: Optional[threading.Thread] = None
        self._observer: Optional[Observer] = None
        self._watched_paths: Set[str] = set()

        self.status: Dict[str, Any] = {
            "status": "idle",
            "current_folder": None,
            "current_file": None,
            "total_files": 0,
            "indexed_files": 0,
            "analyzed_files": 0,
            "progress_percent": 0.0,
            "speed_fps": 0.0,
            "error_message": None,
            "ai_mode": "local",
        }

    def get_status(self) -> Dict[str, Any]:
        settings = self.db.get_settings()
        with self._lock:
            s = dict(self.status)
            s["ai_mode"] = settings.get("ai_mode", "local")
            return s

    def cancel_scan(self):
        with self._lock:
            self._cancel_requested = True

    def discover_images(self, root_path: str, recursive: bool = True) -> List[Path]:
        root = Path(root_path).resolve()
        if not root.exists():
            return []

        found: List[Path] = []
        skip_dirs = {
            ".targon_cache",
            "node_modules",
            ".git",
            "__pycache__",
            "$RECYCLE.BIN",
            "System Volume Information",
            "AppData",
            "Windows",
        }

        if not recursive:
            for item in root.iterdir():
                if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                    found.append(item)
            return sorted(found)

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune system/cache directories in-place
            dirnames[:] = [
                d for d in dirnames if d not in skip_dirs and not d.startswith(".")
            ]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    found.append(Path(dirpath) / fn)

        return sorted(found)

    def index_and_analyze_single_file(
        self,
        file_path: str,
        folder_id: Optional[int] = None,
        force_reanalyze: bool = False,
        scanned_root: Optional[str] = None,
    ) -> Optional[int]:
        try:
            norm_path = str(Path(file_path).resolve())
            settings = self.db.get_settings()
            existing = self.db.get_photo_by_path(norm_path)

            meta, pil_img = extract_image_metadata(
                norm_path, scanned_root=scanned_root, return_image=True
            )
            if (
                settings.get("skip_small_images", True)
                and 0 < meta.get("width", 0) < 48
                and 0 < meta.get("height", 0) < 48
            ):
                return None

            meta["folder_id"] = folder_id
            quality_mode = (
                "fast"
                if settings.get("low_spec_mode", False)
                else settings.get("thumbnail_quality", "balanced")
            )

            thumb_path, preview_path = self.thumbnailer.generate_thumbnails(
                norm_path,
                meta["file_hash"],
                pil_img=pil_img,
                quality_mode=quality_mode,
            )
            meta["thumbnail_path"] = thumb_path
            meta["preview_path"] = preview_path

            photo_id = self.db.upsert_photo(meta)

            # Check if an existing .xmp sidecar is present on disk (only when not forcing fresh AI reanalysis)
            if not force_reanalyze:
                existing_xmp = read_xmp_sidecar(norm_path)
                if existing_xmp and existing_xmp.get("tags"):
                    xmp_batch = [
                        (xt, "user", 1.0, "xmp")
                        for xt in existing_xmp["tags"]
                        if xt.lower() != "object"
                    ]
                    if xmp_batch:
                        self.db.add_photo_tags_batch(photo_id, xmp_batch, sync_xmp=False)

            # Run AI neural network pipeline if not yet processed or if hash changed or forced
            needs_ai = (
                force_reanalyze
                or not existing
                or not existing.get("ai_processed")
                or existing.get("file_hash") != meta["file_hash"]
            )
            if needs_ai:
                if force_reanalyze:
                    conn = self.db._get_conn()
                    try:
                        conn.execute(
                            "DELETE FROM photo_tags WHERE photo_id = ? AND source IN ('ai', 'xmp')",
                            (photo_id,),
                        )
                        conn.execute("DELETE FROM photo_subjects WHERE photo_id = ?", (photo_id,))
                        conn.commit()
                    finally:
                        conn.close()
                self.ai_engine.process_photo(
                    photo_id,
                    norm_path,
                    meta["file_hash"],
                    pil_img=pil_img,
                    sync_xmp=False,
                )

            # Ensure XMP sidecar is synced once at the end if in 'sidecar' or 'both' mode
            self.db.sync_photo_xmp_sidecar(photo_id)

            return photo_id
        except Exception:
            return None

    def scan_folder_sync(
        self, folder_path: str, recursive: bool = True, force_reanalyze: bool = False
    ) -> Dict[str, Any]:
        """Synchronous scan method (used directly in tests or called by background worker)."""
        root = Path(folder_path).resolve()
        if not root.exists() or not root.is_dir():
            with self._lock:
                self.status.update(
                    {
                        "status": "error",
                        "error_message": f"Directory not found: {folder_path}",
                    }
                )
            return self.get_status()

        with self._lock:
            self._cancel_requested = False
            self.status.update(
                {
                    "status": "indexing",
                    "current_folder": str(root),
                    "current_file": "discovering images...",
                    "total_files": 0,
                    "indexed_files": 0,
                    "analyzed_files": 0,
                    "progress_percent": 0.0,
                    "speed_fps": 0.0,
                    "error_message": None,
                }
            )

        folder_id = self.db.upsert_folder(str(root), watch_enabled=True)
        image_files = self.discover_images(str(root), recursive=recursive)
        total = len(image_files)

        with self._lock:
            self.status["total_files"] = total
            if total == 0:
                self.status.update(
                    {
                        "status": "completed",
                        "current_file": None,
                        "progress_percent": 100.0,
                    }
                )
                return self.get_status()
            self.status["status"] = "analyzing"

        settings = self.db.get_settings()
        workers = int(settings.get("scan_threads", 4))
        if settings.get("low_spec_mode", False):
            workers = min(workers, 2)
        workers = max(1, min(8, workers))

        start_time = time.time()

        # Use multi-threaded worker pool for larger batches to maximize img/sec throughput
        if workers > 1 and total > 8:
            done_count = 0

            def _worker(img_p: Path):
                with self._lock:
                    if self._cancel_requested:
                        return None
                    self.status["current_file"] = img_p.name
                return self.index_and_analyze_single_file(
                    str(img_p),
                    folder_id=folder_id,
                    force_reanalyze=force_reanalyze,
                    scanned_root=str(root),
                )

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_worker, p) for p in image_files]
                for fut in as_completed(futures):
                    with self._lock:
                        if self._cancel_requested:
                            self.status["status"] = "idle"
                            self.status["current_file"] = None
                            break
                        done_count += 1
                        elapsed = max(0.01, time.time() - start_time)
                        self.status["indexed_files"] = done_count
                        self.status["analyzed_files"] = done_count
                        self.status["progress_percent"] = round((done_count / total) * 100.0, 1)
                        self.status["speed_fps"] = round(done_count / elapsed, 2)
        else:
            for idx, img_path in enumerate(image_files):
                with self._lock:
                    if self._cancel_requested:
                        self.status["status"] = "idle"
                        self.status["current_file"] = None
                        break
                    self.status["current_file"] = img_path.name

                self.index_and_analyze_single_file(
                    str(img_path),
                    folder_id=folder_id,
                    force_reanalyze=force_reanalyze,
                    scanned_root=str(root),
                )

                elapsed = max(0.01, time.time() - start_time)
                done = idx + 1
                with self._lock:
                    self.status["indexed_files"] = done
                    self.status["analyzed_files"] = done
                    self.status["progress_percent"] = round((done / total) * 100.0, 1)
                    self.status["speed_fps"] = round(done / elapsed, 2)

        with self._lock:
            if not self._cancel_requested:
                self.status["status"] = "completed"
                self.status["current_file"] = None
                self.status["progress_percent"] = 100.0

        self.ensure_watching(str(root), folder_id)
        return self.get_status()

    def start_scan_async(
        self, folder_path: str, recursive: bool = True, force_reanalyze: bool = False
    ) -> Dict[str, Any]:
        with self._lock:
            if self.status["status"] in ("indexing", "analyzing"):
                return self.get_status()

        self._scan_thread = threading.Thread(
            target=self.scan_folder_sync,
            args=(folder_path, recursive, force_reanalyze),
            daemon=True,
        )
        self._scan_thread.start()
        time.sleep(0.05)
        return self.get_status()

    def reanalyze_library_sync(self) -> Dict[str, Any]:
        """Re-runs the neural recognition pipeline across all existing photos in the library."""
        rows = self.db.reset_ai_analysis()
        total = len(rows)
        with self._lock:
            self._cancel_requested = False
            self.status.update(
                {
                    "status": "analyzing" if total > 0 else "completed",
                    "current_folder": "Re-analyzing Library",
                    "current_file": "Starting neural analysis..." if total > 0 else None,
                    "total_files": total,
                    "indexed_files": total,
                    "analyzed_files": 0,
                    "progress_percent": 0.0 if total > 0 else 100.0,
                    "speed_fps": 0.0,
                    "error_message": None,
                }
            )

        start_time = time.time()
        for idx, r in enumerate(rows):
            with self._lock:
                if self._cancel_requested:
                    self.status["status"] = "idle"
                    self.status["current_file"] = None
                    break
                self.status["current_file"] = os.path.basename(r["path"])

            if os.path.exists(r["path"]):
                try:
                    self.ai_engine.process_photo(r["id"], r["path"], r["file_hash"] or "")
                    self.db.sync_photo_xmp_sidecar(r["id"])
                except Exception:
                    pass

            elapsed = max(0.01, time.time() - start_time)
            done = idx + 1
            with self._lock:
                self.status["analyzed_files"] = done
                self.status["progress_percent"] = round((done / total) * 100.0, 1)
                self.status["speed_fps"] = round(done / elapsed, 2)

        with self._lock:
            if not self._cancel_requested:
                self.status["status"] = "completed"
                self.status["current_file"] = None
                self.status["progress_percent"] = 100.0
        return self.get_status()

    def start_reanalyze_library_async(self) -> Dict[str, Any]:
        with self._lock:
            if self.status["status"] in ("indexing", "analyzing"):
                return self.get_status()
        self._scan_thread = threading.Thread(
            target=self.reanalyze_library_sync,
            daemon=True,
        )
        self._scan_thread.start()
        time.sleep(0.05)
        return self.get_status()

    def ensure_watching(self, folder_path: str, folder_id: int):
        settings = self.db.get_settings()
        if not settings.get("watch_folders", True):
            return
        norm_path = str(Path(folder_path).resolve())
        if norm_path in self._watched_paths:
            return
        try:
            if self._observer is None:
                self._observer = Observer()
                self._observer.daemon = True
                self._observer.start()
            handler = PhotoWatchHandler(self, folder_id)
            self._observer.schedule(handler, norm_path, recursive=True)
            self._watched_paths.add(norm_path)
        except Exception:
            pass
