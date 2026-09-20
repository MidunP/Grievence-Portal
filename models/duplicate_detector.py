"""
Phase 4: Multilingual Duplicate Detection Engine — v2.
Uses sentence embeddings (paraphrase-multilingual-mpnet-base-v2) when available.
Falls back to a hybrid TF-IDF cosine similarity (word + char n-gram) that is far
more accurate than the previous character-hash vector approach.
"""

import json
import re
import math
import pickle
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

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import csr_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from config import DUPLICATE_SIMILARITY_THRESHOLD, DATA_DIR, MODELS_DIR


# ─────────────────────────────────────────────────────────────────────────────
# TF-IDF Cosine Fallback (much better than the old character-hash embedder)
# ─────────────────────────────────────────────────────────────────────────────
class TfidfCosineEmbedder:
    """
    Dual TF-IDF (word + char n-gram) vectorizer for fallback duplicate detection.
    Fit once on the database corpus, then embed individual queries.
    """

    def __init__(self):
        self.word_vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), max_features=10_000,
            sublinear_tf=True, min_df=1
        )
        self.char_vec = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), max_features=15_000,
            sublinear_tf=True, min_df=1
        )
        self.is_fit = False

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        from scipy.sparse import hstack
        Xw = self.word_vec.fit_transform(texts)
        Xc = self.char_vec.fit_transform(texts)
        X = hstack([Xw, Xc]).toarray().astype(np.float32)
        # L2 normalise rows
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        X = X / norms
        self.is_fit = True
        return X

    def transform(self, text: str) -> np.ndarray:
        from scipy.sparse import hstack
        Xw = self.word_vec.transform([text])
        Xc = self.char_vec.transform([text])
        v = hstack([Xw, Xc]).toarray().astype(np.float32)[0]
        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Legacy character-hash embedder (kept as last resort)
# ─────────────────────────────────────────────────────────────────────────────
class FallbackEmbedder:
    """Character 3-gram and word 1-gram hybrid vectorizer (legacy)."""

    def embed(self, text: str) -> np.ndarray:
        clean = re.sub(r'[^\w\s]', '', text.lower().strip())
        words = clean.split()
        ngrams = [clean[i:i+3] for i in range(len(clean) - 2)]
        vec = np.zeros(512, dtype=np.float32)
        for w in words:
            idx = sum(ord(c) for c in w) % 256
            vec[idx] += 2.0
        for ng in ngrams:
            idx = 256 + (sum(ord(c) for c in ng) % 256)
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


# ─────────────────────────────────────────────────────────────────────────────
# Main Duplicate Detector
# ─────────────────────────────────────────────────────────────────────────────
class DuplicateDetector:
    """
    Multilingual duplicate complaint detector.
    Embedding priority:
      1. SentenceTransformer (paraphrase-multilingual-mpnet-base-v2) — best quality
      2. TF-IDF Cosine (sklearn)                                     — good fallback
      3. Character-hash (legacy)                                     — last resort
    """

    def __init__(self, similarity_threshold: Optional[float] = None):
        self.complaint_db: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None

        # Determine embedding backend
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
                )
                self.backend = "sentence_transformer"
                default_thresh = DUPLICATE_SIMILARITY_THRESHOLD
            except Exception:
                self.model = None
                self.backend = "tfidf" if SKLEARN_AVAILABLE else "hash"
                default_thresh = 0.75
        elif SKLEARN_AVAILABLE:
            self.model = TfidfCosineEmbedder()
            self.backend = "tfidf"
            default_thresh = 0.70
        else:
            self.model = FallbackEmbedder()
            self.backend = "hash"
            default_thresh = 0.75

        self.similarity_threshold = similarity_threshold if similarity_threshold is not None else default_thresh
        print(f"  [DupDetector] Backend: {self.backend}, threshold={self.similarity_threshold}")

    def get_embedding(self, text: str) -> np.ndarray:
        if self.backend == "sentence_transformer":
            return self.model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
        elif self.backend == "tfidf":
            return self.model.transform(text)
        else:
            return self.model.embed(text)

    def populate_database(self, complaints: List[Dict]):
        """Index complaints into the vector database."""
        self.complaint_db = complaints
        if not complaints:
            self.embeddings = None
            return

        texts = [item["text"] for item in complaints]

        if self.backend == "sentence_transformer":
            vecs = self.model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
            self.embeddings = np.array(vecs, dtype=np.float32)
        elif self.backend == "tfidf":
            self.embeddings = self.model.fit_transform(texts)
        else:
            vecs = [self.model.embed(t) for t in texts]
            self.embeddings = np.array(vecs, dtype=np.float32)

        print(f"  [DupDetector] Indexed {len(complaints)} complaints, shape={self.embeddings.shape}")

    def check_duplicate(self, text: str, category: Optional[str] = None) -> Dict:
        """
        Checks if text is a near-duplicate of any complaint in the database.
        Optionally filters by category for higher precision.
        """
        if self.embeddings is None or len(self.complaint_db) == 0:
            return {"is_duplicate": False, "similarity_score": 0.0, "matched_complaint": None}

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
            "backend": self.backend,
            "matched_complaint": {
                "id": best_match["id"],
                "text": best_match["text"],
                "category": best_match["category"],
                "priority": best_match.get("priority", "Unknown"),
            } if best_match else None,
        }


if __name__ == "__main__":
    detector = DuplicateDetector(similarity_threshold=0.70)

    with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
        samples = json.load(f)[:100]

    detector.populate_database(samples)

    test_query = samples[0]["text"]
    res = detector.check_duplicate(test_query)
    print("Duplicate Check Result for known sample:")
    print(json.dumps(res, indent=2, ensure_ascii=False))

    # Test dissimilar query
    res2 = detector.check_duplicate("Completely unrelated text about something else entirely.")
    print("\nDuplicate Check for dissimilar text:")
    print(json.dumps(res2, indent=2, ensure_ascii=False))
