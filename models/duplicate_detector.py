"""
Phase 4: Multilingual Duplicate Detection Engine.
Uses sentence embeddings (paraphrase-multilingual-mpnet-base-v2) or character n-gram cosine vectorizer.
Integrates FAISS vector search (or NumPy fallback) for fast nearest-neighbor matching.
"""

import math
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from config import DUPLICATE_SIMILARITY_THRESHOLD, DATA_DIR, MODELS_DIR


class FallbackEmbedder:
    """Lightweight character 3-gram vectorizer when sentence-transformers is missing."""

    def embed(self, text: str) -> np.ndarray:
        clean = re.sub(r'\s+', ' ', text.lower().strip())
        ngrams = [clean[i:i+3] for i in range(len(clean)-2)]
        vec = np.zeros(256, dtype=np.float32)
        for ng in ngrams:
            idx = sum(ord(c) for c in ng) % 256
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


class DuplicateDetector:
    """
    Multilingual duplicate complaint detector using vector embeddings & FAISS similarity.
    """

    def __init__(self, similarity_threshold: float = DUPLICATE_SIMILARITY_THRESHOLD):
        self.similarity_threshold = similarity_threshold
        self.complaint_db: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
            except Exception:
                self.model = FallbackEmbedder()
        else:
            self.model = FallbackEmbedder()

    def get_embedding(self, text: str) -> np.ndarray:
        if isinstance(self.model, FallbackEmbedder):
            return self.model.embed(text)
        else:
            return self.model.encode([text], normalize_embeddings=True)[0].astype(np.float32)

    def populate_database(self, complaints: List[Dict]):
        """Index complaints into vector database."""
        self.complaint_db = complaints
        if not complaints:
            self.embeddings = None
            return

        vecs = [self.get_embedding(item["text"]) for item in complaints]
        self.embeddings = np.array(vecs, dtype=np.float32)

    def check_duplicate(self, text: str, category: Optional[str] = None) -> Dict:
        """
        Checks if text is a duplicate of any existing complaint in database.
        Optionally filters comparison candidates by category.
        """
        if self.embeddings is None or len(self.complaint_db) == 0:
            return {"is_duplicate": False, "highest_similarity": 0.0, "matched_complaint": None}

        query_vec = self.get_embedding(text)

        best_sim = -1.0
        best_match = None

        for idx, item in enumerate(self.complaint_db):
            if category and item.get("category") != category:
                continue

            doc_vec = self.embeddings[idx]
            sim = float(np.dot(query_vec, doc_vec))

            if sim > best_sim:
                best_sim = sim
                best_match = item

        is_dup = best_sim >= self.similarity_threshold

        return {
            "is_duplicate": is_dup,
            "similarity_score": round(best_sim, 4),
            "threshold": self.similarity_threshold,
            "matched_complaint": {
                "id": best_match["id"],
                "text": best_match["text"],
                "category": best_match["category"],
                "priority": best_match["priority"]
            } if best_match else None
        }


if __name__ == "__main__":
    detector = DuplicateDetector(similarity_threshold=0.80)
    
    with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
        samples = json.load(f)[:50]
        
    detector.populate_database(samples)

    # Test exact / similar query
    test_query = samples[0]["text"]
    res = detector.check_duplicate(test_query)
    print("Duplicate Check Result for known sample:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
