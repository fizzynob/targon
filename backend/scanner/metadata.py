import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
from PIL import Image, ExifTags, ImageOps


IMAGE_TYPE_LABELS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
    ".gif": "GIF",
    ".heic": "HEIC",
}


def compute_fast_file_hash(file_path: str) -> str:
    """Computes a fast hash of the file (size + first 64KB + last 64KB)."""
    p = Path(file_path)
    stat = p.stat()
    size = stat.st_size
    h = hashlib.sha256()
    h.update(str(size).encode("utf-8"))
    with open(p, "rb") as f:
        h.update(f.read(65536))
        if size > 131072:
            f.seek(size - 65536)
            h.update(f.read(65536))
    return h.hexdigest()[:32]


def extract_dominant_hex_color(img: Image.Image) -> str:
    """Computes a pleasant dominant hex color for image placeholders."""
    try:
        small = img.convert("RGB").resize((16, 16), Image.Resampling.BILINEAR)
        arr = np.array(small)
        r = int(np.mean(arr[:, :, 0]))
        g = int(np.mean(arr[:, :, 1]))
        b = int(np.mean(arr[:, :, 2]))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#E5E5EA"


def _format_rational(val: Any) -> Optional[str]:
    if val is None:
        return None
    try:
        if hasattr(val, "numerator") and hasattr(val, "denominator"):
            if val.denominator == 0:
                return None
            return str(round(float(val.numerator) / float(val.denominator), 2))
        if isinstance(val, tuple) and len(val) == 2 and val[1] != 0:
            return str(round(float(val[0]) / float(val[1]), 2))
        return str(val)
    except Exception:
        return str(val)


