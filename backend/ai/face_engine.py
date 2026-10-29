import os
import threading
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image


class FaceEngine:
    """
    Face Detection and Facial Feature Embedding Engine.
    Detects:
      1. Human faces using OpenCV YuNet ONNX (FaceDetectorYN).
      2. Pet / Cat faces using OpenCV Haar Cat Face Cascade with strict thresholds.
    Extracts:
      - Normalized bounding boxes [ymin, xmin, ymax, xmax].
      - 256-dimensional Perceptual Facial Identity Vector for person re-identification.
    """

    def __init__(self):
        ai_dir = os.path.dirname(os.path.abspath(__file__))
        self.yunet_path = os.path.join(ai_dir, "face_detection_yunet.onnx")
        self.cat_haar_path = os.path.join(ai_dir, "haarcascade_frontalcatface.xml")

        self.yunet = None
        self.cat_cascade = None
        self._lock = threading.Lock()

        self._init_models()

    def _init_models(self):
        # 1. Initialize YuNet Face Detector (high precision, low false positive deep model)
        if os.path.exists(self.yunet_path) and os.path.getsize(self.yunet_path) > 1000:
            try:
                self.yunet = cv2.FaceDetectorYN.create(
                    model=self.yunet_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.68,
                    nms_threshold=0.30,
                    top_k=20,
                )
            except Exception:
                self.yunet = None

        # 2. Pet/Cat face Haar cascade with strict validation
        if os.path.exists(self.cat_haar_path) and os.path.getsize(self.cat_haar_path) > 1000:
            try:
                self.cat_cascade = cv2.CascadeClassifier(self.cat_haar_path)
            except Exception:
                self.cat_cascade = None

    def detect_all_faces(self, pil_img: Image.Image) -> List[Dict[str, Any]]:
        """
        Detects all human and pet faces in the given image.
        Returns a list of dicts:
        [
          {
            "bbox": [ymin, xmin, ymax, xmax],
            "confidence": 0.95,
            "face_type": "human_face" | "pet_face",
            "is_portrait": bool,
          }
        ]
        """
        rgb = np.array(pil_img.convert("RGB"))
        h, w, _ = rgb.shape
        if h < 48 or w < 48:
            return []

        results = []

        # 1. Detect human faces with YuNet (including low-light CLAHE fallback if needed)
        if self.yunet is not None:
            try:
                target_max = float(np.clip(max(h, w), 320, 512))
                scale = target_max / float(max(h, w))
                new_w, new_h = max(32, int(w * scale)), max(32, int(h * scale))
                small_bgr = cv2.resize(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), (new_w, new_h))
                with self._lock:
                    self.yunet.setInputSize((new_w, new_h))
                    _, faces = self.yunet.detect(small_bgr)

                    # If no faces found and image is very dark, try CLAHE + gamma brightened pass
                    if (faces is None or len(faces) == 0) and float(np.mean(rgb)) < 60.0:
                        lab = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2LAB)
                        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
                        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                        enh_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                        enh_bgr = np.clip((enh_bgr / 255.0) ** 0.55 * 255.0, 0, 255).astype(np.uint8)
                        _, faces = self.yunet.detect(enh_bgr)

                if faces is not None and len(faces) > 0:
                    for f in faces:
                        fx, fy, fw, fh = f[0], f[1], f[2], f[3]
                        conf = float(f[14])
                        # Filter tiny or low-confidence artifacts
                        if conf < 0.68 or fw < 24 or fh < 24:
                            continue

                        orig_x = fx / scale
                        orig_y = fy / scale
                        orig_w = fw / scale
                        orig_h = fh / scale

                        pad_w = orig_w * 0.15
                        pad_h = orig_h * 0.15

                        xmin = max(0.0, (orig_x - pad_w) / float(w))
                        ymin = max(0.0, (orig_y - pad_h) / float(h))
                        xmax = min(1.0, (orig_x + orig_w + pad_w) / float(w))
                        ymax = min(1.0, (orig_y + orig_h + pad_h) / float(h))

                        box_area = (xmax - xmin) * (ymax - ymin)

                        # Extract 5 facial landmarks normalized to 0..1 [right_eye, left_eye, nose, mouth_r, mouth_l]
                        landmarks = []
                        if len(f) >= 14:
                            for lm_idx in range(4, 14, 2):
                                lx = (f[lm_idx] / scale) / float(w)
                                ly = (f[lm_idx + 1] / scale) / float(h)
                                landmarks.append([round(float(lx), 4), round(float(ly), 4)])

                        results.append({
                            "bbox": [round(float(ymin), 4), round(float(xmin), 4), round(float(ymax), 4), round(float(xmax), 4)],
                            "confidence": round(float(conf), 3),
                            "face_type": "human_face",
                            "box_area": round(float(box_area), 4),
                            "landmarks": landmarks,
                        })
            except Exception:
                pass

        # 2. Detect pet / cat faces only if no human face found (downscaled for speed)
        if not results and self.cat_cascade is not None:
            try:
                c_scale = min(1.0, 384.0 / float(max(h, w)))
                cw_img = max(32, int(w * c_scale))
                ch_img = max(32, int(h * c_scale))
                gray_full = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                gray = cv2.resize(gray_full, (cw_img, ch_img)) if c_scale < 1.0 else gray_full
                min_s = max(24, int(50 * c_scale))
                with self._lock:
                    cat_faces = self.cat_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.15,
                        minNeighbors=7,  # strict to prevent landscape false positives
                        minSize=(min_s, min_s),
                    )
                if len(cat_faces) > 0:
                    for (cx, cy, cw, ch) in cat_faces:
                        pad = cw * 0.12
                        xmin = max(0.0, (cx - pad) / float(cw_img))
                        ymin = max(0.0, (cy - pad) / float(ch_img))
                        xmax = min(1.0, (cx + cw + pad) / float(cw_img))
                        ymax = min(1.0, (cy + ch + pad) / float(ch_img))

                        results.append({
                            "bbox": [round(float(ymin), 4), round(float(xmin), 4), round(float(ymax), 4), round(float(xmax), 4)],
                            "confidence": 0.90,
                            "face_type": "pet_face",
                            "box_area": round(float((xmax - xmin) * (ymax - ymin)), 4),
                        })
            except Exception:
                pass

        results.sort(key=lambda x: x["box_area"], reverse=True)
        for r in results:
            r["is_portrait"] = bool(len(results) == 1 and r["box_area"] > 0.10)

        return results

    def extract_face_embedding(
        self, face_crop: Image.Image, landmarks: Optional[List[List[float]]] = None
    ) -> List[float]:
        """
        Generates a 256-dimensional Perceptual Identity Vector from a face crop.
        Captures structural contours, facial eye/nose/mouth geometry, texture gradients,
        and localized color distribution.
        """
        crop_rgb = np.array(face_crop.convert("RGB").resize((112, 112), Image.Resampling.BICUBIC), dtype=np.float32)

        # Apply Gray-World illumination normalization to eliminate ambient color casts
        mean_rgb = np.mean(crop_rgb, axis=(0, 1)) + 1e-4
        gray_target = np.mean(mean_rgb)
        norm_rgb = np.clip(crop_rgb * (gray_target / mean_rgb), 0, 255).astype(np.uint8)

        gray = cv2.cvtColor(norm_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        hsv = cv2.cvtColor(norm_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        lab = cv2.cvtColor(norm_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

        # 1. Structural Gradient Descriptors (Eyes, Eyebrows, Nose, Lips edges) - 64 dims
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        grad_feats = []
        for r_y in (0, 28, 56, 84):
            for r_x in (0, 28, 56, 84):
                block_mag = mag[r_y : r_y + 28, r_x : r_x + 28]
                block_ang = angle[r_y : r_y + 28, r_x : r_x + 28]
                hist, _ = np.histogram(block_ang, bins=4, range=(0, 360), weights=block_mag)
                norm = np.linalg.norm(hist) + 1e-6
                grad_feats.extend((hist / norm).tolist())

        # 2. Facial Color / Skin / Fur Chrominance distribution - 64 dims
        color_feats = []
        for c in (0, 1, 2):
            h_chan = hsv[:, :, c]
            hist, _ = np.histogram(h_chan, bins=16, range=(0, 256 if c > 0 else 180))
            color_feats.extend((hist / (np.linalg.norm(hist) + 1e-6)).tolist())
        l_chan = lab[:, :, 0]
        hist_l, _ = np.histogram(l_chan, bins=16, range=(0, 256))
        color_feats.extend((hist_l / (np.linalg.norm(hist_l) + 1e-6)).tolist())

        # 3. Spatial symmetry - 64 dims
        left_half = gray[:, :56]
        right_half = cv2.flip(gray[:, 56:], 1)
        symmetry_diff = np.abs(left_half - right_half)
        sym_block = cv2.resize(symmetry_diff, (8, 8)).flatten()
        sym_norm = sym_block / (np.linalg.norm(sym_block) + 1e-6)

        # 4. Landmark Geometry (if available) or Low-Res Structural Descriptor - 64 dims
        geom_feats: List[float] = []
        if landmarks and len(landmarks) >= 5:
            # 5 landmarks: right_eye, left_eye, nose, mouth_r, mouth_l
            re, le, nose, mr, ml = [np.array(pt, dtype=np.float32) for pt in landmarks[:5]]
            eye_dist = float(np.linalg.norm(re - le))
            eye_center = (re + le) / 2.0
            mouth_center = (mr + ml) / 2.0
            mouth_dist = float(np.linalg.norm(mr - ml))
            eye_to_nose = float(np.linalg.norm(eye_center - nose))
            nose_to_mouth = float(np.linalg.norm(nose - mouth_center))
            eye_to_mouth = float(np.linalg.norm(eye_center - mouth_center))

            scale_ref = max(1e-4, eye_dist)
            geom_raw = [
                eye_dist,
                mouth_dist / scale_ref,
                eye_to_nose / scale_ref,
                nose_to_mouth / scale_ref,
                eye_to_mouth / scale_ref,
                float(np.linalg.norm(re - nose)) / scale_ref,
                float(np.linalg.norm(le - nose)) / scale_ref,
                float(np.linalg.norm(mr - nose)) / scale_ref,
                float(np.linalg.norm(ml - nose)) / scale_ref,
                (re[1] - le[1]) / scale_ref,  # eye tilt
                (mr[1] - ml[1]) / scale_ref,  # mouth tilt
                abs(re[0] - nose[0]) / scale_ref,  # horizontal eye balance
                abs(le[0] - nose[0]) / scale_ref,
            ]
            # Tile and normalize to 64 dims
            tiled = np.tile(np.array(geom_raw, dtype=np.float32), 5)[:64]
            geom_norm = tiled / (np.linalg.norm(tiled) + 1e-6)
        else:
            low_res = cv2.resize(gray, (8, 8)).flatten()
            geom_norm = low_res / (np.linalg.norm(low_res) + 1e-6)

        vec = np.concatenate([
            np.array(grad_feats, dtype=np.float32)[:64],
            np.array(color_feats, dtype=np.float32)[:64],
            sym_norm[:64],
            geom_norm[:64],
        ])

        norm = float(np.linalg.norm(vec))
        if norm > 1e-6:
            vec = vec / norm
        return [round(float(x), 5) for x in vec.tolist()]


face_engine = FaceEngine()
