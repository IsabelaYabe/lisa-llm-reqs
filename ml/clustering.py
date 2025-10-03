from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any, Tuple, List
import numpy as np

try:
    import umap
    print("UMAP disponível.")
    _HAS_UMAP = True
except Exception:
    print("UMAP não disponível, usando PCA como fallback.")
    _HAS_UMAP = False

from sklearn.decomposition import PCA

from sklearn.cluster import KMeans
try:
    import hdbscan
    print("HDBSCAN disponível.")
    _HAS_HDBSCAN = True
except Exception:
    print("HDBSCAN não disponível, instale o pacote `hdbscan` para usar este método.")
    _HAS_HDBSCAN = False

from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

from logger import logger

@dataclass
class Clusterer:
    method: Literal["kmeans", "hdbscan"] = "kmeans"
    n_clusters: int = 8
    kmeans_init: str = "k-means++"
    kmeans_n_init: int | str = "auto"
    random_state: int = 42
    min_cluster_size: int = 10
    min_samples: Optional[int] = None
    cluster_selection_epsilon: float = 0.0
    reducer: Literal["umap", "pca", "none"] = "umap"
    n_components: int = 2
    umap_neighbors: int = 15
    umap_min_dist: float = 0.1
    _kmeans: Optional[KMeans] = None
    _hdb: Optional["hdbscan.HDBSCAN"] = None

    def reduce(self, X: np.ndarray) -> np.ndarray:
        if self.reducer == "none":
            logger.info("Reducer is 'none', returning original data.")
            return X
        if self.reducer == "umap":
            logger.info("Reducing dimensions with UMAP.")
            reducer = umap.UMAP(
                n_components=self.n_components,
                n_neighbors=self.umap_neighbors,
                min_dist=self.umap_min_dist,
                random_state=self.random_state,
                metric="cosine",
            )
            return reducer.fit_transform(X)
        
        logger.info("Reducing dimensions with PCA.")
        pca = PCA(n_components=min(self.n_components, X.shape[1]), random_state=self.random_state)
        return pca.fit_transform(X)

    def fit(self, X: np.ndarray) -> "Clusterer":
        if self.method == "kmeans":
            logger.info(f"Fitting KMeans with n_clusters={self.n_clusters}.")
            self._kmeans = KMeans(
                n_clusters=self.n_clusters,
                init=self.kmeans_init,
                n_init=self.kmeans_n_init,
                random_state=self.random_state,
            )
            self._kmeans.fit(X)
            return self

        if not _HAS_HDBSCAN:
            logger.error("HDBSCAN is not available. Install the `hdbscan` package to use this method.")
            raise RuntimeError("hdbscan not available — install `hdbscan` or use method='kmeans'.")

        logger.info(f"Fitting HDBSCAN with min_cluster_size={self.min_cluster_size}.")
        self._hdb = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            metric="euclidean",
        )
        self._hdb.fit(X)
        return self

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        if self.method == "hdbscan":
            if self._hdb is None:
                raise RuntimeError("HDBSCAN model must be fitted before calling `fit_predict`.")
            logger.info("Returning HDBSCAN labels.")
            return self._hdb.labels_
        
        if self.method == "kmeans":
            if self._kmeans is None:
                raise RuntimeError("KMeans model must be fitted before calling `fit_predict`.")
            logger.info("Returning KMeans labels.")
            return self._kmeans.labels_

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.method == "kmeans":
            logger.info("Predicting clusters with KMeans.")
            if self._kmeans is None:
                raise RuntimeError("KMeans model must be fitted before calling `predict`.")
            return self._kmeans.predict(X)
        
        if self.method == "hdbscan":
            logger.info("Predicting clusters with HDBSCAN.")
            if self._hdb is None:
                raise RuntimeError("HDBSCAN model must be fitted before calling `predict`.")
            if hasattr(hdbscan, "approximate_predict"):
                labels, _ = hdbscan.approximate_predict(self._hdb, X)
                return labels
            else:
                raise RuntimeError("HDBSCAN `approximate_predict` is not available in the installed version.")
        
        raise ValueError(f"Unsupported clustering method: {self.method}")

    def summary(self, labels: np.ndarray) -> Dict[Any, int]:
        uniq, cnt = np.unique(labels, return_counts=True)
        return dict(zip(uniq.tolist(), cnt.tolist()))

    def silhouette(self, X: np.ndarray, labels: np.ndarray) -> float | None:
        labs = labels[labels != -1]
        Xv = X[labels != -1]
        if len(np.unique(labs)) < 2:
            return None
        return float(silhouette_score(Xv, labs, metric="cosine"))

    def centroids(self, X: np.ndarray, labels: np.ndarray) -> Dict[int, np.ndarray]:
        """
        For KMeans: returns centroids.
        For HDBSCAN: returns approximate 'medoids' (points closest to the cluster center).
        """
        out: Dict[int, np.ndarray] = {}
        valid = labels != -1
        for c in np.unique(labels[valid]):
            idx = np.where(labels == c)[0]
            if idx.size == 0:
                continue
            Xc = X[idx]
            if self.method == "kmeans" and self._kmeans is not None:
                out[int(c)] = self._kmeans.cluster_centers_[int(c)]
            else:
                center = Xc.mean(axis=0, keepdims=True)
                # medoide = ponto mais próximo do "centro" (média)
                d = ((Xc - center)**2).sum(axis=1)
                out[int(c)] = Xc[np.argmin(d)]
        return out

    def exemplars(self, X: np.ndarray, labels: np.ndarray, k: int = 5) -> Dict[int, List[int]]:
        """
        Indices of the k items closest to the centroid/medoid per cluster.
        """
        centers = self.centroids(X, labels)
        res: Dict[int, List[int]] = {}
        for c, center in centers.items():
            idx = np.where(labels == c)[0]
            Xc = X[idx]
            d = ((Xc - center)**2).sum(axis=1)  # euclidiana
            ord_ = np.argsort(d)[:k]
            res[c] = idx[ord_].tolist()
        return res

    def plot_2d(self, X: np.ndarray, labels: np.ndarray, title: str = "Clusters (2D)"):
        """
        Plot clusters in 2D using scatter plot.
        """
        Z = self.reduce(X) if X.shape[1] > 2 else X
        uniq = np.unique(labels)
        colors = plt.cm.tab20(np.linspace(0, 1, max(len(uniq), 3)))
        plt.figure(figsize=(8, 6))
        for i, c in enumerate(uniq):
            m = labels == c
            lab = f"cluster {c}" if c != -1 else "ruído (-1)"
            plt.scatter(Z[m, 0], Z[m, 1], s=20, color=colors[i % len(colors)], label=lab, alpha=0.8)
        plt.legend()
        plt.title(title)
        plt.tight_layout()
        plt.show()
