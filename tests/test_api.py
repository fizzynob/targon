from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import create_app


def test_api_endpoints_and_three_roots(tmp_path: Path):
    db_file = str(tmp_path / "api_test.db")
    cache_dir = str(tmp_path / "api_cache")
    app = create_app(db_path=db_file, cache_dir=cache_dir)
    client = TestClient(app)

    # 1. Health & Settings
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # 2. Scan Demo Library
    r_demo = client.post("/api/scan/demo")
    assert r_demo.status_code == 200
    data = r_demo.json()
    assert data["stats"]["total_photos"] >= 8

    # 3. Verify /api/roots returns all 3 Root System trees (type_tree, drive_tree, device_tree)
    r_roots = client.get("/api/roots")
    assert r_roots.status_code == 200
    roots = r_roots.json()
    assert len(roots["type_tree"]) > 0
    assert len(roots["drive_tree"]) > 0
    assert len(roots["device_tree"]) > 0

    # 4. Query photos by Root 1: Type ('Blu' -> 'Cat' -> 'Animal')
    r_blu = client.get("/api/photos", params={"search": "Blu"})
    assert len(r_blu.json()) == 3

    r_cats = client.get("/api/photos", params={"category": "cat"})
    assert len(r_cats.json()) == 5

    r_animals = client.get("/api/photos", params={"super_type": "Animal"})
    assert len(r_animals.json()) == 6  # 5 cats + 1 dog

    # 5. Query photos by Root 2: Drive (Subfolder -> Folder -> Drive)
    r_sub = client.get("/api/photos", params={"subfolder_name": "Cats_Blu"})
    assert len(r_sub.json()) == 3

    # 6. Query photos by Root 3: Device (EXIF Device + Time -> Image Type)
    r_dev = client.get("/api/photos", params={"device_name": "Apple iPhone 16 Pro"})
    assert len(r_dev.json()) == 3

    r_png = client.get("/api/photos", params={"image_type": "PNG"})
    assert len(r_png.json()) == 1

    # 7. Test Delete Single Photo
    all_photos = client.get("/api/photos").json()
    first_id = all_photos[0]["id"]
    r_del = client.delete(f"/api/photos/{first_id}")
    assert r_del.status_code == 200
    assert r_del.json()["status"] == "deleted"

    # 8. Test Clear Library
    r_clear = client.post("/api/library/clear", json={"delete_files": False})
    assert r_clear.status_code == 200
    assert r_clear.json()["status"] == "success"
    assert len(client.get("/api/photos").json()) == 0


def test_game_detection_and_filtering(tmp_path: Path):
    db_file = str(tmp_path / "game_test.db")
    cache_dir = str(tmp_path / "game_cache")
    app = create_app(db_path=db_file, cache_dir=cache_dir)
    client = TestClient(app)

    db = app.state.db
    # Insert a game asset
    db.upsert_photo({
        "path": "C:/Games/Steam/textures/unit_sprite.png",
        "filename": "unit_sprite.png",
        "width": 104,
        "height": 104,
        "file_size": 15000,
        "image_type": "PNG",
        "drive_root": "C:",
        "folder_name": "Steam",
        "subfolder_name": "textures",
        "device_name": "Unknown Device",
        "is_game_asset": 1,
    })

    # Insert a real camera photo
    db.upsert_photo({
        "path": "C:/Users/f1zzy/Pictures/vacation/lake.jpg",
        "filename": "lake.jpg",
        "width": 4032,
        "height": 3024,
        "file_size": 2500000,
        "image_type": "JPEG",
        "drive_root": "C:",
        "folder_name": "Pictures",
        "subfolder_name": "vacation",
        "device_name": "Apple iPhone 16 Pro",
        "is_game_asset": 0,
    })

    # 1. Default query with game_detection=1 setting -> returns only real photo
    r_default = client.get("/api/photos")
    assert r_default.status_code == 200
    photos = r_default.json()
    assert len(photos) == 1
    assert photos[0]["filename"] == "lake.jpg"
    assert photos[0]["is_game_asset"] is False

    # 2. Query with exclude_games=False -> returns both photos
    r_all = client.get("/api/photos", params={"exclude_games": False})
    assert len(r_all.json()) == 2

    # 3. Query with exclude_games=True -> returns only lake.jpg
    r_excl = client.get("/api/photos", params={"exclude_games": True})
    assert len(r_excl.json()) == 1
    assert r_excl.json()[0]["filename"] == "lake.jpg"

    # 4. Check three roots with exclude_games=True vs False
    roots_excl = client.get("/api/roots", params={"exclude_games": True}).json()
    assert len(roots_excl["device_tree"]) == 1
    assert roots_excl["device_tree"][0]["name"] == "Apple iPhone 16 Pro"

    roots_all = client.get("/api/roots", params={"exclude_games": False}).json()
    assert len(roots_all["device_tree"]) == 2

    # 5. Update settings to disable game_detection
    r_set = client.put("/api/settings", json={"game_detection": False, "sound_effects": True})
    assert r_set.status_code == 200
    assert r_set.json()["game_detection"] is False

    # Now default query returns both
    r_new_default = client.get("/api/photos")
    assert len(r_new_default.json()) == 2


