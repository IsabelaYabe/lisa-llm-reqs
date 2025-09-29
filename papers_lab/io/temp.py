from __future__ import annotations
from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List, Mapping, Sequence
import re, pandas as pd

from logger import logger
from providers.models import Research

_MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
           "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
_RE_YEAR  = re.compile(r"(\d{4})\s*$", re.IGNORECASE)
_RE_MONTH = re.compile(r"([A-Za-z]+)\s+\d{4}\s*$", re.IGNORECASE)
_DOI_RX   = re.compile(r"^10\.\S+", re.IGNORECASE)

def paper_to_dict(p: Any) -> Dict:
    if is_dataclass(p): return asdict(p)
    if isinstance(p, dict): return p
    logger.warning(f"Unexpected object: {type(p)}")
    return getattr(p, "__dict__", {"_value": p})

@singledispatch
def extract_papers(obj: Any) -> List[Dict]:
    if is_dataclass(obj): d = asdict(obj)
    elif isinstance(obj, dict): d = obj
    else: d = getattr(obj, "__dict__", {}) or {}
    papers = d.get("papers") or {}
    if isinstance(papers, dict):  return [paper_to_dict(p) for p in papers.values()]
    if isinstance(papers, list):  return [paper_to_dict(p) for p in papers]
    return []

@extract_papers.register
def _(obj: Research) -> List[Dict]:
    return [paper_to_dict(p) for p in (obj.papers or {}).values()]

def _parse_year_month(text: str) -> tuple[int|None, int|None]:
    if not text: return None, None
    s = str(text).strip().lower()
    mY = _RE_YEAR.search(s);  year  = int(mY.group(1)) if mY else None
    mM = _RE_MONTH.search(s); month = _MONTHS.get(mM.group(1).lower()) if mM else None
    return year, month

class PapersTransform:
    """Pipeline de transformações para DF 'largo' único por DOI."""

    def __init__(
        self,
        *,
        doi_col: str = "DOI",
        date_col: str = "date",
        sep: str = ".",
    ):
        self.doi_col  = doi_col
        self.date_col = date_col
        self.sep      = sep

    def to_wide_unique(self, researches: List[Any]) -> pd.DataFrame:
        rows: List[Dict] = []
        for r in researches:
            rows.extend(extract_papers(r))
        rows = [p for p in rows if isinstance(p, dict) and p.get(self.doi_col)]
        seen, unique = set(), []
        for p in rows:
            doi = str(p[self.doi_col]).strip()
            if doi not in seen:
                seen.add(doi)
                # normaliza DOI já aqui (opcional)
                p[self.doi_col] = doi
                unique.append(p)
        # enriquece com year/month (se houver 'date')
        for p in unique:
            y, m = _parse_year_month(p.get(self.date_col))
            p["year"]       = y
            p["month"]      = m
            p["year_month"] = f"{y:04d}-{m:02d}" if (y and m) else None
        return pd.json_normalize(unique, sep=self.sep)

    def validate_doi(self, df: pd.DataFrame, *, drop_invalid: bool = True) -> pd.DataFrame:
        dfx = df.copy()
        mask = dfx[self.doi_col].astype("string").str.fullmatch(_DOI_RX.pattern, case=False, na=False)
        return dfx[mask].reset_index(drop=True) if drop_invalid else dfx.assign(doi_valid=mask)

    def select_rename(self, df: pd.DataFrame, *, keep: Sequence[str] | None = None,
                      rename: Mapping[str, str] | None = None) -> pd.DataFrame:
        dfx = df.copy()
        if rename: dfx = dfx.rename(columns=dict(rename))
        if keep:   dfx = dfx[[c for c in keep if c in dfx.columns]]
        return dfx

    def ensure_types(self, df: pd.DataFrame, schema: Mapping[str, str | type]) -> pd.DataFrame:
        dfx = df.copy()
        for col, typ in schema.items():
            if col in dfx.columns:
                try:
                    dfx[col] = dfx[col].astype(typ)
                except Exception:
                    logger.warning(f"Type cast failed for {col} -> {typ}")
        return dfx

    def add_counts(self, df: pd.DataFrame, *, keywords_col="keywords", authors_col="authors") -> pd.DataFrame:
        dfx = df.copy()
        if keywords_col in dfx:
            dfx["n_keywords"] = dfx[keywords_col].apply(lambda x: len(x) if isinstance(x, (list, tuple, set)) else 0)
        if authors_col in dfx:
            dfx["n_authors"]  = dfx[authors_col].apply(lambda x: len(x) if isinstance(x, (list, tuple, set)) else 0)
        return dfx

    def transform(
        self,
        researches: List[Any],
        *,
        drop_invalid_doi: bool = True,
        keep: Sequence[str] | None = None,
        rename: Mapping[str, str] | None = None,
        schema: Mapping[str, str | type] | None = None,
        with_counts: bool = True,
    ) -> pd.DataFrame:
        """Retorna DF largo único por DOI, com year/month/year_month e ajustes opcionais."""
        df = self.to_wide_unique(researches)
        if drop_invalid_doi: df = self.validate_doi(df, drop_invalid=True)
        if with_counts:      df = self.add_counts(df)
        if rename or keep:   df = self.select_rename(df, keep=keep, rename=rename)
        if schema:           df = self.ensure_types(df, schema)
        return df
