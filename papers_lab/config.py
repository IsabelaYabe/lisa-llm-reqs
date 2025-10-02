"""
Configurações e constantes para o módulo papers_lab.
"""
from pathlib import Path
import re

# ==================== PATHS E DIRETÓRIOS ====================
PAPERS_LAB_ROOT = Path(__file__).parent
PROJECT_ROOT = PAPERS_LAB_ROOT.parent
PAPERS_DIR = PROJECT_ROOT / "papers"
OUTPUTS_DIR = PROJECT_ROOT / "outputs" 
CACHE_DIR = PROJECT_ROOT / "cache"

# ==================== REGEX PATTERNS ====================
DOI_PATTERN = re.compile(r"^10\.\S+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"(\d{4})\s*$", re.IGNORECASE)
MONTH_PATTERN = re.compile(r"([A-Za-z]+)\s+\d{4}\s*$", re.IGNORECASE)
YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")

# ==================== MAPEAMENTOS ====================
MONTH_MAPPING = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

# ==================== DADOS E TRANSFORMAÇÕES ====================
# Colunas padrão esperadas nos DataFrames
DEFAULT_COLUMNS = {
    "required": ["DOI", "title", "authors"],
    "optional": ["abstract", "keywords", "year", "month", "date", "venue"],
    "generated": ["year_month", "n_authors", "n_keywords", "doi_valid"]
}

# Configurações de transformação
TRANSFORM_DEFAULTS = {
    "doi_col": "DOI",
    "date_col": "date", 
    "year_col": "year",
    "month_col": "month",
    "sep": ".",
    "drop_invalid_doi": True
}

# ==================== ANÁLISE EXPLORATÓRIA ====================
# Valores padrão para análises
EDA_DEFAULTS = {
    "top_n": 20,
    "top_k": 15,
    "max_items_viz": 50,
    "cooccurrence_top_n": 50,
    "trends_top_k": 15
}

# ==================== VISUALIZAÇÃO ====================
VIZ_DEFAULTS = {
    "cmap_name": "Wistia",
    "figsize": (10, 6),
    "title_fontsize": 14,
    "label_fontsize": 11,
    "grid": True,
    "value_label_fmt": "{:.0f}"
}

# Colormaps por tipo de análise
COLORMAPS = {
    "papers": ["Wistia", "YlOrRd", "Blues", "plasma"],
    "heatmap": ["viridis", "plasma", "inferno"],
    "network": ["tab10", "Set3", "Paired"],
    "timeline": ["coolwarm", "RdYlBu", "seismic"]
}

# ==================== I/O E FORMATOS ====================
SUPPORTED_FORMATS = {
    "input": [".pkl", ".json", ".csv"],
    "output": [".csv", ".json", ".xlsx", ".pkl"]
}

# Configurações de Storage
STORAGE_DEFAULTS = {
    "pattern": "*.pkl",
    "recursive": True,
    "encoding": "utf-8"
}

# ==================== PROVIDERS ====================
PROVIDER_CONFIGS = {
    "ieee": {
        "base_url": "https://ieeexploreapi.ieee.org/api/v1/search/articles",
        "rate_limit": 200,  # requests per hour
        "batch_size": 25,
        "max_results": 200
    },
    "acm": {
        "base_url": "https://dl.acm.org/action/doSearch", 
        "rate_limit": 100,
        "batch_size": 20,
        "max_results": 100
    }
}

# ==================== VALIDAÇÃO ====================
VALIDATION_RULES = {
    "doi": {
        "pattern": DOI_PATTERN,
        "required": True
    },
    "year": {
        "min_value": 1990,
        "max_value": 2030,
        "type": int
    },
    "month": {
        "min_value": 1,
        "max_value": 12,
        "type": int
    },
    "authors": {
        "max_count": 50,
        "type": list
    },
    "keywords": {
        "max_count": 20,
        "type": list
    }
}

# Limites de processamento
PROCESSING_LIMITS = {
    "max_papers_per_batch": 1000,
    "max_text_length": 10000,
    "max_memory_mb": 1024
}

# ==================== ESTATÍSTICAS E MÉTRICAS ====================
STATS_CONFIG = {
    "percentiles": [0.25, 0.5, 0.75, 0.9, 0.95],
    "include_types": ["number", "object", "datetime"],
    "float_format": "{:.3f}",
    "date_format": "%Y-%m-%d"
}

# ==================== CLUSTERING E ML ====================
ML_DEFAULTS = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "batch_size": 64,
    "max_seq_length": 384,
    "normalize_embeddings": True,
    
    # UMAP
    "umap_n_components": 2,
    "umap_n_neighbors": 15,
    "umap_min_dist": 0.1,
    "umap_metric": "cosine",
    
    # HDBSCAN
    "hdbscan_min_cluster_size": 10,
    "hdbscan_metric": "euclidean",
    
    # K-Means
    "kmeans_n_clusters": 10,
    "kmeans_random_state": 42
}

# ==================== LOGGING ====================
LOGGING_CONFIG = {
    "format": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "level": "INFO",
    "file": "papers_lab.log"
}
