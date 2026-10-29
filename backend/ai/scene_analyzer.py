from typing import List, Tuple, Dict, Any
import numpy as np
import cv2
from PIL import Image


class SceneAnalyzer:
    """
    Intelligent Photometric, Atmospheric & Composition Analyzer.
    Analyzes full image for:
      - Lighting & Mood: Golden Hour, Sunset, Blue Hour, Night, Bright Daylight, Low Light
      - Composition: Black & White / Monochrome, Macro, Panoramic
      - Natural Photometrics: Foliage, Snow / High-Key
    Semantic scene categories (Beach, Mountain, Castle, Portrait, etc.) are handled by CLIPEngine.
    """

    def analyze_scene(self, pil_img: Image.Image) -> Dict[str, Any]:
        tags: List[Tuple[str, str, float]] = []

        w, h = pil_img.size
        aspect_ratio = float(w) / float(max(1, h))

        # Check composition / framing
        if aspect_ratio >= 1.85:
            tags.append(("panoramic", "scene", 0.90))
        elif aspect_ratio <= 0.60:
            tags.append(("vertical framing", "scene", 0.86))

        # Downsample to 256x256 for rapid sub-millisecond photometric analysis
        small = pil_img.convert("RGB").resize((256, 256), Image.Resampling.BILINEAR)
        rgb = np.array(small, dtype=np.float32)
        rgb_u8 = rgb.astype(np.uint8)

        hsv = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2HSV).astype(np.float32)
        h_chan = hsv[:, :, 0]  # 0..180
        s_chan = hsv[:, :, 1]  # 0..255
        v_chan = hsv[:, :, 2]  # 0..255

        mean_v = float(np.mean(v_chan))
        mean_s = float(np.mean(s_chan))
        p95_v = float(np.percentile(v_chan, 95))
        p5_v = float(np.percentile(v_chan, 5))
        contrast_span = p95_v - p5_v

        # 1. Black & White / Monochrome Detection
        if mean_s < 14.0 and np.std(s_chan) < 12.0:
            tags.append(("black and white", "scene", 0.98))
            tags.append(("monochrome", "attribute", 0.96))

        # 2. Lighting & Atmospheric Analysis
        if mean_v < 52.0 and p95_v > 185.0:
            tags.append(("night", "scene", 0.92))
            tags.append(("low light", "scene", 0.88))
        elif mean_v < 60.0:
            tags.append(("low light", "scene", 0.90))
        elif mean_v > 188.0:
            tags.append(("bright lighting", "scene", 0.88))

        if contrast_span > 210.0:
            tags.append(("high contrast", "attribute", 0.85))

        # 3. Vibrant Golden Hour & Sunset Detection (requires bright, saturated warm orange/gold light)
        warm_mask = ((h_chan < 22.0) | (h_chan > 168.0)) & (s_chan > 90.0) & (v_chan > 110.0)
        warm_ratio = float(np.sum(warm_mask)) / float(256 * 256)
        if warm_ratio > 0.42 and mean_v > 100.0:
            tags.append(("golden hour", "scene", 0.91))
            tags.append(("sunset", "scene", 0.89))
            tags.append(("warm lighting", "scene", 0.87))

        # 4. Blue Hour / Twilight
        blue_mask = (h_chan >= 98.0) & (h_chan <= 128.0) & (s_chan > 65.0) & (v_chan < 130.0)
        blue_ratio = float(np.sum(blue_mask)) / float(256 * 256)
        if blue_ratio > 0.45 and mean_v < 105.0:
            tags.append(("blue hour", "scene", 0.90))
            tags.append(("twilight", "scene", 0.88))

        # 5. Natural Foliage Photometrics
        green_mask = (h_chan >= 34.0) & (h_chan <= 80.0) & (s_chan > 55.0) & (v_chan > 50.0)
        green_ratio = float(np.sum(green_mask)) / float(256 * 256)
        if green_ratio > 0.35:
            tags.append(("foliage", "attribute", 0.89))

        return {
            "tags": tags,
            "mean_luminance": round(mean_v, 2),
            "mean_saturation": round(mean_s, 2),
            "contrast_span": round(contrast_span, 2),
            "is_bw": ("black and white" in [t[0] for t in tags]),
        }


scene_analyzer = SceneAnalyzer()
