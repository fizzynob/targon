from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image

from backend.ai.face_engine import face_engine


class SubjectDetector:
    """
    Locates salient foreground subjects, human faces, and pet faces.
    Returns normalized bounding boxes [ymin, xmin, ymax, xmax] in [0.0, 1.0].
    """

    def __init__(self):
        yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
        self._center_prior = 0.4 + 0.6 * np.exp(
            -(((xx - 128.0) ** 2 + (yy - 128.0) ** 2) / (2 * (95.0**2)))
        )
        self._morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))

    def detect_all_subjects_and_faces(
        self, pil_img: Image.Image, enable_faces: bool = True
    ) -> Tuple[List[float], float, List[Dict[str, Any]]]:
        """
        Detects primary subject and any specific human/pet faces in the image.
        Returns:
          - primary_bbox: [ymin, xmin, ymax, xmax]
          - salience_score: float (0.0 to 1.0)
          - detected_faces: list of dicts with individual face boxes and confidences
        """
        detected_faces = face_engine.detect_all_faces(pil_img) if enable_faces else []

        if detected_faces:
            # If prominent faces are found, prioritize the largest face as the primary subject
            top_face = detected_faces[0]
            ymin, xmin, ymax, xmax = top_face["bbox"]
            conf = float(top_face["confidence"])

            # Expand slightly downwards to include shoulders / body for a pleasing portrait crop
            box_h = ymax - ymin
            expanded_ymax = min(1.0, ymax + box_h * 0.35)
            primary_bbox = [ymin, xmin, expanded_ymax, xmax]
            return primary_bbox, conf, detected_faces

        # No faces found: Fall back to saliency & color-contrast segmentation without re-running face detection
        saliency_bbox, score = self.detect_primary_subject_bbox(pil_img, check_faces=False)
        return saliency_bbox, score, []

    def detect_primary_subject_bbox(
        self, pil_img: Image.Image, check_faces: bool = True
    ) -> Tuple[List[float], float]:
        """
        Computes a tight bounding box around the primary foreground subject using
        border-color background modeling + gradient saliency map + morphological closing.
        Returns ([ymin, xmin, ymax, xmax], salience_score).
        """
        try:
            if check_faces:
                faces = face_engine.detect_all_faces(pil_img)
                if faces:
                    top_face = faces[0]
                    ymin, xmin, ymax, xmax = top_face["bbox"]
                    box_h = ymax - ymin
                    expanded_ymax = min(1.0, ymax + box_h * 0.35)
                    return [ymin, xmin, expanded_ymax, xmax], float(top_face["confidence"])

            w, h = pil_img.size
            if h < 32 or w < 32:
                return [0.1, 0.1, 0.9, 0.9], 0.5

            # Resize directly in PIL to 256x256 for ultra-fast saliency analysis
            small_pil = pil_img.convert("RGB").resize((256, 256), Image.Resampling.BILINEAR)
            small = np.array(small_pil)
            lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)

            # Estimate background distribution from outer border strips
            border_pixels = np.concatenate(
                [
                    lab[:12, :, :].reshape(-1, 3),
                    lab[-12:, :, :].reshape(-1, 3),
                    lab[:, :12, :].reshape(-1, 3),
                    lab[:, -12:, :].reshape(-1, 3),
                ],
                axis=0,
            )
            bg_mean = np.median(border_pixels, axis=0)

            # Color contrast map vs border background
            color_dist = np.linalg.norm(lab - bg_mean, axis=2)
            color_dist = cv2.GaussianBlur(color_dist, (9, 9), 0)
            if color_dist.max() > 1e-5:
                color_dist = color_dist / color_dist.max()

            # Edge / texture density map (pets/faces have rich fur/eye/whisker gradients)
            gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            grad = np.sqrt(gx * gx + gy * gy)
            grad = cv2.GaussianBlur(grad, (15, 15), 0)
            if grad.max() > 1e-5:
                grad = grad / grad.max()

            saliency = (0.55 * color_dist + 0.45 * grad) * self._center_prior
            if saliency.max() > 1e-5:
                saliency = saliency / saliency.max()

            # Threshold to find primary subject mask
            thresh_val = max(0.38, float(np.percentile(saliency, 72)))
            mask = (saliency >= thresh_val).astype(np.uint8) * 255

            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._morph_kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._morph_kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return [0.12, 0.12, 0.88, 0.88], 0.6

            # Pick contour with highest integrated saliency * area
            best_box = None
            best_score = -1.0
            for c in contours:
                x, y, cw, ch = cv2.boundingRect(c)
                area_frac = (cw * ch) / float(256 * 256)
                if area_frac < 0.03:
                    continue
                roi_sal = float(np.mean(saliency[y : y + ch, x : x + cw]))
                score = roi_sal * (area_frac**0.35)
                if score > best_score:
                    best_score = score
                    best_box = (x, y, cw, ch)

            if best_box is None:
                return [0.12, 0.12, 0.88, 0.88], 0.65

            x, y, cw, ch = best_box
            # Add a slight 6% padding so ears/whiskers are never clipped
            pad_x = int(cw * 0.06)
            pad_y = int(ch * 0.06)
            xmin = max(0.02, (x - pad_x) / 256.0)
            ymin = max(0.02, (y - pad_y) / 256.0)
            xmax = min(0.98, (x + cw + pad_x) / 256.0)
            ymax = min(0.98, (y + ch + pad_y) / 256.0)

            return [round(ymin, 4), round(xmin, 4), round(ymax, 4), round(xmax, 4)], round(
                float(best_score), 3
            )
        except Exception:
            return [0.1, 0.1, 0.9, 0.9], 0.5
