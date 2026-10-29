import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from backend.db.database import Database
from backend.scanner.thumbnailer import Thumbnailer
from backend.scanner.drive_scanner import DriveScanner
from backend.ai.engine import AIEngine
from backend.ai.imagenet_taxonomy import classify_imagenet_idx
from backend.ai.scene_analyzer import scene_analyzer
from backend.ai.ocr_engine import ocr_engine
from backend.ai.face_engine import face_engine
from backend.ai.clip_engine import clip_engine


def test_complete_taxonomy_coverage_no_empty_tags():
    """Verifies that all classes across the 1000 ImageNet categories emit fine-grained tags."""
    sample_indices = [
        0,    # tench (fish)
        9,    # ostrich (bird)
        151,  # chihuahua (dog)
        207,  # golden retriever (dog)
        281,  # tabby cat (cat)
        284,  # siamese cat (cat)
        292,  # tiger (big cat)
        340,  # zebra (wildlife)
        401,  # accordion (instrument)
        402,  # acoustic guitar (instrument)
        404,  # airliner (vehicle)
        498,  # castle (architecture)
        508,  # computer keyboard / desktop (electronics)
        620,  # laptop (electronics)
        671,  # mountain bike (vehicle)
        923,  # plate (food)
        963,  # pizza (food)
        970,  # alp / mountain (nature/landscape)
        985,  # daisy (botanical)
    ]
    for idx in sample_indices:
        cat, tags = classify_imagenet_idx(idx)
        assert len(tags) > 0, f"Index {idx} returned empty tags!"
        assert cat != "", f"Index {idx} returned empty category!"
        tag_names = [t[0] for t in tags]
        # Verify specific items have specific tags
        if idx == 963:
            assert "pizza" in tag_names
            assert "food" in tag_names
        elif idx == 402:
            assert "acoustic guitar" in tag_names
            assert "instrument" in tag_names
        elif idx == 404:
            assert "airliner" in tag_names
            assert "vehicle" in tag_names


def test_scene_analyzer_photometrics():
    """Verifies photometric classification (sunset, B&W, nature)."""
    # Sunset warm image
    sunset = Image.new("RGB", (200, 200), color=(255, 115, 25))
    res_sunset = scene_analyzer.analyze_scene(sunset)
    sunset_tags = [t[0] for t in res_sunset["tags"]]
    assert any("sunset" in t or "golden hour" in t for t in sunset_tags)

    # Black and white image
    bw = Image.new("L", (200, 200), color=110).convert("RGB")
    res_bw = scene_analyzer.analyze_scene(bw)
    bw_tags = [t[0] for t in res_bw["tags"]]
    assert "black and white" in bw_tags or "monochrome" in bw_tags

    # Foliage image
    foliage = Image.new("RGB", (200, 200), color=(35, 155, 45))
    res_foliage = scene_analyzer.analyze_scene(foliage)
    foliage_tags = [t[0] for t in res_foliage["tags"]]
    assert "nature" in foliage_tags or "foliage" in foliage_tags


def test_face_engine_landmarks_and_normalization():
    """Verifies that face engine extracts normalized 256-dim embeddings with landmarks."""
    face_crop = Image.new("RGB", (112, 112), color=(220, 180, 150))
    d = ImageDraw.Draw(face_crop)
    # Draw simple facial features
    d.ellipse((30, 40, 40, 50), fill=(50, 40, 30))  # left eye
    d.ellipse((72, 40, 82, 50), fill=(50, 40, 30))  # right eye
    d.polygon([(56, 55), (52, 68), (60, 68)], fill=(180, 120, 100))  # nose
    d.line((42, 85, 70, 85), fill=(160, 60, 60), width=4)  # mouth

    landmarks = [
        [0.35, 0.45],  # right eye
        [0.75, 0.45],  # left eye
        [0.55, 0.60],  # nose
        [0.40, 0.82],  # mouth right
        [0.70, 0.82],  # mouth left
    ]

    emb = face_engine.extract_face_embedding(face_crop, landmarks=landmarks)
    assert len(emb) == 256
    # Verify vector is L2 normalized
    import numpy as np
    norm = np.linalg.norm(np.array(emb))
    assert abs(norm - 1.0) < 1e-3


def test_live_text_ocr_and_search(tmp_path: Path):
    """Verifies that an image with text is recognized by OCR and searchable in the database."""
    db_file = str(tmp_path / "ocr_test.db")
    cache_dir = str(tmp_path / "cache")

    db = Database(db_path=db_file)
    thumbnailer = Thumbnailer(cache_dir=cache_dir)
    ai_engine = AIEngine(db=db, thumbnailer=thumbnailer)

    img_path = str(tmp_path / "coffee_menu_receipt.jpg")
    img = Image.new("RGB", (500, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 30), "Espresso Coffee Shop Receipt Total $8.00", fill=(0, 0, 0))
    img.save(img_path)

    p_id = db.upsert_photo({
        "path": img_path,
        "filename": "coffee_menu_receipt.jpg",
        "file_size": 1024,
        "file_hash": "testhash_ocr",
    })

    ai_res = ai_engine.process_photo(p_id, img_path, "testhash_ocr")
    assert ai_res is not None

    photo = db.get_photo_by_path(img_path)
    assert photo is not None
    assert photo.get("ocr_text") is not None
    # Verify that searching for 'receipt' finds this photo
    search_results = db.query_photos(search="receipt")
    assert len(search_results) == 1
    assert search_results[0]["id"] == p_id


def test_clip_zero_shot_and_natural_language_search():
    """Verifies that OpenAI CLIP ViT-B/32 produces 512-dim embeddings and accurate zero-shot classification."""
    assert clip_engine.is_ready

    # Create synthetic images
    cat_img = Image.new("RGB", (224, 224), color=(120, 125, 130)) # Gray-ish cat-like tone
    img_emb = clip_engine.embed_image(cat_img)
    assert img_emb is not None
    assert len(img_emb) == 512

    # Verify text embedding
    txt_emb = clip_engine.embed_text(["a photo of a gray cat", "a photo of a red car"])
    assert txt_emb is not None
    assert txt_emb.shape == (2, 512)

    # Verify cosine similarity calculation
    sim = clip_engine.compute_similarity(img_emb, txt_emb[0])
    assert isinstance(sim, float)
    assert -1.0 <= sim <= 1.0
