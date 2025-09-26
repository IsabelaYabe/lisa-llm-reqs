"""
Pipeline para agrupar palavras-chave de papers por tópicos e gerar gráfico.

Principais melhorias:
- Organização em funções pequenas e reutilizáveis
- Tipagem e docstrings
- Validações, mensagens claras de erro e logging básico
- Normalização e limpeza de palavras com utilitários dedicados
- Uso correto de X normalizado no HDBSCAN
- Parametrização (pastas de entrada, modelo, min_cluster_size)
- Função main() com bloco if __name__ == "__main__"

Dependências: pandas, sentence-transformers, scikit-learn, hdbscan, matplotlib
"""
from __future__ import annotations

import os
import re
import pickle
import logging
import unicodedata
from dataclasses import asdict
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple, Union

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import hdbscan
import matplotlib.pyplot as plt
from collections import Counter
import itertools

# ==========================
# Configuração de logging
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ==========================
# Constantes e mapeamentos
# ==========================
DEFAULT_CLUSTER_NAMES: Dict[int, str] = {
    -1:  "Ruído",
    0:   "Dependência & Correlação",
    1:   "Cenários de Uso",
    2:   "Fluxo de Controle & Grafos",
    3:   "Diagramas de Classe & Estrutura",
    4:   "Avaliação & Assessment",
    5:   "Recuperação & Extração de Informação",
    6:   "Análise de Tarefas",
    7:   "Teste & Depuração de Software",
    8:   "Tradução Automática / Machine Translation",
    9:   "Sistemas Industriais & Ciberfísicos",
    10:  "Frameworks & Modelagem OO",
    11:  "Semântica & Similaridade",
    12:  "Engenharia Reversa",
    13:  "Visualização & Ferramentas Visuais",
    14:  "Inteligência Artificial & Aprendizado de Máquina",
    15:  "Manutenção de Software",
    16:  "Processamento de Linguagem Natural (NLP)",
    17:  "Grandes Modelos de Linguagem (LLMs)",
    18:  "Modelagem & Sistemas de Modelos",
    19:  "UML (Unified Modeling Language)",
    20:  "Engenharia de Software (Geral)",
    21:  "Educação em Computação & Programação",
    22:  "Sumarização & Representação de Código",
    23:  "Java & Linguagens de Programação",
}

