import json
from typing import Dict, Any, List, Optional
from PIL import Image

from backend.security.vault import vault


class GeminiVisionBooster:
    """
    Cloud Vision Engine using Google Gemini (google-genai SDK).
    Supports 'hybrid' (local ONNX + Gemini enrichment) and 'cloud' (Gemini-first) modes.
    Always uses PPAPI-stored local credentials if not explicitly passed.
    """

    def analyze_photo(
        self,
        pil_img: Image.Image,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        known_subjects: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        # Resolve key from PPAPI vault if not provided
        resolved_key = (api_key or "").strip()
        if not resolved_key:
            resolved_key = vault.get_gemini_api_key()

        if not resolved_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=resolved_key)

            known_desc = ""
            if known_subjects:
                named_list = [
                    f"- {s.get('name', s.get('display_name', ''))} (category: {s.get('category', 'unknown')})"
                    for s in known_subjects
                    if (s.get("is_named") or s.get("name")) and s.get("name")
                ]
                if named_list:
                    known_desc = (
                        "Known named individuals and pets in user's library:\n"
                        + "\n".join(named_list)
                        + "\nMatch visually if this photo is definitely the same individual/pet.\n"
                    )

            prompt = (
                "You are an expert Apple Photos-style visual intelligence engine.\n"
                f"{known_desc}"
                "Analyze this photo in high detail and return ONLY valid JSON matching this schema:\n"
                "{\n"
                '  "primary_category": "person" | "cat" | "dog" | "bird" | "nature" | "landscape" | "food" | "vehicle" | "architecture" | "indoor" | "document" | "object",\n'
                '  "super_type": "People" | "Animal" | "Nature" | "Urban" | "Object",\n'
                '  "has_faces": true or false,\n'
                '  "face_count": number of human or pet faces,\n'
                '  "faces": [\n'
                '    {\n'
                '      "type": "human_face" | "pet_face",\n'
                '      "bbox": [ymin, xmin, ymax, xmax],\n'
                '      "expression_or_traits": "smiling, brown hair" | "green eyes, blue-gray coat",\n'
                '      "matched_name": "Blu" | "Sarah" | null\n'
                '    }\n'
                '  ],\n'
                '  "has_distinct_subject": true or false,\n'
                '  "subject_bbox": [ymin, xmin, ymax, xmax] normalized between 0.0 and 1.0,\n'
                '  "matched_known_name": string or null,\n'
                '  "suggested_individual_name": "Blu" | "Alice" | null,\n'
                '  "fine_grained_tags": ["Russian Blue", "Indoor", "Velvet Sofa", "Emerald Eyes", "Feline", "Portrait"],\n'
                '  "category_tags": ["cat", "pet", "animal"],\n'
                '  "scene_tags": ["indoor", "living room", "warm lighting"],\n'
                '  "attribute_tags": ["blue-gray fur", "calm expression"],\n'
                '  "description": "One concise, warm, Apple-style sentence describing the photo."\n'
                "}"
            )

            thumb = pil_img.copy()
            thumb.thumbnail((768, 768))

            response = client.models.generate_content(
                model=model_name or "gemini-2.5-flash",
                contents=[thumb, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            if response and response.text:
                return json.loads(response.text)
        except Exception as e:
            return None
        return None
