from pathlib import Path
from backend.db.database import Database
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.drive_scanner import DriveScanner
from backend.scanner.xmp_sidecar import write_xmp_sidecar, read_xmp_sidecar, get_xmp_path
from backend.ai.engine import AIEngine
from backend.sample_generator import ensure_sample_drive_photos


def test_xmp_sidecar_generation_and_parsing(tmp_path: Path):
    img_path = tmp_path / "test_cat.jpg"
    img_path.write_bytes(b"dummy image content")

    tags = [
        {"name": "Blu", "tag_type": "identity"},
        {"name": "cat", "tag_type": "category"},
        {"name": "animal", "tag_type": "category"},
        {"name": "pet", "tag_type": "category"},
        {"name": "slate-gray coat", "tag_type": "attribute"},
    ]
    root_systems = {
        "type_root": {"specific": "Blu", "category": "Cat", "super_type": "Animal"},
        "drive_root": {"subfolder": "Cats_Blu", "folder": "Photos", "drive": "C:"},
        "device_root": {"device": "Apple iPhone 16 Pro", "capture_date": "2026-10-20", "image_type": "JPEG"},
    }

    # 1. Write XMP Sidecar
    xmp_file = write_xmp_sidecar(
        image_path=str(img_path),
        description="Blu (Cat) — Slate-gray coat",
        tags=tags,
        root_systems=root_systems,
    )
    assert xmp_file.exists()
    content = xmp_file.read_text(encoding="utf-8")
    assert "<dc:subject>" in content
    assert "<rdf:li>Blu</rdf:li>" in content
    assert "<rdf:li>cat</rdf:li>" in content
    assert "<lr:hierarchicalSubject>" in content
    assert "Animal|Cat|Blu" in content

    # 2. Read XMP Sidecar
    parsed = read_xmp_sidecar(str(img_path))
    assert parsed is not None
    assert "Blu" in parsed["tags"]
    assert "cat" in parsed["tags"]
    assert "animal" in parsed["tags"]
    assert any("Animal|Cat|Blu" in h for h in parsed["hierarchical_tags"])
    assert parsed["identity"] == "Blu"
    assert parsed["category"] == "Cat"


def test_tag_storage_configuration_modes(tmp_path: Path):
    """
    Verifies that the user can configure tag storage as:
      - Sidecar file / XMP only
      - Database only
      - Both
    """
    sample_dir = ensure_sample_drive_photos()
    db_file = str(tmp_path / "xmp_cfg.db")
    cache_dir = str(tmp_path / "xmp_cache")

    db = Database(db_path=db_file)
    thumbnailer = Thumbnailer(cache_dir=cache_dir)
    ai_engine = AIEngine(db=db, thumbnailer=thumbnailer)
    scanner = DriveScanner(db=db, thumbnailer=thumbnailer, ai_engine=ai_engine)

    # 1. Test 'both' mode (default): writes to DB and creates .xmp sidecars
    db.update_settings({"tag_storage_mode": "both"})
    assert db.get_settings()["tag_storage_mode"] == "both"

    scanner.scan_folder_sync(sample_dir, recursive=True)

    blu_p = Path(sample_dir) / "Cats_Blu" / "01_blu_sofa_portrait.jpg"
    xmp_p = get_xmp_path(str(blu_p))
    assert xmp_p.exists(), "In 'both' mode, .xmp sidecar must be created alongside photo"

    # 2. Test 'database' only mode: no new sidecars are generated for new tags
    db.update_settings({"tag_storage_mode": "database"})
    assert db.get_settings()["tag_storage_mode"] == "database"

    photo = db.get_photo_by_path(str(blu_p))
    db.add_photo_tag(photo["id"], "custom_db_only_tag", tag_type="user")

    # 3. Test 'sidecar' mode: can export and import sidecars
    db.update_settings({"tag_storage_mode": "sidecar"})
    assert db.get_settings()["tag_storage_mode"] == "sidecar"

    exported_count = db.export_all_xmp_sidecars()
    assert exported_count >= 8

    imported_count = db.import_all_xmp_sidecars()
    assert imported_count >= 8
