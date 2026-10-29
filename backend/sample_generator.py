import io
import shutil
import urllib.request
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance, ImageOps, ImageDraw


SAMPLE_URLS = {
    "blu_base": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=900&q=85",
    "marmalade_1": "https://images.unsplash.com/photo-1511044568932-338cba0ad803?w=900&q=85",
    "marmalade_2": "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=900&q=85",
    "golden_dog_1": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=900&q=85",
    "alpine_lake": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=900&q=85",
    "coastal_beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&q=85",
}


def _fetch_url_image(url: str) -> Optional[Image.Image]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return Image.open(io.BytesIO(resp.read())).convert("RGB")
    except Exception:
        return None


def _create_fallback_image(kind: str) -> Image.Image:
    """Offline fallback generator if network is unavailable."""
    img = Image.new("RGB", (800, 600), (240, 240, 245))
    draw = ImageDraw.Draw(img)
    if "blu" in kind:
        draw.ellipse((220, 140, 580, 480), fill=(95, 108, 125))
        draw.polygon([(240, 180), (200, 70), (320, 145)], fill=(88, 100, 118))
        draw.polygon([(560, 180), (600, 70), (480, 145)], fill=(88, 100, 118))
        draw.ellipse((310, 250, 360, 300), fill=(72, 185, 120))
        draw.ellipse((440, 250, 490, 300), fill=(72, 185, 120))
    elif "marmalade" in kind:
        draw.ellipse((220, 140, 580, 480), fill=(218, 126, 48))
        draw.polygon([(240, 180), (200, 70), (320, 145)], fill=(205, 110, 38))
        draw.polygon([(560, 180), (600, 70), (480, 145)], fill=(205, 110, 38))
        draw.ellipse((310, 250, 360, 300), fill=(220, 190, 60))
        draw.ellipse((440, 250, 490, 300), fill=(220, 190, 60))
    elif "dog" in kind:
        draw.ellipse((200, 130, 600, 490), fill=(215, 175, 115))
    else:
        draw.rectangle((0, 0, 800, 320), fill=(110, 170, 235))
        draw.rectangle((0, 320, 800, 600), fill=(65, 145, 95))
    return img


