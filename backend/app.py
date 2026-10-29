import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db.database import Database
from backend.db.models import (
    RenameSubjectRequest,
    MergeSubjectsRequest,
    ReassignPhotoSubjectRequest,
    AddTagRequest,
    StartScanRequest,
    SettingsModel,
    BatchDeletePhotosRequest,
    ClearLibraryRequest,
    SetRatingRequest,
    RotatePhotoRequest,
    BatchTagRequest,
    BatchRatingRequest,
)
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.drive_scanner import DriveScanner
from backend.ai.engine import AIEngine
from backend.sample_generator import ensure_sample_drive_photos, generate_300_placeholder_photos


def create_app(db_path: Optional[str] = None, cache_dir: Optional[str] = None) -> FastAPI:
    app = FastAPI(
        title="Targon AI Photo Engine",
        description="Apple-inspired Drive Photo Scanner & Neural Network Pet/Entity Identifier",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db = Database(db_path=db_path)
    thumbnailer = Thumbnailer(cache_dir=cache_dir)
    ai_engine = AIEngine(db=db, thumbnailer=thumbnailer)
    scanner = DriveScanner(db=db, thumbnailer=thumbnailer, ai_engine=ai_engine)

    # Store references on app.state for testing and direct access
    app.state.db = db
    app.state.thumbnailer = thumbnailer
    app.state.ai_engine = ai_engine
    app.state.scanner = scanner

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "service": "targon-backend"}

    @app.get("/favicon.ico")
    def get_favicon():
        fav_path = Path(__file__).resolve().parent.parent / "frontend" / "public" / "favicon.ico"
        if fav_path.exists():
            return FileResponse(fav_path, media_type="image/x-icon")
        return {"status": "not found"}

    @app.get("/icon.png")
    def get_icon_png():
        p = Path(__file__).resolve().parent.parent / "frontend" / "public" / "icon.png"
        if p.exists():
            return FileResponse(p, media_type="image/png")
        return {"status": "not found"}

    @app.get("/favicon-32x32.png")
    def get_favicon_32():
        p = Path(__file__).resolve().parent.parent / "frontend" / "public" / "favicon-32x32.png"
        if p.exists():
            return FileResponse(p, media_type="image/png")
        return {"status": "not found"}

    @app.get("/favicon-16x16.png")
    def get_favicon_16():
        p = Path(__file__).resolve().parent.parent / "frontend" / "public" / "favicon-16x16.png"
        if p.exists():
            return FileResponse(p, media_type="image/png")
        return {"status": "not found"}

    @app.get("/apple-touch-icon.png")
    def get_apple_touch_icon():
        p = Path(__file__).resolve().parent.parent / "frontend" / "public" / "apple-touch-icon.png"
        if p.exists():
            return FileResponse(p, media_type="image/png")
        return {"status": "not found"}

    @app.get("/api/stats")
    def get_stats():
        return db.get_library_stats()

    @app.get("/api/roots")
    def get_three_roots(exclude_games: Optional[bool] = Query(default=None)):
        return db.get_three_root_trees(exclude_games=exclude_games)

    @app.get("/api/settings")
    def get_settings():
        return db.get_settings()

    @app.put("/api/settings")
    def update_settings(payload: SettingsModel):
        return db.update_settings(payload.model_dump())

    @app.get("/api/photos")
    def list_photos(
        search: Optional[str] = Query(default=None),
        subject_id: Optional[int] = Query(default=None),
        tag: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None),
        super_type: Optional[str] = Query(default=None),
        folder_id: Optional[int] = Query(default=None),
        drive_root: Optional[str] = Query(default=None),
        folder_name: Optional[str] = Query(default=None),
        subfolder_name: Optional[str] = Query(default=None),
        device_name: Optional[str] = Query(default=None),
        capture_date: Optional[str] = Query(default=None),
        image_type: Optional[str] = Query(default=None),
        favorites_only: bool = Query(default=False),
        exclude_games: Optional[bool] = Query(default=None),
        min_rating: Optional[int] = Query(default=None),
        orientation: Optional[str] = Query(default=None),
        duplicates_only: bool = Query(default=False),
        sort_by: str = Query(default="date_desc"),
        limit: int = Query(default=500),
        offset: int = Query(default=0),
    ):
        return db.query_photos(
            search=search,
            subject_id=subject_id,
            tag=tag,
            category=category,
            super_type=super_type,
            folder_id=folder_id,
            drive_root=drive_root,
            folder_name=folder_name,
            subfolder_name=subfolder_name,
            device_name=device_name,
            capture_date=capture_date,
            image_type=image_type,
            favorites_only=favorites_only,
            exclude_games=exclude_games,
            min_rating=min_rating,
            orientation=orientation,
            duplicates_only=duplicates_only,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

    @app.post("/api/xmp/export-all")
    def export_all_xmp():
        count = db.export_all_xmp_sidecars()
        return {"status": "exported", "count": count}

    @app.post("/api/xmp/import-all")
    def import_all_xmp():
        count = db.import_all_xmp_sidecars()
        return {"status": "imported", "count": count}

    @app.get("/api/photos/{photo_id}/xmp")
    def get_photo_xmp(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute("SELECT path FROM photos WHERE id = ?", (photo_id,)).fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")
        from backend.scanner.xmp_sidecar import get_xmp_path
        xmp_p = get_xmp_path(row["path"])
        if not xmp_p.exists():
            return {"exists": False, "path": str(xmp_p), "content": None}
        try:
            with open(xmp_p, "r", encoding="utf-8") as f:
                content = f.read()
            return {"exists": True, "path": str(xmp_p), "content": content}
        except Exception as e:
            return {"exists": True, "path": str(xmp_p), "error": str(e)}

    @app.post("/api/photos/{photo_id}/favorite")
    def toggle_favorite(photo_id: int):
        is_fav = db.toggle_favorite_photo(photo_id)
        return {"photo_id": photo_id, "is_favorite": is_fav}

    @app.post("/api/photos/{photo_id}/rating")
    def set_rating(photo_id: int, req: SetRatingRequest):
        new_rating = db.set_photo_rating(photo_id, req.rating)
        return {"photo_id": photo_id, "rating": new_rating}

    @app.post("/api/photos/{photo_id}/rotate")
    def rotate_photo(photo_id: int, req: RotatePhotoRequest):
        new_rot = db.rotate_photo(photo_id, req.degrees)
        return {"photo_id": photo_id, "rotation": new_rot}

    @app.post("/api/photos/batch-tag")
    def batch_tag(req: BatchTagRequest):
        count = db.batch_add_tag(req.photo_ids, req.tag_name, req.tag_type)
        return {"status": "ok", "tagged_count": count}

    @app.post("/api/photos/batch-rating")
    def batch_rating(req: BatchRatingRequest):
        count = db.batch_set_rating(req.photo_ids, req.rating)
        return {"status": "ok", "rated_count": count}

    @app.post("/api/photos/{photo_id}/tags")
    def add_tag_to_photo(photo_id: int, req: AddTagRequest):
        db.add_photo_tag(
            photo_id=photo_id,
            tag_name=req.name,
            tag_type=req.tag_type,
            confidence=1.0,
            source="user",
        )
        photos = db.query_photos(limit=500)
        for p in photos:
            if p["id"] == photo_id:
                return p
        return {"status": "ok"}

    @app.delete("/api/photos/{photo_id}/tags/{tag_id}")
    def remove_tag_from_photo(photo_id: int, tag_id: int):
        db.remove_photo_tag(photo_id, tag_id)
        return {"status": "ok"}

    @app.post("/api/photos/{photo_id}/reanalyze")
    def reanalyze_photo(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")
        scanner.index_and_analyze_single_file(
            row["path"], folder_id=row["folder_id"], force_reanalyze=True
        )
        items = db.query_photos(limit=500)
        for it in items:
            if it["id"] == photo_id:
                return it
        return {"status": "ok"}

    @app.post("/api/photos/{photo_id}/reveal")
    def reveal_in_explorer(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute("SELECT path FROM photos WHERE id = ?", (photo_id,)).fetchone()
        finally:
            conn.close()
        if not row or not os.path.exists(row["path"]):
            raise HTTPException(status_code=404, detail="File not found on disk")
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(row["path"])])
        return {"status": "opened", "path": row["path"]}

    @app.get("/api/photos/{photo_id}/thumbnail")
    def get_photo_thumbnail(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute(
                "SELECT thumbnail_path, path FROM photos WHERE id = ?", (photo_id,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")
        for candidate in (row["thumbnail_path"], row["path"]):
            if candidate and os.path.exists(candidate):
                return FileResponse(candidate)
        raise HTTPException(status_code=404, detail="Image file missing")

    @app.get("/api/photos/{photo_id}/preview")
    def get_photo_preview(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute(
                "SELECT preview_path, path FROM photos WHERE id = ?", (photo_id,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")
        for candidate in (row["preview_path"], row["path"]):
            if candidate and os.path.exists(candidate):
                return FileResponse(candidate)
        raise HTTPException(status_code=404, detail="Image file missing")

    @app.get("/api/photos/{photo_id}/original")
    def get_photo_original(photo_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute("SELECT path FROM photos WHERE id = ?", (photo_id,)).fetchone()
        finally:
            conn.close()
        if not row or not os.path.exists(row["path"]):
            raise HTTPException(status_code=404, detail="Original file missing")
        return FileResponse(row["path"])

    @app.delete("/api/photos/{photo_id}")
    def delete_single_photo(photo_id: int, delete_file: bool = False):
        success = db.delete_photo(photo_id, delete_file=delete_file)
        if not success:
            raise HTTPException(status_code=404, detail="Photo not found")
        return {"status": "deleted", "photo_id": photo_id}

    @app.post("/api/photos/batch-delete")
    def batch_delete_photos(req: BatchDeletePhotosRequest):
        count = db.delete_photos(req.photo_ids, delete_file=req.delete_files)
        return {"status": "deleted", "count": count}

    @app.post("/api/library/clear")
    def clear_entire_library(req: ClearLibraryRequest = ClearLibraryRequest()):
        res = db.clear_library(delete_files=req.delete_files)
        return res

    @app.post("/api/library/reanalyze")
    def reanalyze_entire_library():
        return scanner.start_reanalyze_library_async()

    # --- Subjects & Pet Re-Identification ---
    @app.get("/api/subjects")
    def list_subjects():
        return db.get_subjects()

    @app.get("/api/subjects/{subject_id}/avatar")
    def get_subject_avatar(subject_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute(
                "SELECT avatar_path FROM subjects WHERE id = ?", (subject_id,)
            ).fetchone()
        finally:
            conn.close()
        if row and row["avatar_path"] and os.path.exists(row["avatar_path"]):
            return FileResponse(row["avatar_path"])
        raise HTTPException(status_code=404, detail="Avatar not found")

    @app.get("/api/photo-subjects/{ps_id}/crop")
    def get_photo_subject_crop(ps_id: int):
        conn = db._get_conn()
        try:
            row = conn.execute(
                "SELECT crop_path FROM photo_subjects WHERE id = ?", (ps_id,)
            ).fetchone()
        finally:
            conn.close()
        if row and row["crop_path"] and os.path.exists(row["crop_path"]):
            return FileResponse(row["crop_path"])
        raise HTTPException(status_code=404, detail="Crop not found")

    @app.post("/api/subjects/{subject_id}/rename")
    def rename_subject(subject_id: int, req: RenameSubjectRequest):
        updated = db.rename_subject(subject_id, req.name, req.category)
        if not updated:
            raise HTTPException(status_code=404, detail="Subject not found")
        return updated

    @app.post("/api/subjects/merge")
    def merge_subjects(req: MergeSubjectsRequest):
        merged = db.merge_subjects(req.source_subject_id, req.target_subject_id)
        if not merged:
            raise HTTPException(status_code=400, detail="Could not merge subjects")
        return merged

    @app.post("/api/photo-subjects/{ps_id}/reassign")
    def reassign_photo_subject(ps_id: int, req: ReassignPhotoSubjectRequest):
        updated = db.reassign_photo_subject(ps_id, req.new_name, req.category)
        if not updated:
            raise HTTPException(status_code=404, detail="Photo subject not found")
        return updated

    # --- Tags ---
    @app.get("/api/tags")
    def list_tags():
        return db.get_all_tags()

    # --- Folders & Drive Scanning ---
    @app.get("/api/folders")
    def list_folders():
        return db.get_folders()

    @app.delete("/api/folders/{folder_id}")
    def remove_folder(folder_id: int):
        db.delete_folder(folder_id)
        return {"status": "deleted", "folder_id": folder_id}

    @app.get("/api/drives")
    def list_drives_and_quick_folders():
        """Returns system drives and quick-access user photo folders for the Drive Picker UI."""
        home = Path.home()
        quick_folders: List[Dict[str, str]] = []
        demo_dir = Path(__file__).resolve().parent.parent / "sample_drive_photos"
        quick_folders.append(
            {
                "name": "Demo Library (Blu & Friends)",
                "path": str(demo_dir.resolve()),
                "type": "demo",
            }
        )
        for label, sub in [
            ("Pictures", "Pictures"),
            ("Desktop", "Desktop"),
            ("Downloads", "Downloads"),
            ("Documents", "Documents"),
        ]:
            cand = home / sub
            if cand.exists():
                quick_folders.append({"name": label, "path": str(cand.resolve()), "type": "user"})

        drives: List[Dict[str, str]] = []
        if os.name == "nt":
            for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_root = f"{letter}:\\"
                if os.path.exists(drive_root):
                    drives.append({"name": f"Local Disk ({letter}:)", "path": drive_root, "type": "drive"})
        else:
            drives.append({"name": "Root (/)", "path": "/", "type": "drive"})

        return {"quick_folders": quick_folders, "drives": drives}

    @app.post("/api/scan/start")
    def start_scan(req: StartScanRequest):
        return scanner.start_scan_async(req.folder_path, recursive=req.recursive)

    @app.post("/api/scan/demo")
    def scan_demo_library():
        """
        Ensures the sample photo dataset ('Blu' the Russian Blue cat, another ginger cat,
        a golden retriever dog, and scenic landscapes) exists, scans it, and names the
        Russian Blue cat cluster 'Blu' so the user can immediately explore the exact feature!
        """
        sample_dir = ensure_sample_drive_photos()
        scanner.scan_folder_sync(sample_dir, recursive=True)

        # Find the subject attached to 01_blu_sofa_portrait.jpg and name it 'Blu' if still unnamed
        blu_photo_path = str(
            (Path(sample_dir) / "Cats_Blu" / "01_blu_sofa_portrait.jpg").resolve()
        )
        photo = db.get_photo_by_path(blu_photo_path) or db.get_photo_by_path(
            str((Path(sample_dir) / "01_blu_sofa_portrait.jpg").resolve())
        )
        if photo:
            conn = db._get_conn()
            try:
                ps_row = conn.execute(
                    """
                    SELECT ps.subject_id, s.is_named
                    FROM photo_subjects ps
                    JOIN subjects s ON s.id = ps.subject_id
                    WHERE ps.photo_id = ?
                    """,
                    (photo["id"],),
                ).fetchone()
            finally:
                conn.close()
            if ps_row and not ps_row["is_named"]:
                db.rename_subject(ps_row["subject_id"], "Blu", category="cat")

        return {
            "status": "completed",
            "folder_path": sample_dir,
            "stats": db.get_library_stats(),
        }

    @app.post("/api/scan/placeholder-300")
    def scan_placeholder_300(sync: bool = Query(default=False)):
        """
        Generates 300 diverse placeholder images on disk and starts scanning them
        so the user can benchmark scan speed (img/sec) and test large library performance.
        """
        placeholder_dir = generate_300_placeholder_photos(total_count=300)
        if sync:
            st = scanner.scan_folder_sync(placeholder_dir, recursive=True, force_reanalyze=True)
            return {
                "status": st["status"],
                "folder_path": placeholder_dir,
                "total_generated": 300,
                "scan_status": st,
                "stats": db.get_library_stats(),
            }
        st = scanner.start_scan_async(placeholder_dir, recursive=True, force_reanalyze=True)
        return {
            "status": st["status"],
            "folder_path": placeholder_dir,
            "total_generated": 300,
            "scan_status": st,
        }

    @app.post("/api/scan/cancel")
    def cancel_scan():
        scanner.cancel_scan()
        return scanner.get_status()

    @app.get("/api/scan/status")
    def get_scan_status():
        return scanner.get_status()

    # Mount built frontend static files at root / for direct browser access
    dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    return app


app = create_app()