def parse_drive_hierarchy(file_path: str, scanned_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses a file path into the Drive Root System:
      Subfolder -> Folder -> Drive
    Returns:
      {
        "drive_root": e.g. "C:",
        "folder_name": e.g. "sample_drive_photos" or parent folder,
        "subfolder_name": e.g. "Cats_Blu" or immediate subfolder,
        "bottom_up_chain": ["Cats_Blu", "sample_drive_photos", "C:"],
        "top_down_chain": ["C:", "sample_drive_photos", "Cats_Blu"]
      }
    """
    p = Path(file_path).resolve()
    drive = p.drive.rstrip("\\/") if p.drive else "Local Drive"
    parent_parts = list(p.parent.parts)
    # Remove the drive anchor from parts
    if p.anchor and parent_parts and parent_parts[0] == p.anchor:
        dir_parts = parent_parts[1:]
    else:
        dir_parts = [pt for pt in parent_parts if pt not in ("/", "\\")]

    if scanned_root:
        try:
            root_p = Path(scanned_root).resolve()
            rel_parent = p.parent.relative_to(root_p)
            rel_parts = [pt for pt in rel_parent.parts if pt not in (".", "")]
            folder_name = root_p.name or drive
            if len(rel_parts) >= 1:
                subfolder_name = "/".join(rel_parts)
            else:
                subfolder_name = "Root"
            return {
                "drive_root": drive,
                "folder_name": folder_name,
                "subfolder_name": subfolder_name,
                "bottom_up_chain": [subfolder_name, folder_name, drive],
                "top_down_chain": [drive, folder_name, subfolder_name],
            }
        except Exception:
            pass

    if len(dir_parts) >= 2:
        subfolder_name = dir_parts[-1]
        folder_name = dir_parts[-2]
    elif len(dir_parts) == 1:
        subfolder_name = "Root"
        folder_name = dir_parts[0]
    else:
        subfolder_name = "Root"
        folder_name = "Root"

    return {
        "drive_root": drive,
        "folder_name": folder_name,
        "subfolder_name": subfolder_name,
        "bottom_up_chain": [subfolder_name, folder_name, drive],
        "top_down_chain": [drive, folder_name, subfolder_name],
    }


GAME_DIR_KEYWORDS = {
    "game", "games", "steam", "steamapps", "steamrip", "advantagesimages", "assets",
    "textures", "sprites", "icons", "mods", "unity", "unreal", "rpgmaker", "emulators",
    "roms", "gog games", "epic games", "riot games", "blizzard", "ubisoft", "origin",
    "ea games", "minecraft", "roblox", "genshin", "hoyoverse"
}


def detect_is_game_asset(file_path: str, width: int = 0, height: int = 0) -> bool:
    """Detects whether an image is a video game asset, sprite, icon, or texture from path/dimensions."""
    p_lower = file_path.lower().replace("/", "\\")
    parts = [pt.lower() for pt in Path(file_path).parts]
    for part in parts[:-1]:
        for kw in GAME_DIR_KEYWORDS:
            if kw in part:
                return True
    if 0 < width <= 256 and 0 < height <= 256:
        for kw in ("advantages", "icons", "sprites", "textures", "hud", "ui", "character", "items"):
            if kw in p_lower:
                return True
    return False


def extract_image_metadata(
    file_path: str,
    scanned_root: Optional[str] = None,
    return_image: bool = False,
):
    """
    Extracts dimensions, EXIF data (Device Make/Model, Time Taken), Image Type,
    and Drive / Folder / Subfolder hierarchy.
    If return_image=True, returns (meta, loaded_rgb_pil_img) so callers don't re-decode from disk.
    """
    p = Path(file_path).resolve()
    stat = p.stat()
    ext = p.suffix.lower()
    image_type = IMAGE_TYPE_LABELS.get(ext, ext.lstrip(".").upper() or "IMAGE")
    drive_info = parse_drive_hierarchy(str(p), scanned_root=scanned_root)

    meta: Dict[str, Any] = {
        "path": str(p),
        "filename": p.name,
        "file_size": stat.st_size,
        "file_hash": compute_fast_file_hash(str(p)),
        "width": 0,
        "height": 0,
        "image_type": image_type,
        "drive_root": drive_info["drive_root"],
        "folder_name": drive_info["folder_name"],
        "subfolder_name": drive_info["subfolder_name"],
        "date_taken": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "camera_make": None,
        "camera_model": None,
        "device_name": "Unknown Device",
        "iso": None,
        "focal_length": None,
        "aperture": None,
        "shutter_speed": None,
        "dominant_color": "#E5E5EA",
        "is_game_asset": 0,
    }

    loaded_rgb: Optional[Image.Image] = None
    try:
        with Image.open(p) as raw_img:
            if raw_img.format:
                meta["image_type"] = raw_img.format.upper()

            exif_data = raw_img.getexif()
            if exif_data:
                exif_map = {}
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_map[tag_name] = value

                try:
                    ifd = exif_data.get_ifd(0x8769)
                    for tag_id, value in ifd.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_map[tag_name] = value
                except Exception:
                    pass

                if "Make" in exif_map and exif_map["Make"]:
                    meta["camera_make"] = str(exif_map["Make"]).strip("\x00 ")
                if "Model" in exif_map and exif_map["Model"]:
                    meta["camera_model"] = str(exif_map["Model"]).strip("\x00 ")

                make = meta["camera_make"] or ""
                model = meta["camera_model"] or ""
                if make and model:
                    if model.lower().startswith(make.lower()):
                        meta["device_name"] = model
                    else:
                        meta["device_name"] = f"{make} {model}"
                elif model:
                    meta["device_name"] = model
                elif make:
                    meta["device_name"] = make

                if "ISOSpeedRatings" in exif_map:
                    meta["iso"] = f"ISO {exif_map['ISOSpeedRatings']}"
                if "FocalLength" in exif_map:
                    fl = _format_rational(exif_map["FocalLength"])
                    if fl:
                        meta["focal_length"] = f"{fl}mm"
                if "FNumber" in exif_map:
                    fn = _format_rational(exif_map["FNumber"])
                    if fn:
                        meta["aperture"] = f"ƒ/{fn}"
                if "ExposureTime" in exif_map:
                    et = exif_map["ExposureTime"]
                    try:
                        val_f = float(et)
                        if 0 < val_f < 1:
                            denom = int(round(1.0 / val_f))
                            meta["shutter_speed"] = f"1/{denom}s"
                        else:
                            meta["shutter_speed"] = f"{val_f}s"
                    except Exception:
                        pass

                for dt_key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                    if dt_key in exif_map and exif_map[dt_key]:
                        raw_dt = str(exif_map[dt_key]).strip("\x00 ")
                        try:
                            parsed = datetime.strptime(raw_dt[:19], "%Y:%m:%d %H:%M:%S")
                            meta["date_taken"] = parsed.strftime("%Y-%m-%d %H:%M:%S")
                            break
                        except Exception:
                            pass

            img = ImageOps.exif_transpose(raw_img)
            meta["width"], meta["height"] = img.size
            meta["is_game_asset"] = 1 if detect_is_game_asset(str(p), meta["width"], meta["height"]) else 0

            if return_image:
                loaded_rgb = img.convert("RGB")
                meta["dominant_color"] = extract_dominant_hex_color(loaded_rgb)
            else:
                meta["dominant_color"] = extract_dominant_hex_color(img)
    except Exception:
        pass

    if return_image:
        return meta, loaded_rgb
    return meta
