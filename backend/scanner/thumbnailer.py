from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image, ImageOps


class Thumbnailer:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            base = Path(__file__).resolve().parent.parent.parent / ".targon_cache"
        else:
            base = Path(cache_dir)
        self.thumbs_dir = base / "thumbnails"
        self.previews_dir = base / "previews"
        self.crops_dir = base / "crops"
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)
        self.crops_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnails(
        self,
        image_path: str,
        file_hash: str,
        pil_img: Optional[Image.Image] = None,
        quality_mode: str = "balanced",
    ) -> Tuple[str, str]:
        """Generates a grid thumbnail and preview in WebP format without re-decoding if pil_img is provided."""
        thumb_path = self.thumbs_dir / f"{file_hash}_thumb.webp"
        preview_path = self.previews_dir / f"{file_hash}_preview.webp"

        if thumb_path.exists() and preview_path.exists():
            return str(thumb_path), str(preview_path)

        def _make_from_rgb(img: Image.Image) -> Tuple[str, str]:
            w, h = img.size
            if quality_mode == "fast":
                resample = Image.Resampling.BILINEAR
                thumb_dim = 360
                thumb_q = 74
                # In fast mode, if image is <= 1280px, reuse original/thumb to avoid double WebP encode
                if not thumb_path.exists():
                    th_img = img.copy()
                    th_img.thumbnail((thumb_dim, thumb_dim), resample)
                    th_img.save(thumb_path, "WEBP", quality=thumb_q, method=0)
                if not preview_path.exists():
                    if max(w, h) <= 1080:
                        return str(thumb_path), str(image_path)
                    prev_img = img.copy()
                    prev_img.thumbnail((960, 960), resample)
                    prev_img.save(preview_path, "WEBP", quality=78, method=0)
                return str(thumb_path), str(preview_path)

            resample = (
                Image.Resampling.LANCZOS
                if quality_mode == "high"
                else Image.Resampling.BILINEAR
            )
            prev_q = 88 if quality_mode == "high" else 82
            thumb_q = 85 if quality_mode == "high" else 78

            # Generate preview (max 1280px)
            if not preview_path.exists():
                if max(w, h) <= 960 and quality_mode != "high":
                    # Small source image: avoid writing redundant large preview file
                    pass
                else:
                    prev_img = img.copy()
                    prev_img.thumbnail((1280, 1280), resample)
                    prev_img.save(preview_path, "WEBP", quality=prev_q, method=0)

            # Generate grid thumbnail (max 480px)
            if not thumb_path.exists():
                th_img = img.copy()
                th_img.thumbnail((480, 480), resample)
                th_img.save(thumb_path, "WEBP", quality=thumb_q, method=0)

            final_preview = str(preview_path) if preview_path.exists() else str(thumb_path)
            return str(thumb_path), final_preview

        if pil_img is not None:
            rgb_img = pil_img if pil_img.mode == "RGB" else pil_img.convert("RGB")
            return _make_from_rgb(rgb_img)

        with Image.open(image_path) as raw_img:
            img = ImageOps.exif_transpose(raw_img).convert("RGB")
            return _make_from_rgb(img)

    def save_subject_crop(
        self,
        image_path: str,
        file_hash: str,
        bbox: List[float],
        idx: int = 0,
        pil_img: Optional[Image.Image] = None,
    ) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        Crops the detected subject [ymin, xmin, ymax, xmax] (normalized 0..1)
        with a comfortable margin for a nice circular Apple Photos avatar.
        Returns (cropped PIL Image for embedding, saved avatar crop path).
        """
        crop_path = self.crops_dir / f"{file_hash}_subj_{idx}.webp"
        try:
            def _crop_from_rgb(img: Image.Image) -> Tuple[Image.Image, str]:
                w, h = img.size
                ymin, xmin, ymax, xmax = bbox

                # Tight crop for feature embedding
                x1 = max(0, int(xmin * w))
                y1 = max(0, int(ymin * h))
                x2 = min(w, int(xmax * w))
                y2 = min(h, int(ymax * h))

                if x2 - x1 < 16 or y2 - y1 < 16:
                    tight_crop = img
                else:
                    tight_crop = img.crop((x1, y1, x2, y2))

                if not crop_path.exists():
                    # Square padded crop for avatar thumbnail
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    side = max(x2 - x1, y2 - y1) * 1.15
                    half = side / 2.0
                    ax1 = max(0, int(cx - half))
                    ay1 = max(0, int(cy - half))
                    ax2 = min(w, int(cx + half))
                    ay2 = min(h, int(cy + half))
                    avatar_crop = img.crop((ax1, ay1, ax2, ay2))
                    avatar_crop = ImageOps.fit(
                        avatar_crop, (256, 256), Image.Resampling.BILINEAR
                    )
                    avatar_crop.save(crop_path, "WEBP", quality=82, method=0)

                return tight_crop, str(crop_path)

            if pil_img is not None:
                rgb_img = pil_img if pil_img.mode == "RGB" else pil_img.convert("RGB")
                return _crop_from_rgb(rgb_img)

            with Image.open(image_path) as raw_img:
                img = ImageOps.exif_transpose(raw_img).convert("RGB")
                return _crop_from_rgb(img)
        except Exception:
            return None, None
