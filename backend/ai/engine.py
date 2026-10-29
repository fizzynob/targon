from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageOps

from backend.db.database import Database
from backend.scanner.thumbnailer import Thumbnailer
from backend.ai.detector import SubjectDetector
from backend.ai.embedder import VisionEmbedder
from backend.ai.clusterer import SubjectClusterer
from backend.ai.gemini_booster import GeminiVisionBooster
from backend.ai.scene_analyzer import scene_analyzer
from backend.ai.ocr_engine import ocr_engine
from backend.ai.clip_engine import clip_engine


INDIVIDUAL_SUBJECT_CATEGORIES = {"cat", "dog", "bird", "animal", "person"}


class AIEngine:
    """
    Unified 3-Mode AI Engine for Targon:
      - 'local': 100% offline ONNX neural network + perceptual subject Re-ID clustering + Live Text OCR
      - 'hybrid': Local ONNX + Subject Re-ID + Gemini 2.5 Flash multimodal enrichment
      - 'cloud': Gemini 2.5 Flash primary vision analysis with local Re-ID embedding
    """

    def __init__(self, db: Database, thumbnailer: Thumbnailer):
        self.db = db
        self.thumbnailer = thumbnailer
        self.detector = SubjectDetector()
        self.embedder = VisionEmbedder()
        self.clusterer = SubjectClusterer(db)
        self.gemini = GeminiVisionBooster()

    def process_photo(
        self,
        photo_id: int,
        image_path: str,
        file_hash: str,
        pil_img: Optional[Image.Image] = None,
        sync_xmp: bool = True,
    ) -> Dict[str, Any]:
        settings = self.db.get_settings()
        ai_mode = settings.get("ai_mode", "local")
        api_key = settings.get("gemini_api_key", "")
        gemini_model = settings.get("gemini_model", "gemini-2.5-flash")
        sim_threshold = float(settings.get("similarity_threshold", 0.76))
        low_spec_mode = bool(settings.get("low_spec_mode", False))
        fast_tagging = bool(settings.get("fast_tagging", True)) or low_spec_mode
        enable_clip = bool(settings.get("enable_clip_search", True)) and not low_spec_mode
        enable_ocr = bool(settings.get("enable_ocr", True))
        enable_faces = bool(settings.get("enable_face_detection", True))
        enable_scene = bool(settings.get("enable_scene_analysis", True))
        auto_cluster = bool(settings.get("auto_cluster", True))

        if pil_img is not None:
            full_img = pil_img if pil_img.mode == "RGB" else pil_img.convert("RGB")
        else:
            with Image.open(image_path) as raw_img:
                full_img = ImageOps.exif_transpose(raw_img).convert("RGB")

        # 1. Detect salient subject bounding box and any human/pet faces
        bbox, det_conf, detected_faces = self.detector.detect_all_subjects_and_faces(
            full_img, enable_faces=enable_faces
        )
        crop_img, crop_path = self.thumbnailer.save_subject_crop(
            image_path, file_hash, bbox, idx=0, pil_img=full_img
        )
        if crop_img is None:
            crop_img = full_img

        # 2. Run Local ONNX Neural Classification & Fine-Grained Attribute/Face Extraction
        (
            primary_cat,
            primary_conf,
            local_tags,
            onnx_probs,
            full_clip_embedding,
        ) = self.embedder.classify_image_and_crop(
            full_img,
            crop_img,
            detected_faces=detected_faces,
            use_clip=enable_clip,
            fast_mode=fast_tagging,
            return_clip_embed=True,
        )

        # 3. Intelligent Photometric, Lighting & Composition Scene Analysis
        if enable_scene:
            scene_res = scene_analyzer.analyze_scene(full_img)
            for s_tag, s_type, s_conf in scene_res.get("tags", []):
                local_tags.append((s_tag, s_type, s_conf))

        # 4. Apple Photos-style Live Text / Windows Native OCR Recognition (fast-gated)
        ocr_text = None
        if enable_ocr and (not low_spec_mode or primary_cat in ("document", "screenshot")):
            force_ocr = primary_cat in ("document", "screenshot") or any(
                t[0] in ("document", "receipt", "printed text", "digital interface", "text")
                for t in local_tags
            )
            ocr_res = ocr_engine.extract_text(full_img, fast_gate=not force_ocr)
            ocr_text = ocr_res.get("text") or None
            for o_tag, o_type, o_conf in ocr_res.get("tags", []):
                local_tags.append((o_tag, o_type, o_conf))

        engine_used = "local"
        description: Optional[str] = None
        suggested_name: Optional[str] = None

        # 5. Optional Gemini Cloud / Hybrid Vision Enrichment (using local PPAPI key)
        if ai_mode in ("hybrid", "cloud"):
            known_subjects = self.db.get_subjects()
            cloud_res = self.gemini.analyze_photo(
                full_img,
                api_key=api_key,
                model_name=gemini_model,
                known_subjects=known_subjects,
            )
            if cloud_res:
                engine_used = ai_mode
                if cloud_res.get("primary_category"):
                    primary_cat = str(cloud_res["primary_category"]).lower()
                if cloud_res.get("description"):
                    description = str(cloud_res["description"])
                if cloud_res.get("matched_known_name"):
                    suggested_name = str(cloud_res["matched_known_name"]).strip()
                elif cloud_res.get("suggested_individual_name"):
                    suggested_name = str(cloud_res["suggested_individual_name"]).strip()

                if (
                    isinstance(cloud_res.get("subject_bbox"), list)
                    and len(cloud_res["subject_bbox"]) == 4
                ):
                    bbox = [float(x) for x in cloud_res["subject_bbox"]]
                    new_crop, new_crop_path = self.thumbnailer.save_subject_crop(
                        image_path, file_hash, bbox, idx=0, pil_img=full_img
                    )
                    if new_crop is not None:
                        crop_img = new_crop
                        crop_path = new_crop_path

                # Fine-grained multi-label tags from Gemini
                for fg_tag in cloud_res.get("fine_grained_tags", []):
                    local_tags.append((str(fg_tag).strip(), "attribute", 0.96))
                for c_tag in cloud_res.get("category_tags", []):
                    local_tags.append((str(c_tag).strip().lower(), "category", 0.95))
                for s_tag in cloud_res.get("scene_tags", []):
                    local_tags.append((str(s_tag).strip().lower(), "scene", 0.92))
                for a_tag in cloud_res.get("attribute_tags", []):
                    local_tags.append((str(a_tag).strip().lower(), "attribute", 0.90))

        # 6. Multi-Subject & Facial Identity Embedding & Clustering (for real-world people & animals)
        matched_subjects = []
        primary_identity_embedding = None
        is_artwork = primary_cat in ("character art", "historical art", "artwork", "architecture")

        if auto_cluster and detected_faces and not is_artwork:
            # Process ALL detected faces (identifying each person or pet in group photos)
            for f_idx, f_info in enumerate(detected_faces[:5]):
                f_box = f_info["bbox"]
                f_type = f_info.get("face_type")
                f_landmarks = f_info.get("landmarks")

                f_crop, f_crop_path = self.thumbnailer.save_subject_crop(
                    image_path, file_hash, f_box, idx=f_idx, pil_img=full_img
                )
                if f_crop is None:
                    continue

                f_emb = self.embedder.extract_subject_identity_embedding(
                    f_crop,
                    onnx_probs,
                    face_type=f_type,
                    landmarks=f_landmarks,
                    precomputed_clip_embed=full_clip_embedding if f_idx == 0 else None,
                    use_clip=enable_clip and not fast_tagging,
                )
                if f_idx == 0:
                    primary_identity_embedding = f_emb

                sub_cat = "person" if f_type == "human_face" else primary_cat
                sub_id, match_conf, _ = self.clusterer.match_or_create_subject(
                    category=sub_cat,
                    embedding=f_emb,
                    avatar_path=f_crop_path,
                    suggested_name=suggested_name if f_idx == 0 else None,
                    similarity_threshold=sim_threshold,
                )
                self.db.link_photo_subject(
                    photo_id=photo_id,
                    subject_id=sub_id,
                    bbox=f_box,
                    confidence=match_conf,
                    embedding_vector=f_emb,
                    crop_path=f_crop_path,
                )
                s_item = self.db.get_subject_by_id(sub_id)
                if s_item:
                    matched_subjects.append(s_item)

        elif auto_cluster and primary_cat in INDIVIDUAL_SUBJECT_CATEGORIES and not is_artwork:
            # Salient subject bounding box (pets, animals, or back/side-view people without frontal face cascade)
            identity_embedding = self.embedder.extract_subject_identity_embedding(
                crop_img,
                onnx_probs,
                face_type=None,
                precomputed_clip_embed=full_clip_embedding,
                use_clip=enable_clip and not fast_tagging,
            )
            primary_identity_embedding = identity_embedding

            sub_id, match_conf, _ = self.clusterer.match_or_create_subject(
                category=primary_cat,
                embedding=identity_embedding,
                avatar_path=crop_path,
                suggested_name=suggested_name,
                similarity_threshold=sim_threshold,
            )
            self.db.link_photo_subject(
                photo_id=photo_id,
                subject_id=sub_id,
                bbox=bbox,
                confidence=match_conf,
                embedding_vector=identity_embedding,
                crop_path=crop_path,
            )
            s_item = self.db.get_subject_by_id(sub_id)
            if s_item:
                matched_subjects.append(s_item)

        # 7. Store Hierarchical Tags in a single fast batch transaction
        seen_tags = set()
        batch_tags = []
        for tag_name, tag_type, conf in local_tags:
            clean_name = tag_name.strip()
            if not clean_name:
                continue
            t_key = (clean_name.lower(), tag_type)
            if t_key not in seen_tags:
                seen_tags.add(t_key)
                batch_tags.append((clean_name, tag_type, conf, "ai"))
        if batch_tags:
            self.db.add_photo_tags_batch(photo_id, batch_tags, sync_xmp=False)

        # 8. Build concise Apple Photos-style description if none came from Gemini
        if not description:
            attr_strs = [t[0] for t in local_tags if t[1] == "attribute"]
            scene_strs = [t[0] for t in local_tags if t[1] == "scene"]
            if matched_subjects:
                subj_names = [s["display_name"].lower() for s in matched_subjects]
                subj_label = f"{', '.join(subj_names[:2])} ({primary_cat.lower()})"
            else:
                subj_label = primary_cat.lower()
            details = ", ".join((attr_strs[:2] + scene_strs[:2])).lower()
            description = f"{subj_label} - {details}" if details else subj_label

        # Reuse already-computed 512-dim CLIP visual embedding (zero extra inference cost!)
        scene_emb = (
            [round(float(x), 5) for x in full_clip_embedding]
            if full_clip_embedding is not None
            else primary_identity_embedding
        )

        self.db.mark_photo_ai_processed(
            photo_id=photo_id,
            description=description,
            engine_used=engine_used,
            scene_embedding=scene_emb,
            face_count=len(detected_faces),
            face_boxes=detected_faces,
            ocr_text=ocr_text,
            sync_xmp=sync_xmp,
        )

        return {
            "photo_id": photo_id,
            "primary_category": primary_cat,
            "subject": matched_subjects[0] if matched_subjects else None,
            "subjects": matched_subjects,
            "description": description,
            "engine_used": engine_used,
            "ocr_text": ocr_text,
        }
