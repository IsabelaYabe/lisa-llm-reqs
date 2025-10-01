# ml_core.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence, Optional, Literal, Tuple
import numpy as np
import pandas as pd

# opcional: sentence-transformers (se não tiver, crie um fallback TF-IDF)
try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    _HAS_ST = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA

# opcional: UMAP/HDBSCAN
try:
    import umap
    _HAS_UMAP = True
except Exception:
    _HAS_UMAP = False

try:
    import hdbscan
    _HAS_HDBSCAN = True
except Exception:
    _HAS_HDBSCAN = False

from sklearn.cluster import KMeans

@dataclass
class Embedder:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 64
    device: Optional[str] = None  # "cuda" | "cpu" | None (auto)
    use_tfidf_fallback: bool = True
    _model: Optional[SentenceTransformer] = None
    _tfidf: Optional[TfidfVectorizer] = None

    def _ensure_model(self):
        if _HAS_ST and self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        if (not _HAS_ST) and self.use_tfidf_fallback and self._tfidf is None:
            self._tfidf = TfidfVectorizer(max_features=4096, ngram_range=(1,2))

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        texts = [t if isinstance(t, str) and t.strip() else "" for t in texts]
        self._ensure_model()
        if _HAS_ST and self._model is not None:
            emb = self._model.encode(texts, batch_size=self.batch_size, show_progress_bar=False, normalize_embeddings=True)
            return np.asarray(emb)
        # fallback TF-IDF (normalizado)
        X = self._tfidf.fit_transform(texts)
        return normalize(X).toarray()

@dataclass
class Clusterer:
    method: Literal["hdbscan","kmeans"] = "hdbscan"
    n_clusters: int = 10                 # só para kmeans
    min_cluster_size: int = 10           # hdbscan
    umap_dim: int = 2
    umap_neighbors: int = 15
    umap_min_dist: float = 0.1
    random_state: int = 42

    def reduce(self, X: np.ndarray) -> np.ndarray:
        if _HAS_UMAP:
            reducer = umap.UMAP(
                n_components=self.umap_dim,
                n_neighbors=self.umap_neighbors,
                min_dist=self.umap_min_dist,
                random_state=self.random_state,
                metric="cosine"
            )
            return reducer.fit_transform(X)
        # fallback: PCA
        pca = PCA(n_components=min(self.umap_dim, X.shape[1]))
        return pca.fit_transform(X)

    def cluster(self, X: np.ndarray) -> np.ndarray:
        if self.method == "kmeans":
            km = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init="auto")
            return km.fit_predict(X)
        # default: hdbscan (robusto a ruído)
        if _HAS_HDBSCAN:
            cl = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size, metric="euclidean")
            return cl.fit_predict(X)
        # fallback: kmeans
        km = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init="auto")
        return km.fit_predict(X)

def pairwise_cosine(A: np.ndarray, B: Optional[np.ndarray]=None) -> np.ndarray:
    return cosine_similarity(A, B)