def test_rating_rotation_sorting_and_batch_operations(tmp_path: Path):
    db_file = str(tmp_path / "curation_test.db")
    cache_dir = str(tmp_path / "curation_cache")
    app = create_app(db_path=db_file, cache_dir=cache_dir)
    client = TestClient(app)

    # 1. Scan demo library
    r_demo = client.post("/api/scan/demo")
    assert r_demo.status_code == 200

    photos = client.get("/api/photos").json()
    assert len(photos) >= 5
    p1 = photos[0]
    p2 = photos[1]
    p3 = photos[2]

    # 2. Test Single Photo Star Rating
    r_rate = client.post(f"/api/photos/{p1['id']}/rating", json={"rating": 5})
    assert r_rate.status_code == 200
    assert r_rate.json()["rating"] == 5

    # 3. Test Photo Rotation
    r_rot1 = client.post(f"/api/photos/{p1['id']}/rotate", json={"degrees": 90})
    assert r_rot1.status_code == 200
    assert r_rot1.json()["rotation"] == 90

    r_rot2 = client.post(f"/api/photos/{p1['id']}/rotate", json={"degrees": 90})
    assert r_rot2.json()["rotation"] == 180

    # 4. Test Batch Rating (4 stars on p2 and p3)
    r_br = client.post(
        "/api/photos/batch-rating",
        json={"photo_ids": [p2["id"], p3["id"]], "rating": 4},
    )
    assert r_br.status_code == 200
    assert r_br.json()["rated_count"] == 2

    # 5. Test Batch Tagging ("Masterpiece Selection")
    r_bt = client.post(
        "/api/photos/batch-tag",
        json={"photo_ids": [p1["id"], p2["id"], p3["id"]], "tag_name": "Masterpiece Selection"},
    )
    assert r_bt.status_code == 200
    assert r_bt.json()["tagged_count"] == 3

    # Verify batch tag query
    r_tag_search = client.get("/api/photos", params={"tag": "Masterpiece Selection"})
    assert len(r_tag_search.json()) == 3

    # 6. Test Min Rating Filtering (min_rating=4 vs min_rating=5)
    r_min4 = client.get("/api/photos", params={"min_rating": 4})
    assert len(r_min4.json()) == 3  # p1 (5 stars), p2 (4 stars), p3 (4 stars)

    r_min5 = client.get("/api/photos", params={"min_rating": 5})
    assert len(r_min5.json()) == 1
    assert r_min5.json()[0]["id"] == p1["id"]

    # 7. Test Sorting: Name Ascending
    r_sort_name = client.get("/api/photos", params={"sort_by": "name_asc"})
    names = [p["filename"].lower() for p in r_sort_name.json()]
    assert names == sorted(names)

    # 8. Test Sorting: Rating Descending
    r_sort_rating = client.get("/api/photos", params={"sort_by": "rating_desc"})
    ratings = [p.get("rating", 0) for p in r_sort_rating.json()]
    assert ratings[0] == 5
    assert ratings[1] == 4
    assert ratings[2] == 4


