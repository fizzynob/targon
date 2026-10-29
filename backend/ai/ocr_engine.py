import asyncio
import io
import re
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image

try:
    import winrt.windows.media.ocr as win_ocr
    import winrt.windows.graphics.imaging as imaging
    import winrt.windows.storage.streams as streams
    WIN_OCR_AVAILABLE = True
except Exception:
    WIN_OCR_AVAILABLE = False


COMMON_STOPWORDS = {
    "the", "and", "that", "have", "for", "not", "with", "you", "this", "but", "his", "from",
    "they", "say", "her", "she", "will", "one", "all", "would", "there", "their", "what",
    "out", "about", "who", "get", "which", "when", "make", "can", "like", "time", "just",
    "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them",
    "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"
}


class OCREngine:
    """
    Apple Photos-style 'Live Text' Recognition Engine.
    Uses native Windows 10/11 WinRT OCR engine for local text extraction.
    Detects:
      - Printed text, street signs, book covers, labels, receipts, slides, memes
      - Searchable text keywords and document tags
    """

    def __init__(self):
        self._engine = None
        if WIN_OCR_AVAILABLE:
            try:
                self._engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            except Exception:
                self._engine = None

    @property
    def is_available(self) -> bool:
        return self._engine is not None

    def has_likely_text(self, pil_img: Image.Image) -> bool:
        """
        Ultra-fast (<0.3ms) pre-check to see if an image contains sharp high-contrast
        character-like horizontal edge transitions (such as printed text, signs, UI, or receipts).
        Avoids invoking the heavy WinRT OCR pipeline on smooth natural scenes.
        """
        try:
            import numpy as np
            small = pil_img.convert("L").resize((240, 160), Image.Resampling.NEAREST)
            arr = np.array(small, dtype=np.int16)
            dx = np.abs(arr[:, 1:] - arr[:, :-1])
            # Text produces concentrated sharp horizontal transitions (>75 luminance jump)
            sharp_transitions = int(np.sum(dx > 75))
            if sharp_transitions < 35:
                return False
            # Check if there is at least one row band with repeated character-like oscillations
            row_counts = np.sum(dx > 75, axis=1)
            return bool(np.max(row_counts) >= 6)
        except Exception:
            return True

    def extract_text(self, pil_img: Image.Image, fast_gate: bool = True) -> Dict[str, Any]:
        """
        Extracts visible text and generates semantic search tags.
        Returns:
          {
            "has_text": bool,
            "text": str,
            "word_count": int,
            "tags": [(tag_name, tag_type, confidence)]
          }
        """
        if not self.is_available:
            return {"has_text": False, "text": "", "word_count": 0, "tags": []}

        if fast_gate and not self.has_likely_text(pil_img):
            return {"has_text": False, "text": "", "word_count": 0, "tags": []}

        try:
            # Resize image to reasonable size for ultra-fast OCR (max 860px dimension)
            w, h = pil_img.size
            scale = min(1.0, 860.0 / max(w, h))
            if scale < 1.0:
                target_w, target_h = max(16, int(w * scale)), max(16, int(h * scale))
                proc_img = pil_img.convert("RGB").resize((target_w, target_h), Image.Resampling.BILINEAR)
            else:
                proc_img = pil_img.convert("RGB")

            raw_text = self._run_winrt_ocr_sync(proc_img)
            clean_text = " ".join(raw_text.split()).strip()

            if not clean_text or len(clean_text) < 3:
                return {"has_text": False, "text": "", "word_count": 0, "tags": []}

            words = [w.lower() for w in re.findall(r"\b[A-Za-z]{3,}\b", clean_text)]
            unique_words = [w for w in set(words) if w not in COMMON_STOPWORDS]

            tags: List[Tuple[str, str, float]] = []
            tags.append(("text", "attribute", 0.95))

            # Detect document / receipt / menu cues
            text_lower = clean_text.lower()
            if any(k in text_lower for k in ("receipt", "subtotal", "total", "tax", "cashier", "amount")):
                tags.append(("receipt", "category", 0.95))
                tags.append(("document", "category", 0.92))
            elif any(k in text_lower for k in ("menu", "appetizer", "dessert", "beverage", "price")):
                tags.append(("menu", "category", 0.93))
                tags.append(("dining", "scene", 0.90))
            elif any(k in text_lower for k in ("invoice", "bill", "due date", "statement")):
                tags.append(("invoice", "category", 0.95))
                tags.append(("document", "category", 0.93))
            elif len(words) > 15:
                tags.append(("document", "category", 0.90))

            # Add up to 4 most significant distinct keywords as searchable attributes
            for w in unique_words[:4]:
                if len(w) >= 4:
                    tags.append((w, "attribute", 0.88))

            return {
                "has_text": True,
                "text": clean_text[:1000],  # Cap at 1000 chars
                "word_count": len(words),
                "tags": tags,
            }
        except Exception:
            return {"has_text": False, "text": "", "word_count": 0, "tags": []}

    def _run_winrt_ocr_sync(self, pil_img: Image.Image) -> str:
        async def _async_recognize():
            buf = io.BytesIO()
            pil_img.save(buf, format="BMP")
            raw_bytes = buf.getvalue()

            writer = streams.DataWriter()
            writer.write_bytes(bytearray(raw_bytes))
            ibuffer = writer.detach_buffer()

            mem_stream = streams.InMemoryRandomAccessStream()
            await mem_stream.write_async(ibuffer)
            mem_stream.seek(0)

            decoder = await imaging.BitmapDecoder.create_async(mem_stream)
            software_bitmap = await decoder.get_software_bitmap_async()

            result = await self._engine.recognize_async(software_bitmap)
            return (result.text or "").strip()

        try:
            return asyncio.run(_async_recognize())
        except Exception:
            return ""


ocr_engine = OCREngine()
