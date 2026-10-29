import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2
from PIL import Image
import onnxruntime as ort

from backend.ai.imagenet_taxonomy import classify_imagenet_idx, CAT_CLASS_MAP, DOG_BREED_HIGHLIGHTS
from backend.ai.face_engine import face_engine
from backend.ai.clip_engine import clip_engine


MOBILENET_ONNX_URL = (
    "https://huggingface.co/onnxmodelzoo/mobilenetv2-12/resolve/main/mobilenetv2-12.onnx"
)


class VisionEmbedder:
    """
    Multimodal Vision-Language (OpenAI CLIP ViT-B/32) + Fine-Grained Perceptual Subject Re-ID Embedder.
    1. Categorizes images into accurate hierarchical concepts (Specific -> Category -> SuperType).
    2. Extracts background-suppressed 256-dim Subject Identity Vectors that reliably
       distinguish individual pets (e.g. a Russian Blue cat 'Blu' vs an orange tabby 'Marmalade')
       and people across different backgrounds and lighting conditions.
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            base = Path(__file__).resolve().parent.parent.parent / ".targon_cache" / "models"
        else:
            base = Path(models_dir)
        base.mkdir(parents=True, exist_ok=True)
        self.onnx_path = base / "mobilenetv2-12.onnx"
        self.session: Optional[ort.InferenceSession] = None
        yy, xx = np.mgrid[0:128, 0:128].astype(np.float32)
        fg_weights = np.exp(
            -(((xx - 64.0) ** 2) / (2 * 36.0**2) + ((yy - 64.0) ** 2) / (2 * 40.0**2))
        )
        self._fg_mask_u8 = (fg_weights > 0.28).astype(np.uint8) * 255
        self._init_onnx_session()

    def _init_onnx_session(self):
        try:
            if not self.onnx_path.exists():
                urllib.request.urlretrieve(MOBILENET_ONNX_URL, str(self.onnx_path))
            if self.onnx_path.exists():
                sess_opts = ort.SessionOptions()
                sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                sess_opts.intra_op_num_threads = 2
                self.session = ort.InferenceSession(
                    str(self.onnx_path),
                    sess_options=sess_opts,
                    providers=["CPUExecutionProvider"],
                )
        except Exception:
            self.session = None

    def _preprocess_imagenet(self, pil_img: Image.Image) -> np.ndarray:
        img = pil_img.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        arr = np.transpose(arr, (2, 0, 1))[np.newaxis, :, :, :]
        return arr

    def run_onnx_logits(self, pil_img: Image.Image) -> Optional[np.ndarray]:
        if self.session is None:
            return None
        try:
            inp_tensor = self._preprocess_imagenet(pil_img)
            inp_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {inp_name: inp_tensor})
            logits = outputs[0][0].astype(np.float32)
            shifted = logits - np.max(logits)
            exp_scores = np.exp(shifted)
            probs = exp_scores / np.sum(exp_scores)
            return probs
        except Exception:
            return None

    def analyze_coat_and_scene_attributes(
        self, pil_img: Image.Image, category: str = "cat"
    ) -> Dict[str, Any]:
        """Extracts pet coat/color attributes strictly tailored to the animal species."""
        rgb = np.array(pil_img.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR))
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)

        center_rgb = rgb[24:104, 24:104]
        center_hsv = hsv[24:104, 24:104]

        mean_s = float(np.mean(center_hsv[:, :, 1]))
        mean_v = float(np.mean(center_hsv[:, :, 2]))
        mean_r = float(np.mean(center_rgb[:, :, 0]))
        mean_g = float(np.mean(center_rgb[:, :, 1]))
        mean_b = float(np.mean(center_rgb[:, :, 2]))

        coat_traits: List[str] = []
        if category == "cat":
            if mean_s < 85 and 55 < mean_v < 195 and (mean_b >= mean_r - 12):
                coat_traits.append("slate-gray coat")
                coat_traits.append("russian blue")
            elif mean_r > mean_b + 38 and mean_g > mean_b + 15 and mean_s > 65:
                coat_traits.append("orange ginger coat")
                coat_traits.append("tabby")
            elif mean_v < 58 and mean_s < 75:
                coat_traits.append("black coat")
            elif mean_v > 200 and mean_s < 55:
                coat_traits.append("white coat")
            elif mean_r > mean_b + 20 and mean_s > 35:
                coat_traits.append("warm brown coat")
        elif category == "dog":
            if mean_r > mean_b + 35 and mean_g > mean_b + 15 and mean_v > 110:
                coat_traits.append("golden coat")
            elif mean_v < 58 and mean_s < 75:
                coat_traits.append("black coat")
            elif mean_v > 200 and mean_s < 55:
                coat_traits.append("white coat")
            elif mean_r > mean_b + 20 and mean_s > 35:
                coat_traits.append("warm brown coat")

        return {
            "coat_traits": coat_traits,
            "scene_tags": [],
        }

    def classify_image_and_crop(
        self,
        full_img: Image.Image,
        crop_img: Image.Image,
        detected_faces: Optional[List[Dict[str, Any]]] = None,
        use_clip: bool = True,
        fast_mode: bool = True,
        return_clip_embed: bool = False,
    ):
        """
        Determines the primary subject category (e.g., 'person', 'cat', 'dog', 'architecture', 'historical art'),
        confidence score, hierarchical tag list [(name, type, conf)], and ONNX probability vector.
        Uses OpenAI CLIP ViT-B/32 as the primary semantic brain, with MobileNetV2 only as a species-consistent booster.
        """
        tag_dict: Dict[Tuple[str, str], float] = {}
        primary_category = "landscape"
        primary_conf = 0.85
        is_illustration = False
        clip_res = None
        clip_emb: Optional[np.ndarray] = None

        # 1. Primary Semantic Brain: OpenAI CLIP Vision-Language Transformer (ViT-B/32)
        if use_clip and clip_engine.is_ready:
            clip_res = clip_engine.classify_image_detailed(
                full_img, crop_img, top_k=5, single_pass=fast_mode
            )
            if clip_res is not None:
                primary_category = clip_res["category"]
                primary_conf = clip_res["confidence"]
                is_illustration = bool(clip_res.get("is_illustration", False))
                clip_emb = clip_res.get("full_embedding")
                for t_name, t_type, t_conf in clip_res["tags"]:
                    tag_dict[(t_name, t_type)] = max(tag_dict.get((t_name, t_type), 0.0), t_conf)

        # 2. Check for detected human faces or pet faces
        human_faces = [f for f in (detected_faces or []) if f.get("face_type") == "human_face"]
        pet_faces = [f for f in (detected_faces or []) if f.get("face_type") == "pet_face"]

        if human_faces:
            if is_illustration:
                # Painted/illustrated characters (e.g. medieval knights) keep their Artwork category
                tag_dict[("character portrait", "attribute")] = 0.92
            else:
                primary_category = "person"
                primary_conf = 0.98
                tag_dict[("person", "category")] = 0.99
                tag_dict[("people", "category")] = 0.98
                tag_dict[("human face", "attribute")] = 0.97
                if len(human_faces) == 1:
                    tag_dict[("portrait", "scene")] = 0.95
                else:
                    tag_dict[("group photo", "scene")] = 0.94
        elif pet_faces and not is_illustration and primary_category in ("cat", "dog", "animal"):
            tag_dict[("pet face", "attribute")] = 0.94

        # 3. Secondary Species-Consistent Fine-Grained Booster (or Fallback if CLIP unavailable/disabled)
        probs: Optional[np.ndarray] = None
        need_mobilenet = (
            clip_res is None
            or primary_category in ("cat", "dog")
            or not fast_mode
        )
        if need_mobilenet:
            probs = self.run_onnx_logits(crop_img)
            if probs is None and crop_img is not full_img:
                probs = self.run_onnx_logits(full_img)

        if probs is not None:
            top_indices = np.argsort(probs)[::-1][:5]
            top_idx = int(top_indices[0])
            top_prob = float(probs[top_idx])

            if clip_res is None and not human_faces:
                # Offline / Low-Spec fallback when CLIP is not used
                cat_mass = float(np.sum(probs[281:294]))
                dog_mass = float(np.sum(probs[151:269]))
                if cat_mass >= 0.12 or (281 <= top_idx <= 293):
                    primary_category = "cat"
                    primary_conf = min(0.99, max(0.80, cat_mass * 2.0, top_prob))
                    tag_dict[("cat", "category")] = primary_conf
                    tag_dict[("pet", "category")] = round(primary_conf * 0.96, 3)
                    tag_dict[("feline", "category")] = round(primary_conf * 0.94, 3)
                    tag_dict[("animal", "category")] = round(primary_conf * 0.95, 3)
                elif dog_mass >= 0.20 or (151 <= top_idx <= 268):
                    primary_category = "dog"
                    primary_conf = min(0.99, max(0.80, dog_mass * 1.8, top_prob))
                    tag_dict[("dog", "category")] = primary_conf
                    tag_dict[("pet", "category")] = round(primary_conf * 0.96, 3)
                    tag_dict[("canine", "category")] = round(primary_conf * 0.94, 3)
                    tag_dict[("animal", "category")] = round(primary_conf * 0.95, 3)
                else:
                    primary_category, sub_tags = classify_imagenet_idx(top_idx)
                    primary_conf = min(0.95, max(0.70, top_prob * 1.5))
                    for t_name, t_type in sub_tags:
                        tag_dict[(t_name, t_type)] = primary_conf
            elif not is_illustration:
                # When CLIP is active, only add MobileNetV2 breed/species tags if they agree with CLIP's category
                if primary_category == "cat":
                    best_cat_idx = 281 + int(np.argmax(probs[281:286]))
                    if probs[best_cat_idx] > 0.18 and best_cat_idx in CAT_CLASS_MAP:
                        breed_label = CAT_CLASS_MAP[best_cat_idx]
                        if breed_label != "egyptian cat":
                            tag_dict[(breed_label, "attribute")] = round(float(probs[best_cat_idx]), 3)
                elif primary_category == "dog":
                    best_dog_idx = 151 + int(np.argmax(probs[151:269]))
                    if best_dog_idx in DOG_BREED_HIGHLIGHTS and probs[best_dog_idx] > 0.15:
                        tag_dict[(DOG_BREED_HIGHLIGHTS[best_dog_idx], "attribute")] = round(
                            float(probs[best_dog_idx]), 3
                        )
                elif top_prob >= 0.35:
                    m_cat, extra_tags = classify_imagenet_idx(top_idx)
                    if m_cat == primary_category:
                        for t_name, t_type in extra_tags:
                            if (t_name, t_type) not in tag_dict:
                                tag_dict[(t_name, t_type)] = round(top_prob, 3)

        # 4. Enrich with species-specific coat attributes for real pets
        if primary_category in ("cat", "dog") and not is_illustration:
            traits = self.analyze_coat_and_scene_attributes(crop_img, category=primary_category)
            for ct in traits["coat_traits"]:
                if (ct, "attribute") not in tag_dict:
                    tag_dict[(ct, "attribute")] = 0.88

        tags_list = [
            (name, t_type, round(conf, 3))
            for (name, t_type), conf in sorted(tag_dict.items(), key=lambda x: x[1], reverse=True)
        ]
        if return_clip_embed:
            return primary_category, round(primary_conf, 3), tags_list, probs, clip_emb
        return primary_category, round(primary_conf, 3), tags_list, probs

    def extract_subject_identity_embedding(
        self,
        crop_img: Image.Image,
        onnx_probs: Optional[np.ndarray] = None,
        face_type: Optional[str] = None,
        landmarks: Optional[List[List[float]]] = None,
        precomputed_clip_embed: Optional[np.ndarray] = None,
        use_clip: bool = True,
    ) -> List[float]:
        """
        Computes a 256-dimensional L2-normalized Subject Identity Embedding Vector.
        If a human face is detected, delegates to the FaceEngine structural descriptor.
        For pets/people, combines background-suppressed color, texture, anatomy zones, and CLIP semantic features.
        """
        if face_type == "human_face":
            return face_engine.extract_face_embedding(crop_img, landmarks=landmarks)
        rgb = np.array(crop_img.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR))
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

        fg_mask_u8 = self._fg_mask_u8

        # 1. Weighted 3D HSV Coat Color & Saturation Histogram (64 dims)
        hist_hsv = cv2.calcHist(
            [hsv], [0, 1, 2], fg_mask_u8, [8, 4, 2], [0, 180, 0, 256, 0, 256]
        ).flatten()
        hist_hsv = hist_hsv / (np.linalg.norm(hist_hsv) + 1e-6)

        # 2. Perceptual CIELAB Chromaticity & Luminance Histogram (48 dims)
        hist_lab = cv2.calcHist(
            [lab], [0, 1, 2], fg_mask_u8, [6, 4, 2], [0, 256, 40, 220, 40, 220]
        ).flatten()
        hist_lab = hist_lab / (np.linalg.norm(hist_lab) + 1e-6)

        # 3. Spatial Anatomy Zones in Normalized Lab & RGB (48 dims)
        zones = [
            (16, 48, 32, 96),
            (36, 76, 36, 92),
            (64, 110, 28, 100),
            (28, 100, 28, 100),
        ]
        zone_feats: List[float] = []
        for y1, y2, x1, x2 in zones:
            patch_lab = lab[y1:y2, x1:x2]
            patch_rgb = rgb[y1:y2, x1:x2].astype(np.float32) / 255.0
            l_mean = (float(np.mean(patch_lab[:, :, 0])) - 128.0) / 128.0
            a_mean = (float(np.mean(patch_lab[:, :, 1])) - 128.0) / 64.0
            b_mean = (float(np.mean(patch_lab[:, :, 2])) - 128.0) / 64.0
            l_std = float(np.std(patch_lab[:, :, 0])) / 64.0
            a_std = float(np.std(patch_lab[:, :, 1])) / 32.0
            b_std = float(np.std(patch_lab[:, :, 2])) / 32.0

            rb_diff = float(np.mean(patch_rgb[:, :, 0] - patch_rgb[:, :, 2]))
            gb_diff = float(np.mean(patch_rgb[:, :, 1] - patch_rgb[:, :, 2]))
            rg_diff = float(np.mean(patch_rgb[:, :, 0] - patch_rgb[:, :, 1]))
            rgb_std = float(np.std(patch_rgb))

            p90 = float(np.percentile(patch_lab[:, :, 0], 90))
            p10 = float(np.percentile(patch_lab[:, :, 0], 10))
            contrast_span = (p90 - p10) / 255.0
            chroma_mag = float(
                np.mean(
                    np.sqrt(
                        (patch_lab[:, :, 1] - 128.0) ** 2 + (patch_lab[:, :, 2] - 128.0) ** 2
                    )
                )
            ) / 64.0

            zone_feats.extend(
                [
                    l_mean,
                    a_mean * 1.8,
                    b_mean * 1.8,
                    l_std,
                    a_std,
                    b_std,
                    rb_diff * 2.0,
                    gb_diff * 2.0,
                    rg_diff * 2.0,
                    rgb_std,
                    contrast_span,
                    chroma_mag * 1.5,
                ]
            )
        zone_arr = np.array(zone_feats, dtype=np.float32)
        zone_arr = zone_arr / (np.linalg.norm(zone_arr) + 1e-6)

        # 4. Coat Pattern & Texture Descriptor (48 dims)
        gray = cv2.cvtColor(rgb[20:108, 20:108], cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        orient_hist, _ = np.histogram(ang, bins=16, range=(0, 360), weights=mag)
        mag_hist, _ = np.histogram(mag, bins=16, range=(0, 1.5))
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_32F, ksize=3))
        lap_hist, _ = np.histogram(lap, bins=16, range=(0, 1.0))
        tex_arr = np.concatenate([orient_hist, mag_hist, lap_hist]).astype(np.float32)
        tex_arr = tex_arr / (np.linalg.norm(tex_arr) + 1e-6)

        # 5. Deep CLIP Vision-Language Transformer Embedding Slice (48 dims)
        clip_slice = np.zeros(48, dtype=np.float32)
        c_embed = precomputed_clip_embed
        if c_embed is None and use_clip and clip_engine.is_ready:
            c_embed = clip_engine.embed_image(crop_img)
        if c_embed is not None and len(c_embed) == 512:
            stride = 512 // 48
            clip_slice = np.array(
                [c_embed[i * stride : (i + 1) * stride].mean() for i in range(48)],
                dtype=np.float32,
            )
            clip_slice = clip_slice / (np.linalg.norm(clip_slice) + 1e-6)
        elif onnx_probs is not None and len(onnx_probs) == 1000:
            selected_indices = list(range(281, 294)) + list(range(151, 290, 4))[:35]
            neural_slice = onnx_probs[selected_indices].astype(np.float32)
            neural_slice = np.power(np.maximum(neural_slice, 1e-8), 0.35)
            clip_slice = neural_slice / (np.linalg.norm(neural_slice) + 1e-6)

        combined = np.concatenate(
            [
                hist_hsv * 1.35,      # 64 dims
                hist_lab * 1.35,      # 48 dims
                zone_arr * 1.60,      # 48 dims
                tex_arr * 0.75,       # 48 dims
                clip_slice * 1.15,    # 48 dims
            ]
        ).astype(np.float32)

        norm = float(np.linalg.norm(combined))
        if norm > 1e-6:
            combined = combined / norm
        return [round(float(x), 5) for x in combined]
