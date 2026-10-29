from pathlib import Path
from PIL import Image
from backend.db.database import Database
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.drive_scanner import DriveScanner
from backend.ai.engine import AIEngine


def test_drive_scanner_and_thumbnailer(tmp_path: Path):
    db_file = str(tmp_path / "test.db")
    cache_dir = str(tmp_path / "cache")
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)

    # Create two sample test images
    img1 = Image.new("RGB", (640, 480), (95, 110, 128))
    img1.save(photos_dir / "sample1.jpg", "JPEG")

    img2 = Image.new("RGB", (800, 600), (210, 125, 45))
    img2.save(photos_dir / "sample2.png", "PNG")

    db = Database(db_path=db_file)
    thumbnailer = Thumbnailer(cache_dir=cache_dir)
    ai_engine = AIEngine(db=db, thumbnailer=thumbnailer)
    scanner = DriveScanner(db=db, thumbnailer=thumbnailer, ai_engine=ai_engine)

    status = scanner.scan_folder_sync(str(photos_dir), recursive=True)
    assert status["status"] == "completed"
    assert status["total_files"] == 2
    assert status["indexed_files"] == 2
    assert status["analyzed_files"] == 2

    photos = db.query_photos()
    assert len(photos) == 2
    for p in photos:
        assert p["ai_processed"] is True
        assert p["width"] > 0 and p["height"] > 0
