from __future__ import annotations

from typing import List, Sequence, Optional, Literal
from sentence_transformers import SentenceTransformer
import numpy as np

# sentence-transformers/all-MiniLM-L12-v2 (384) | sentence-transformers/all-mpnet-base-v2 (768) | sentence-transformers/all-roberta-large-v1 (1024+)
class Embedder:
    def __init__(self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
        batch_size: int = 64,
        device: Optional[str] = None,  # "cuda" | "cpu" 
        normalize_embeddings: bool = False,
        show_progress_bar: bool = False,  
        convert_to_numpy: bool = True,    
        convert_to_tensor: bool = False,  
        max_seq_length: Optional[int] = None,    
        cache_folder: Optional[str] = None,  
        num_workers: int = 0,  
        precision: Literal["float32", "float16"] = "float32"
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.show_progress_bar = show_progress_bar
        self.convert_to_numpy = convert_to_numpy
        self.convert_to_tensor = convert_to_tensor
        self.max_seq_length = max_seq_length
        self.cache_folder = cache_folder 
        self.num_workers = num_workers
        self.precision = precision 
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """
        Get the underlying SentenceTransformer model, loading it if necessary.
        """
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device, cache_folder=self.cache_folder)
            if self.max_seq_length is not None:
                self._model.max_seq_length = int(self.max_seq_length)
            if self.precision == "float16" and self.device == "cuda":
                self._model = self._model.half()  

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        """
        txts: List[str] = [t if isinstance(t, str) and t.strip() else "" for t in texts]

        self._ensure_model()

        emb = self._model.encode(
            txts,
            batch_size=self.batch_size,
            show_progress_bar=self.show_progress_bar,
            convert_to_numpy=self.convert_to_numpy,
            convert_to_tensor=self.convert_to_tensor,
            normalize_embeddings=self.normalize_embeddings,
            num_workers=self.num_workers
        )
        return emb