_PUNCT_TBL = str.maketrans("", "", r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")

# ==========================
# Utilitários de texto
# ==========================

def norm_token(s: str) -> str:
    """Normaliza string (NFKC, minúsculas, remove pontuação e espaços extras)."""
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = s.translate(_PUNCT_TBL)
    s = re.sub(r"\s+", " ", s)
    return s


def to_token_set(words: Union[Iterable[str], None]) -> set[str]:
    if not words:
        return set()
    return {norm_token(w) for w in words if isinstance(w, str) and w.strip()}

# ==========================
# Leitura e preparação dos dados
# ==========================

def extract_researches_results(root_dir: Union[str, os.PathLike]) -> List[dict]:
    """Varre um diretório e carrega .pkl contendo um dataclass com atributo `papers`.

    Retorna uma lista de dicts (via asdict) com a estrutura do objeto carregado.
    """
    root_dir = os.fspath(root_dir)
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Diretório não existe: {root_dir}")

    researches: List[dict] = []
    for fname in os.listdir(root_dir):
        path = os.path.join(root_dir, fname)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as f:
                obj = pickle.load(f)
            research = asdict(obj) if hasattr(obj, "__dataclass_fields__") else obj
            if not isinstance(research, Mapping):
                logger.warning("Ignorando arquivo não mapeável: %s", fname)
                continue
            researches.append(research)
        except Exception as e:
            logger.exception("Falha ao carregar %s: %s", fname, e)
    logger.info("Pesquisas carregadas: %d (%s)", len(researches), root_dir)
    return researches


def extract_papers(researches: List[dict]) -> List[dict]:
    """Extrai os papers do campo `papers` (dict) de cada pesquisa."""
    papers: List[dict] = []
    for res in researches:
        papers_dict = res.get("papers", {}) if isinstance(res, Mapping) else {}
        if isinstance(papers_dict, Mapping):
            for p in papers_dict.values():
                if isinstance(p, Mapping):
                    papers.append(dict(p))
    logger.info("Total de papers extraídos: %d", len(papers))
    return papers


def build_clean_dataframe(papers: List[dict]) -> pd.DataFrame:
    """Monta DataFrame e remove duplicados por DOI."""
    df = pd.DataFrame(papers)
    if "DOI" in df.columns:
        df = df.drop_duplicates(subset="DOI", keep="first").reset_index(drop=True)
    else:
        df = df.drop_duplicates(subset="title", keep="first").reset_index(drop=True)
        logger.warning("Coluna DOI ausente; deduplicando por título.")
    return df


def compute_keyword_counts(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Explode a coluna `keywords` (listas) e conta frequências."""
    valid_keywords = [k for k in df_clean.get("keywords", []) if isinstance(k, list)]
    flat_keywords = list(itertools.chain.from_iterable(valid_keywords))
    counts = Counter(flat_keywords)
    df_kw = pd.DataFrame(list(counts.items()), columns=["keyword", "count"])
    df_kw = df_kw.sort_values("count", ascending=False).reset_index(drop=True)
    return df_kw

# ==========================
# Embeddings e clustering
# ==========================

def embed_keywords(df_kw: pd.DataFrame, model_name: str = "all-MiniLM-L6-v2") -> Tuple[pd.DataFrame, "np.ndarray"]:
    """Cria embeddings para as keywords e retorna matriz normalizada."""
    model = SentenceTransformer(model_name)
    X = model.encode(df_kw["keyword"].tolist(), show_progress_bar=True)
    Xn = normalize(X)
    return df_kw, Xn


def cluster_keywords(df_kw: pd.DataFrame, Xn, min_cluster_size: int = 3) -> Tuple[pd.DataFrame, Dict[int, List[str]]]:
    """Roda HDBSCAN e retorna df com rótulo de cluster e dicionário id->termos."""
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
    labels = clusterer.fit_predict(Xn)
    df_kw = df_kw.copy()
    df_kw["cluster"] = labels

    clusters: Dict[int, List[str]] = (
        df_kw.groupby("cluster")["keyword"].apply(list).to_dict()
    )
    logger.info("Clusters encontrados: %d (inclui -1)", len(clusters))
    return df_kw, clusters

# ==========================
# Rotulagem de tópicos por paper
# ==========================

def label_topics_for_paper(keywords: List[str], clusters_dict: Mapping[int, List[str]]) -> List[Union[int, str]]:
    """Mapeia as keywords do paper aos ids de clusters (ou "Other" se nenhum casar)."""
    keyset = to_token_set(keywords)
    hits: List[Union[int, str]] = []
    for cid, terms in clusters_dict.items():
        termset = to_token_set(terms)
        if keyset & termset:
            hits.append(cid)
    return hits or ["Other"]


def assign_topics_to_papers(df_clean: pd.DataFrame, clusters: Mapping[int, List[str]]) -> pd.DataFrame:
    df = df_clean.copy()
    df["topic_ids"] = df["keywords"].apply(lambda ks: label_topics_for_paper(ks if isinstance(ks, list) else [], clusters))
    return df

# ==========================
# Visualização
# ==========================

def plot_topic_counts(tp: pd.DataFrame, cluster_names: Mapping[int, str] = DEFAULT_CLUSTER_NAMES, title: str = "Papers por Tópico") -> None:
    """Gera gráfico de barras horizontais com contagem de papers por tópico."""
    tp = tp[tp["topic_ids"] != "Other"].copy()
    topic_counts = tp.groupby("topic_ids").size().rename("n").reset_index()
    topic_counts["topic_name"] = topic_counts["topic_ids"].map(cluster_names)
    topic_counts = topic_counts.sort_values("n", ascending=True)

    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    bars = ax.barh(topic_counts["topic_name"], topic_counts["n"])  # não fixa cor

    plt.title(title, pad=20)
    plt.xlabel("Quantidade de Papers")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f"{width:.0f}", va="center", ha="left", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.show()

# ==========================
# Execução de ponta-a-ponta
# ==========================

def run_pipeline(
    dir_acm: Union[str, os.PathLike] = os.path.join("papers", "acm"),
    dir_ieee: Union[str, os.PathLike] = os.path.join("papers", "ieee"),
    model_name: str = "all-MiniLM-L6-v2",
    min_cluster_size: int = 3,
    cluster_names: Mapping[int, str] = DEFAULT_CLUSTER_NAMES,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, List[str]]]:
    """Executa o fluxo completo e retorna:
    - df_clean: DataFrame dos papers (deduplicado)
    - df_kw: DataFrame de keywords com rótulo de cluster
    - clusters: dict id->lista de termos do cluster
    """
    # Carrega pesquisas das duas fontes
    researches_acm = extract_papers(extract_researches_results(dir_acm))
    researches_ieee = extract_papers(extract_researches_results(dir_ieee))

    papers = list(researches_acm) + list(researches_ieee)
    if not papers:
        logger.warning("Nenhum paper encontrado. Verifique os diretórios.")

    # Monta DataFrame de papers
    df_clean = build_clean_dataframe(papers)

    # Conta keywords
    df_kw = compute_keyword_counts(df_clean)

    # Embeddings e clustering
    df_kw, Xn = embed_keywords(df_kw, model_name=model_name)
    df_kw, clusters = cluster_keywords(df_kw, Xn, min_cluster_size=min_cluster_size)

    # Atribui tópicos aos papers
    df_with_topics = assign_topics_to_papers(df_clean, clusters)

    # DataFrame "explodido" por tópico para contar facilmente
    tp = df_with_topics.explode("topic_ids", ignore_index=True)

    # Plot
    plot_topic_counts(tp, cluster_names=cluster_names)

    return df_with_topics, df_kw, clusters


if __name__ == "__main__":
    # Execução padrão com diretórios "papers/acm" e "papers/ieee"
    run_pipeline()