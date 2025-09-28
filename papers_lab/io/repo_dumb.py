from __future__ import annotations
import pickle
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Iterable, Iterator, Optional
from datetime import datetime

import pandas as pd


class Storage:
    """
    Repositório utilitário para persistir e carregar pesquisas (Research)
    e materializar papers em DataFrame para EDA.
    """

    # --------------------
    # Persistência simples
    # --------------------
    def save_research(
        self,
        research: Any,
        root: str | Path,
        name: str | None = None,
        *,
        with_timestamp: bool = True,
        suffix: str = ".pkl",
        protocol: int = pickle.HIGHEST_PROTOCOL,
    ) -> str:
        """
        Salva um objeto de pesquisa (dataclass ou dict) em pickle.
        - root: pasta raiz onde salvar
        - name: base do nome do arquivo (sem extensão). Se None, usa 'research'
        - with_timestamp: se True, acrescenta YYYYmmdd-HHMMSS ao nome
        - suffix: extensão (default .pkl)

        Retorna o caminho salvo (str).
        """
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)

        base = (name or "research").strip().replace(" ", "_")
        if with_timestamp:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            base = f"{base}_{ts}"
        path = root / f"{base}{suffix}"

        with open(path, "wb") as f:
            pickle.dump(research, f, protocol=protocol)
        return str(path)

    def load_research(self, path: str | Path) -> Any:
        """
        Carrega uma pesquisa (pickle).
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    # --------------------
    # Carga em lote
    # --------------------
    def iter_dir(
        self,
        root: str | Path,
        *,
        pattern: str = "*.pkl",
        recursive: bool = True,
    ) -> Iterator[Any]:
        """
        Itera pesquisas em uma pasta (e subpastas se recursive=True), carregando .pkl que casem o pattern.
        """
        root = Path(root)
        if not root.exists():
            return
        if recursive:
            globber = root.rglob
        else:
            globber = root.glob

        for p in globber(pattern):
            if p.is_file():
                try:
                    yield self.load_research(p)
                except Exception as e:
                    logger.error(f"Erro ao carregar {p}: {e}", exc_info=True)

    def load_dir(
        self,
        root: str | Path,
        *,
        pattern: str = "*.pkl",
        recursive: bool = True,
        limit: Optional[int] = None,
    ) -> list[Any]:
        """
        Carrega todos os .pkl sob root (opcionalmente limitado).
        """
        items: list[Any] = []
        for i, obj in enumerate(self.iter_dir(root, pattern=pattern, recursive=recursive), start=1):
            items.append(obj)
            if limit and i >= limit:
                break
        return items

    # --------------------
    # Flatten e DataFrame
    # --------------------²²
    @staticmethod³
    def _to_dict(obj: Any) -> Dict:
        """
        Converte dataclass -> dict; se já for dict, retorna como está.
        """
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, "__dataclass_fields__"):  
            return asdict(obj)
        if isinstance(obj, dict):
            return obj
        return getattr(obj, "__dict__", {"value": obj})

    def flatten_papers(self, research_list: List[Any]) -> List[Dict]:
        """
        Recebe uma lista de pesquisas (dict/dataclass) e concatena os papers
        (assumindo estrutura: research['papers'] é dict de {id: paper}).
        Retorna lista de dicts (papers).
        """
        papers: List[Dict] = []
        for r in research_list:
            r_dict = self._to_dict(r)
            papers_dict = r_dict.get("papers", {}) or {}
            for p in papers_dict.values():
                papers.append(self._to_dict(p))
        return papers

    def to_dataframe(self, research_list: List[Any]) -> pd.DataFrame:
        """
        Constrói um DataFrame de papers a partir de uma lista de pesquisas.
        Tenta manter colunas típicas: title, DOI, date, authors, keywords, source_url, etc.
        """
        rows = self.flatten_papers(research_list)
        df = pd.DataFrame(rows)

        # Normaliza tipos de colunas típicas (sem ser agressivo)
        for col in ("authors", "keywords"):
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x if isinstance(x, list) else ([] if pd.isna(x) else [x]))

        # Garante colunas esperadas, se faltarem
        for col in ("title", "DOI", "date", "abstract", "source_url"):
            if col not in df.columns:
                df[col] = pd.Series([None] * len(df))

        return df

    # --------------------
    # Utilidades para EDA
    # --------------------

    @staticmethod
    def dedupe_papers(df: pd.DataFrame, subset: str | list[str] = "DOI", keep: str = "first") -> pd.DataFrame:
        """
        Remove duplicatas no DataFrame de papers, por default usando DOI.
        """
        return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)

    @staticmethod
    def validate_research(obj: Any) -> bool:
        """
        Validação leve: checa os campos mínimos de uma pesquisa.
        """
        r = Storage._to_dict(obj)
        # campos desejáveis
        has_pubs = "publisher" in r
        has_papers = isinstance(r.get("papers"), (dict,))
        has_urls = isinstance(r.get("papers_urls"), (list,))
        return bool(has_pubs and has_papers and has_urls)