from pathlib import Path
from backend.db.database import Database
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.drive_scanner import DriveScanner
from backend.ai.engine import AIEngine
from backend.sample_generator import ensure_sample_drive_photos


def test_blu_vs_other_cat_differentiation_and_three_root_systems(tmp_path: Path):
    """
    Verifies the core requirements and the 3 Root Systems:
      1. Type Root:   Blu -> Cat -> Animal (and differs from another cat entirely)
      2. Drive Root:  In Subfolder -> In Folder -> In Drive
      3. Device Root: EXIF Device + Capture Time -> Image Type (JPEG, PNG, WEBP)
    """
    db_file = str(tmp_path / "test_cats.db")
    cache_dir = str(tmp_path / "cache")
    sample_dir = ensure_sample_drive_photos()

    db = Database(db_path=db_file)
    thumbnailer = Thumbnailer(cache_dir=cache_dir)
    ai_engine = AIEngine(db=db, thumbnailer=thumbnailer)
    scanner = DriveScanner(db=db, thumbnailer=thumbnailer, ai_engine=ai_engine)

    scanner.scan_folder_sync(sample_dir, recursive=True)

    blu_photo_1 = db.get_photo_by_path(
        str(Path(sample_dir) / "Cats_Blu" / "01_blu_sofa_portrait.jpg")
    )
    assert blu_photo_1 is not None

    all_photos = {p["filename"]: p for p in db.query_photos(limit=100)}
    blu_subj_id = all_photos["01_blu_sofa_portrait.jpg"]["subjects"][0]["subject_id"]

    # Name this cluster "Blu"
    db.rename_subject(blu_subj_id, "Blu", category="cat")

    updated_photos = {p["filename"]: p for p in db.query_photos(limit=100)}

    # 1. Verify Type Root: Blu -> Cat -> Animal for all 3 Blu photos
    for blu_fn in (
        "01_blu_sofa_portrait.jpg",
        "02_blu_afternoon_window.jpg",
        "03_blu_closeup_gaze.png",
    ):
        p = updated_photos[blu_fn]
        tag_names = {t["name"].lower(): t["tag_type"] for t in p["tags"]}
        assert "blu" in tag_names
        assert "cat" in tag_names
        assert "animal" in tag_names
        assert p["root_systems"]["type_root"]["chain"] == ["Blu", "Cat", "Animal"]

        # 2. Verify Drive Root: Cats_Blu -> sample_drive_photos -> Drive
        dr = p["root_systems"]["drive_root"]
        assert dr["subfolder"] == "Cats_Blu"
        assert dr["folder"] == "sample_drive_photos"

    # 3. Verify Device Root (EXIF Device + Time -> Image Type)
    p1_dev = updated_photos["01_blu_sofa_portrait.jpg"]["root_systems"]["device_root"]
    assert "iPhone 16 Pro" in p1_dev["device"]
    assert p1_dev["date_taken"].startswith("2026-10-20")
    assert p1_dev["image_type"] == "JPEG"

    p3_dev = updated_photos["03_blu_closeup_gaze.png"]["root_systems"]["device_root"]
    assert "Alpha A7R V" in p3_dev["device"]
    assert p3_dev["image_type"] == "PNG"

    # 4. Verify the other cat is in a different cluster, NOT tagged Blu, but still Cat -> Animal
    for other_cat_fn in (
        "04_other_cat_ginger_tabby.jpg",
        "05_other_cat_sunny_garden.webp",
    ):
        p = updated_photos[other_cat_fn]
        tag_names = {t["name"].lower(): t["tag_type"] for t in p["tags"]}
        assert "cat" in tag_names
        assert "animal" in tag_names
        assert "blu" not in tag_names
        assert p["subjects"][0]["subject_id"] != blu_subj_id
        assert p["root_systems"]["type_root"]["category"] == "Cat"
        assert p["root_systems"]["type_root"]["super_type"] == "Animal"
        assert p["root_systems"]["drive_root"]["subfolder"] == "Cats_Other"