def test_orientation_and_duplicate_filtering(tmp_path: Path):
    db_file = str(tmp_path / "dup_test.db")
    cache_dir = str(tmp_path / "dup_cache")
    app = create_app(db_path=db_file, cache_dir=cache_dir)
    client = TestClient(app)
    db = app.state.db

    # Insert landscape photo
    db.upsert_photo({
        "path": "C:/photos/landscape.jpg",
        "filename": "landscape.jpg",
        "width": 1920,
        "height": 1080,
        "file_hash": "hash_same_123",
        "date_taken": "2026-10-25 12:00:00",
    })
    # Insert portrait photo (same hash -> duplicate)
    db.upsert_photo({
        "path": "C:/photos/portrait.jpg",
        "filename": "portrait.jpg",
        "width": 1080,
        "height": 1920,
        "file_hash": "hash_same_123",
        "date_taken": "2026-10-25 12:00:02",
    })
    # Insert unique square photo
    db.upsert_photo({
        "path": "C:/photos/square.jpg",
        "filename": "square.jpg",
        "width": 800,
        "height": 800,
        "file_hash": "hash_unique_456",
        "date_taken": "2026-10-25 12:05:00",
    })

    # Test orientation landscape
    r_land = client.get("/api/photos", params={"orientation": "landscape"})
    assert len(r_land.json()) == 1
    assert r_land.json()[0]["filename"] == "landscape.jpg"

    # Test orientation portrait
    r_port = client.get("/api/photos", params={"orientation": "portrait"})
    assert len(r_port.json()) == 1
    assert r_port.json()[0]["filename"] == "portrait.jpg"

    # Test duplicates_only
    r_dups = client.get("/api/photos", params={"duplicates_only": True})
    assert len(r_dups.json()) == 2
    filenames = {p["filename"] for p in r_dups.json()}
    assert filenames == {"landscape.jpg", "portrait.jpg"}


def test_expanded_settings_and_300_placeholder_generation(tmp_path: Path):
    from backend.sample_generator import generate_300_placeholder_photos

    db_file = str(tmp_path / "perf_test.db")
    cache_dir = str(tmp_path / "perf_cache")
    app = create_app(db_path=db_file, cache_dir=cache_dir)
    client = TestClient(app)

    # 1. Verify expanded settings persistence & retrieval
    r_update = client.put(
        "/api/settings",
        json={
            "low_spec_mode": True,
            "scan_threads": 4,
            "fast_tagging": True,
            "enable_clip_search": False,
            "enable_ocr": False,
            "enable_face_detection": False,
            "enable_scene_analysis": False,
            "thumbnail_quality": "fast",
            "skip_small_images": True,
            "default_grid_cols": 6,
            "group_by_date_default": False,
            "reduce_motion": True,
            "show_card_tags": False,
            "confirm_before_delete": True,
        },
    )
    assert r_update.status_code == 200
    saved = r_update.json()
    assert saved["low_spec_mode"] is True
    assert saved["scan_threads"] == 4
    assert saved["fast_tagging"] is True
    assert saved["thumbnail_quality"] == "fast"
    assert saved["default_grid_cols"] == 6
    assert saved["group_by_date_default"] is False
    assert saved["reduce_motion"] is True
    assert saved["show_card_tags"] is False
    assert saved["confirm_before_delete"] is True

    # 2. Verify 300 placeholder photo generator creates exactly 300 images
    p300_dir = tmp_path / "p300_gen"
    out_dir = generate_300_placeholder_photos(target_dir=str(p300_dir), total_count=300)
    all_generated = [
        p for p in Path(out_dir).rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".png"}
    ]
    assert len(all_generated) == 300

    # 3. Verify scanning with optimized pipeline indexes & tags rapidly
    scanner = app.state.scanner
    status = scanner.scan_folder_sync(str(p300_dir), recursive=True)
    assert status["status"] == "completed"
    assert status["total_files"] == 300
    assert status["indexed_files"] == 300
    assert status["speed_fps"] > 0

    r_stats = client.get("/api/stats")
    assert r_stats.status_code == 200
    assert r_stats.json()["total_photos"] == 300




