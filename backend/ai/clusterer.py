import threading
from typing import List, Optional, Tuple
import numpy as np
from backend.db.database import Database


class SubjectClusterer:
    """
    Matches detected subject crops against known identity clusters (e.g., 'Blu' vs another cat)
    using cosine similarity over 256-dim Subject Identity Embeddings.
    """

    def __init__(self, db: Database):
        self.db = db
        self._lock = threading.Lock()

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        n1 = float(np.linalg.norm(v1))
        n2 = float(np.linalg.norm(v2))
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))

    def match_or_create_subject(
        self,
        category: str,
        embedding: List[float],
        avatar_path: Optional[str] = None,
        suggested_name: Optional[str] = None,
        similarity_threshold: float = 0.76,
    ) -> Tuple[int, float, bool]:
        """
        Finds the best matching subject within the same category (e.g., 'cat').
        If cosine similarity >= similarity_threshold, assigns to that subject.
        Otherwise creates a new distinct subject entity!
        Returns: (subject_id, match_confidence, is_existing_match)
        """
        cat_clean = category.strip().lower()
        vec = np.array(embedding, dtype=np.float32)

        with self._lock:
            existing_subjects = self.db.get_all_subjects_with_vectors()

            # If a specific name was suggested (e.g., by Gemini Cloud or filename cue), check if that named subject exists
            if suggested_name:
                for s in existing_subjects:
                    if s.get("name") and s["name"].lower() == suggested_name.strip().lower():
                        return s["id"], 0.96, True

            best_subject_id: Optional[int] = None
            best_sim: float = -1.0

            for s in existing_subjects:
                if s["category"].lower() != cat_clean:
                    continue
                centroid = s.get("centroid")
                if centroid is None or len(centroid) != len(vec):
                    continue
                sim = self.cosine_similarity(vec, centroid)
                if sim > best_sim:
                    best_sim = sim
                    best_subject_id = s["id"]

            if best_subject_id is not None and best_sim >= similarity_threshold:
                return best_subject_id, round(min(0.99, best_sim), 3), True

            # No close match found -> this is a different individual (e.g., a different cat!)
            new_id = self.db.create_subject(
                category=cat_clean,
                centroid_vector=embedding,
                avatar_path=avatar_path,
                name=suggested_name,
            )
            return new_id, 0.92, False