def _save_with_exif(
    img: Image.Image,
    dest_path: Path,
    fmt: str,
    make: str,
    model: str,
    dt_str: str,
):
    """Saves an image with embedded EXIF Make, Model, and DateTimeOriginal tags."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    exif = Image.Exif()
    exif[0x010F] = make   # Make
    exif[0x0110] = model  # Model
    exif[0x0132] = dt_str # DateTime
    exif[0x9003] = dt_str # DateTimeOriginal
    if fmt == "JPEG":
        img.save(dest_path, "JPEG", quality=92, exif=exif.tobytes())
    elif fmt == "PNG":
        img.save(dest_path, "PNG", exif=exif.tobytes())
    elif fmt == "WEBP":
        img.save(dest_path, "WEBP", quality=90, exif=exif.tobytes())
    else:
        img.save(dest_path)


def ensure_sample_drive_photos(target_dir: Optional[str] = None) -> str:
    """
    Populates `sample_drive_photos/` organized into realistic subfolders with rich EXIF
    Device, Capture Time, and Image Type metadata to showcase all 3 Root Systems:
      1. Type:   Blu -> Cat -> Animal
      2. Drive:  Subfolder -> Folder -> Drive
      3. Device: EXIF Device + Time -> Image Type (JPEG / PNG / WEBP)
    """
    if target_dir is None:
        folder = Path(__file__).resolve().parent.parent / "sample_drive_photos"
    else:
        folder = Path(target_dir)

    expected_rel_paths = [
        Path("Cats_Blu") / "01_blu_sofa_portrait.jpg",
        Path("Cats_Blu") / "02_blu_afternoon_window.jpg",
        Path("Cats_Blu") / "03_blu_closeup_gaze.png",
        Path("Cats_Other") / "04_other_cat_ginger_tabby.jpg",
        Path("Cats_Other") / "05_other_cat_sunny_garden.webp",
        Path("Dogs") / "06_golden_retriever_park.jpg",
        Path("Nature_Scenery") / "07_alpine_mountain_lake.jpg",
        Path("Nature_Scenery") / "08_pacific_coastal_beach.jpg",
    ]
    if all((folder / rp).exists() for rp in expected_rel_paths):
        return str(folder.resolve())

    # Remove old flat files if upgrading structure
    if folder.exists():
        for item in folder.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                except Exception:
                    pass
    folder.mkdir(parents=True, exist_ok=True)

    # 1. Generate 3 distinct photographs of Blu (Russian Blue cat) in Subfolder `Cats_Blu`
    blu_base = _fetch_url_image(SAMPLE_URLS["blu_base"]) or _create_fallback_image("blu")
    w, h = blu_base.size

    _save_with_exif(
        blu_base,
        folder / "Cats_Blu" / "01_blu_sofa_portrait.jpg",
        fmt="JPEG",
        make="Apple",
        model="iPhone 16 Pro",
        dt_str="2026:10:20 14:15:30",
    )

    c2 = ImageOps.mirror(blu_base.crop((int(w * 0.07), int(h * 0.04), int(w * 0.93), int(h * 0.93))))
    blu_2 = ImageEnhance.Brightness(ImageEnhance.Color(c2).enhance(1.06)).enhance(1.05)
    _save_with_exif(
        blu_2,
        folder / "Cats_Blu" / "02_blu_afternoon_window.jpg",
        fmt="JPEG",
        make="Apple",
        model="iPhone 16 Pro",
        dt_str="2026:10:21 16:42:10",
    )

    c3 = blu_base.crop((int(w * 0.04), int(h * 0.09), int(w * 0.89), int(h * 0.96)))
    blu_3 = ImageEnhance.Contrast(c3).enhance(1.06)
    _save_with_exif(
        blu_3,
        folder / "Cats_Blu" / "03_blu_closeup_gaze.png",
        fmt="PNG",
        make="Sony",
        model="Alpha A7R V",
        dt_str="2026:10:22 11:08:05",
    )

    # 2. Generate 2 photographs of a completely different cat in Subfolder `Cats_Other`
    marm_1 = _fetch_url_image(SAMPLE_URLS["marmalade_1"]) or _create_fallback_image("marmalade")
    _save_with_exif(
        marm_1,
        folder / "Cats_Other" / "04_other_cat_ginger_tabby.jpg",
        fmt="JPEG",
        make="Fujifilm",
        model="X100VI",
        dt_str="2026:10:18 09:30:00",
    )

    marm_2 = _fetch_url_image(SAMPLE_URLS["marmalade_2"]) or _create_fallback_image("marmalade")
    _save_with_exif(
        marm_2,
        folder / "Cats_Other" / "05_other_cat_sunny_garden.webp",
        fmt="WEBP",
        make="Fujifilm",
        model="X100VI",
        dt_str="2026:10:19 15:12:44",
    )

    # 3. Generate dog & landscape photographs in `Dogs` & `Nature_Scenery`
    dog_1 = _fetch_url_image(SAMPLE_URLS["golden_dog_1"]) or _create_fallback_image("dog")
    _save_with_exif(
        dog_1,
        folder / "Dogs" / "06_golden_retriever_park.jpg",
        fmt="JPEG",
        make="Apple",
        model="iPhone 16 Pro",
        dt_str="2026:10:15 17:20:00",
    )

    lake = _fetch_url_image(SAMPLE_URLS["alpine_lake"]) or _create_fallback_image("landscape")
    _save_with_exif(
        lake,
        folder / "Nature_Scenery" / "07_alpine_mountain_lake.jpg",
        fmt="JPEG",
        make="Canon",
        model="EOS R5",
        dt_str="2026:09:14 07:45:12",
    )

    beach = _fetch_url_image(SAMPLE_URLS["coastal_beach"]) or _create_fallback_image("landscape")
    _save_with_exif(
        beach,
        folder / "Nature_Scenery" / "08_pacific_coastal_beach.jpg",
        fmt="JPEG",
        make="Canon",
        model="EOS R5",
        dt_str="2026:09:16 18:10:33",
    )

    return str(folder.resolve())


def _build_synthetic_template(theme: str, idx: int) -> Image.Image:
    """Creates a fast, distinct 360x270 synthetic photo template for 300-photo stress testing."""
    w, h = 360, 270
    shift = (idx * 7) % 35
    if theme == "Cats_Blu":
        img = Image.new("RGB", (w, h), (225 - shift // 2, 228 - shift // 2, 235))
        d = ImageDraw.Draw(img)
        d.ellipse((95, 55, 265, 225), fill=(90 + (idx % 12), 104 + (idx % 10), 122))
        d.polygon([(110, 80), (88, 25), (150, 62)], fill=(82, 95, 114))
        d.polygon([(250, 80), (272, 25), (210, 62)], fill=(82, 95, 114))
        d.ellipse((138, 112, 162, 136), fill=(70, 185, 118))
        d.ellipse((198, 112, 222, 136), fill=(70, 185, 118))
    elif theme == "Cats_Tabby":
        img = Image.new("RGB", (w, h), (235, 230 - shift // 2, 218))
        d = ImageDraw.Draw(img)
        d.ellipse((95, 55, 265, 225), fill=(218 - (idx % 15), 125 + (idx % 10), 46))
        d.polygon([(110, 80), (88, 25), (150, 62)], fill=(202, 108, 36))
        d.polygon([(250, 80), (272, 25), (210, 62)], fill=(202, 108, 36))
        d.ellipse((138, 112, 162, 136), fill=(215, 190, 55))
        d.ellipse((198, 112, 222, 136), fill=(215, 190, 55))
    elif theme == "Dogs_Park":
        img = Image.new("RGB", (w, h), (88, 162 - shift // 2, 92))
        d = ImageDraw.Draw(img)
        d.ellipse((90, 50, 270, 230), fill=(216 - (idx % 14), 174, 110 + (idx % 12)))
        d.ellipse((135, 108, 155, 128), fill=(45, 35, 30))
        d.ellipse((205, 108, 225, 128), fill=(45, 35, 30))
        d.ellipse((165, 142, 195, 166), fill=(35, 28, 25))
    elif theme == "Alpine_Mountains":
        img = Image.new("RGB", (w, h), (105 + shift, 168, 238))
        d = ImageDraw.Draw(img)
        d.polygon([(20, 185), (130, 48), (240, 185)], fill=(100, 112, 128))
        d.polygon([(130, 48), (102, 85), (158, 85)], fill=(245, 248, 252))
        d.polygon([(140, 185), (255, 62), (350, 185)], fill=(86, 98, 115))
        d.rectangle((0, 185, w, h), fill=(48, 128 + (idx % 20), 175))
    elif theme == "Sunset_Beach":
        img = Image.new("RGB", (w, h), (252, 122 + (idx % 25), 38))
        d = ImageDraw.Draw(img)
        d.ellipse((145, 72, 215, 142), fill=(255, 218, 95))
        d.rectangle((0, 150, w, 215), fill=(35, 135, 175))
        d.rectangle((0, 215, w, h), fill=(228, 202, 156))
    elif theme == "Forest_Nature":
        img = Image.new("RGB", (w, h), (42, 142 + (idx % 25), 55))
        d = ImageDraw.Draw(img)
        for tx in range(35, 330, 55):
            d.polygon([(tx, 35 + (idx % 15)), (tx - 28, 185), (tx + 28, 185)], fill=(28, 110, 42))
            d.rectangle((tx - 6, 185, tx + 6, 230), fill=(92, 62, 38))
    elif theme == "City_Architecture":
        img = Image.new("RGB", (w, h), (175, 195, 220))
        d = ImageDraw.Draw(img)
        d.rectangle((45, 55, 125, 240), fill=(115, 124, 138))
        d.rectangle((140, 35, 225, 240), fill=(92, 102, 118))
        d.rectangle((240, 75, 315, 240), fill=(128, 136, 148))
        d.rectangle((0, 240, w, h), fill=(70, 74, 80))
    else:
        # Monochrome / Street art
        val = 95 + (idx % 60)
        img = Image.new("RGB", (w, h), (val, val, val))
        d = ImageDraw.Draw(img)
        d.rectangle((50, 45, 310, 225), outline=(225, 225, 225), width=3)
        d.ellipse((130, 85, 230, 185), fill=(val - 35, val - 35, val - 35))

    # Subtle unique pixel watermark in corner so every single image has a unique SHA256 file_hash
    d = ImageDraw.Draw(img)
    d.rectangle((w - 18, h - 12, w - 2, h - 2), fill=((idx * 37) % 255, (idx * 73) % 255, (idx * 19) % 255))
    return img


def generate_300_placeholder_photos(
    target_dir: Optional[str] = None, total_count: int = 300
) -> str:
    """
    Rapidly generates exactly 300 diverse placeholder images on disk across multiple folders,
    camera devices, dates, and visual themes for stress-testing scan speed (img/sec) and UI scale.
    """
    from concurrent.futures import ThreadPoolExecutor

    if target_dir is None:
        folder = Path(__file__).resolve().parent.parent / "placeholder_300_photos"
    else:
        folder = Path(target_dir)

    folder.mkdir(parents=True, exist_ok=True)

    # Check if we already have exactly total_count valid images in this folder
    existing_imgs = [
        p
        for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    ]
    if len(existing_imgs) == total_count:
        return str(folder.resolve())

    # Clean up any partial/old files so count is strictly total_count (300)
    for p in folder.rglob("*"):
        if p.is_file():
            try:
                p.unlink()
            except Exception:
                pass

    themes = [
        ("Cats_Blu", "blu_cat", "Apple", "iPhone 16 Pro"),
        ("Cats_Tabby", "ginger_tabby", "Fujifilm", "X100VI"),
        ("Dogs_Park", "golden_dog", "Apple", "iPhone 16 Pro"),
        ("Alpine_Mountains", "mountain_lake", "Canon", "EOS R5"),
        ("Sunset_Beach", "sunset_coast", "Sony", "Alpha A7R V"),
        ("Forest_Nature", "woodland_trees", "Nikon", "Z8"),
        ("City_Architecture", "urban_skyline", "Sony", "Alpha A7R V"),
        ("Monochrome_Street", "bw_street", "Leica", "Q3"),
    ]

    # Try to load existing sample photos as base templates for realistic textures when available
    sample_root = Path(__file__).resolve().parent.parent / "sample_drive_photos"
    real_bases = {}
    base_candidates = {
        "Cats_Blu": sample_root / "Cats_Blu" / "01_blu_sofa_portrait.jpg",
        "Cats_Tabby": sample_root / "Cats_Other" / "04_other_cat_ginger_tabby.jpg",
        "Dogs_Park": sample_root / "Dogs" / "06_golden_retriever_park.jpg",
        "Alpine_Mountains": sample_root / "Nature_Scenery" / "07_alpine_mountain_lake.jpg",
        "Sunset_Beach": sample_root / "Nature_Scenery" / "08_pacific_coastal_beach.jpg",
    }
    for k, p in base_candidates.items():
        if p.exists():
            try:
                with Image.open(p) as im:
                    real_bases[k] = im.convert("RGB").resize((360, 270), Image.Resampling.BILINEAR)
            except Exception:
                pass

    def _create_one(i: int):
        idx_1 = i + 1
        subfolder, prefix, make, model = themes[i % len(themes)]
        month = 1 + (i % 10)
        day = 1 + (i % 28)
        hour = 8 + (i % 12)
        minute = i % 60
        dt_str = f"2026:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:15"

        if subfolder in real_bases and (i % 2 == 0):
            base_im = real_bases[subfolder].copy()
            # Apply slight crop/color variation + unique corner marker so hash is unique
            dx = (i % 5) * 4
            dy = (i % 4) * 3
            if dx > 0 or dy > 0:
                w, h = base_im.size
                base_im = base_im.crop((dx, dy, w - dx, h - dy)).resize(
                    (360, 270), Image.Resampling.BILINEAR
                )
            d = ImageDraw.Draw(base_im)
            d.rectangle(
                (342, 258, 358, 268),
                fill=((idx_1 * 41) % 255, (idx_1 * 83) % 255, (idx_1 * 29) % 255),
            )
            img = base_im
        else:
            img = _build_synthetic_template(subfolder, idx_1)

        dest = folder / subfolder / f"{idx_1:03d}_{prefix}_{idx_1:03d}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        exif = Image.Exif()
        exif[0x010F] = make
        exif[0x0110] = model
        exif[0x0132] = dt_str
        exif[0x9003] = dt_str
        img.save(dest, "JPEG", quality=82, exif=exif.tobytes())

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_create_one, range(total_count)))

    return str(folder.resolve())
