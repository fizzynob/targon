import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from backend.app import app


def main():
    # If library is completely empty on first launch, seed the demo dataset in a daemon thread so uvicorn binds immediately
    def seed_if_empty():
        try:
            stats = app.state.db.get_library_stats()
            if stats["total_photos"] == 0:
                from backend.sample_generator import ensure_sample_drive_photos

                sample_dir = ensure_sample_drive_photos()
                app.state.scanner.scan_folder_sync(sample_dir, recursive=True)
                blu_path = str(
                    (Path(sample_dir) / "Cats_Blu" / "01_blu_sofa_portrait.jpg").resolve()
                )
                photo = app.state.db.get_photo_by_path(blu_path) or app.state.db.get_photo_by_path(
                    str((Path(sample_dir) / "01_blu_sofa_portrait.jpg").resolve())
                )
                if photo:
                    conn = app.state.db._get_conn()
                    try:
                        ps_row = conn.execute(
                            "SELECT subject_id FROM photo_subjects WHERE photo_id = ?",
                            (photo["id"],),
                        ).fetchone()
                    finally:
                        conn.close()
                    if ps_row:
                        app.state.db.rename_subject(ps_row["subject_id"], "Blu", category="cat")
        except Exception as e:
            print(f"Initial seed warning: {e}")

    import threading
    threading.Thread(target=seed_if_empty, daemon=True).start()

    import os
    port = int(os.environ.get("TARGON_PORT", "8420"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
