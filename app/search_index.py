# app/search_index.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from joblib import dump, load
from pathlib import Path
from typing import List, Tuple
import numpy as np
import threading
import logging
from .config import settings

logger = logging.getLogger(__name__)

class SearchIndex:
    """
    Thread-safe TF-IDF in-memory index with persistence using joblib.
    - Keep mapping of ids -> texts
    - Persist vectorizer and matrix to disk under TFIDF_DIR
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.ids: List[int] = []
        self.texts: List[str] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.doc_matrix = None
        self.dir = Path(settings.TFIDF_DIR)
        self.vect_file = self.dir / "vectorizer.joblib"
        self.matrix_file = self.dir / "matrix.joblib"
        self.meta_file = self.dir / "meta.joblib"
        self._load_if_exists()

    def _load_if_exists(self):
        try:
            if self.vect_file.exists() and self.matrix_file.exists() and self.meta_file.exists():
                self.vectorizer = load(self.vect_file)
                self.doc_matrix = load(self.matrix_file)
                meta = load(self.meta_file)
                self.ids = meta["ids"]
                self.texts = meta["texts"]
                logger.info("Loaded TF-IDF artifacts from disk.")
        except Exception as e:
            logger.exception("Failed loading TF-IDF artifacts: %s", e)

    def add_bulk(self, items: List[Tuple[int, str]], rebuild: bool = True):
        with self.lock:
            for _id, text in items:
                if _id in self.ids:
                    continue
                self.ids.append(_id)
                self.texts.append(text)
            if rebuild:
                self._rebuild()

    def _rebuild(self):
        with self.lock:
            if not self.texts:
                self.vectorizer = None
                self.doc_matrix = None
                return
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=20000, ngram_range=(1,2))
            self.doc_matrix = self.vectorizer.fit_transform(self.texts)
            # persist to disk (fast)
            dump(self.vectorizer, self.vect_file)
            dump(self.doc_matrix, self.matrix_file)
            dump({"ids": self.ids, "texts": self.texts}, self.meta_file)
            logger.info("Rebuilt and persisted TF-IDF index: %d docs", len(self.ids))

    def query(self, q: str, top_k: int = 5) -> List[Tuple[int, float]]:
        with self.lock:
            if self.vectorizer is None or self.doc_matrix is None:
                return []
            q_vec = self.vectorizer.transform([q])
            sims = linear_kernel(q_vec, self.doc_matrix).flatten()  # cosine similarity
            if sims.max() == 0:
                return []
            top_idx = np.argsort(sims)[-top_k:][::-1]
            results = [(int(self.ids[i]), float(sims[i])) for i in top_idx if sims[i] > 0]
            return results

# instantiate a single shared index (to be imported by main)
search_index = SearchIndex()
