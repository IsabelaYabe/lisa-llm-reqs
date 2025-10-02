from __future__ import annotations

from typing import List, Sequence, Optional, Literal
from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        batch_size: int = 64,
        device: Optional[str] = None,           # "cuda" | "cpu"
        normalize_embeddings: bool = False,
        show_progress_bar: bool = False,
        max_seq_length: Optional[int] = None,
        cache_folder: Optional[str] = None,
        precision: Literal["float32", "float16"] = "float32",
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.show_progress_bar = show_progress_bar
        self.max_seq_length = max_seq_length
        self.cache_folder = cache_folder
        self.precision = precision
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_folder,
            )
            if self.max_seq_length is not None:
                self._model.max_seq_length = int(self.max_seq_length)
            
            if self.precision == "float16" and (self.device or "").startswith("cuda"):
                try:
                    self._model = self._model.half()
                except Exception:
                    pass
        return self._model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        txts: List[str] = [t if isinstance(t, str) and t.strip() else "" for t in texts]
    
        _ = self.model  # garante que carregou

        emb = self.model.encode(
            txts,
            batch_size=self.batch_size,
            show_progress_bar=self.show_progress_bar,
            normalize_embeddings=self.normalize_embeddings,
        )

        # Normaliza saída: (N, D) np.ndarray
        if isinstance(emb, np.ndarray):
            return emb
        try:
            import torch
            if isinstance(emb, torch.Tensor):
                return emb.detach().cpu().numpy()
        except Exception:
            pass
        # às vezes pode vir list de vetores; empilha
        if isinstance(emb, list):
            return np.vstack(emb).astype(np.float32, copy=False)
        return np.asarray(emb)
