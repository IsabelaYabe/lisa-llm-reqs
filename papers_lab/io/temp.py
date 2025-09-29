from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List
import re
import pandas as pd

from logger import logger
from papers_lab.models import Research

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

# ---------------- helpers ----------------

def paper_to_dict(p: Any) -> Dict:
    """Convert a ResearchPaper or similar object to a dictionary."""
    if is_dataclass(p):
        return asdict(p)
    if isinstance(p, dict):
        return p
    logger.warning(f"Unexpected object: {type(p)}")
    return getattr(p, "__dict__", {"_value": p})

@singledispatch
def extract_papers(obj: Any) -> List[Dict]:
    """Extracts 'papers' from various research-like objects as list[dict]."""
    if is_dataclass(obj):
        d = asdict(obj)
    elif isinstance(obj, dict):
        d = obj
    else:
        d = getattr(obj, "__dict__", {}) or {}
    papers = d.get("papers") or {}
    if isinstance(papers, dict):
        return [paper_to_dict(p) for p in papers.values()]
    if isinstance(papers, list):
        return [paper_to_dict(p) for p in papers]
    return []

@extract_papers.register
def _(obj: Research) -> List[Dict]:
    """Fast path for Research objects."""
    return [paper_to_dict(p) for p in (obj.papers or {}).values()]

# regex: … <Month> <YYYY> no final da string (aceita "01-05 July 2024", "05 March 2024")
_RE_YEAR = re.compile(r"(\d{4})\s*$", re.IGNORECASE)
_RE_MONTH = re.compile(r"([A-Za-z]+)\s+\d{4}\s*$", re.IGNORECASE)

def _parse_year_month(text: str) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    s = str(text).strip().lower()
    m_year = _RE_YEAR.search(s)
    year = int(m_year.group(1)) if m_year else None
    m_month = _RE_MONTH.search(s)
    if m_month:
        month = _MONTHS.get(m_month.group(1).lower())
    else:
        month = None
    return year, month

# ---------------- transform ----------------

class PapersTransform:
    """
    Transform research objects into a wide DataFrame (unique by DOI),
    adding derived columns (year, month) parsed from 'date' se existir.
    """

    def _to_wide_unique(self, researches: List[Any], *, sep: str = ".") -> pd.DataFrame:
        # 1) extrai todos os papers como dicts
        rows: List[Dict] = []
        for r in researches:
            rows.extend(extract_papers(r))

        # 2) filtra quem tem DOI
        rows = [p for p in rows if isinstance(p, dict) and p.get("DOI")]

        # 3) dedup por DOI (mantém a primeira ocorrência)
        seen: set[str] = set()
        unique: list[Dict] = []
        for p in rows:
            doi = p["DOI"]
            if doi not in seen:
                seen.add(doi)
                unique.append(p)

        # 4) (otimizado) extrai year/month aqui, só para DOIs únicos
        for p in unique:
            date_val = p.get("date")
            y, m = _parse_year_month(date_val) if date_val is not None else (None, None)
            p["year"] = y
            p["month"] = m
            # opcional: facilitar groupby
            if y is not None and m is not None:
                p["year_month"] = f"{y:04d}-{m:02d}"
            else:
                p["year_month"] = None

        # 5) normaliza em DF “largo”
        return pd.json_normalize(unique, sep=sep)

    def transform(
        self,
        researches: List[Any],
        *,
        sep: str = ".",
    ) -> pd.DataFrame:
        """
        Retorna DataFrame largo único por DOI, já com colunas:
        - year (Int/None)
        - month (Int/None)
        - year_month (YYYY-MM ou None)
        """
        return self._to_wide_unique(researches, sep=sep)
