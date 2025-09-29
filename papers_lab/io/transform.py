from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List, Sequence, Mapping
import re
import pandas as pd

from logger import logger
from providers.models import Research

_MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
           "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
_RE_YEAR  = re.compile(r"(\d{4})\s*$", re.IGNORECASE)
_RE_MONTH = re.compile(r"([A-Za-z]+)\s+\d{4}\s*$", re.IGNORECASE)
_DOI_RX   = re.compile(r"^10\.\S+", re.IGNORECASE)

def paper_to_dict(p: Any) -> Dict:
    """
    Convert a ResearchPaper or similar object to a dictionary.
    """
    if is_dataclass(p):
        return asdict(p)
    if isinstance(p, dict):
        return p
    logger.warning(f"Unexpected object: {type(p)}")
    return getattr(p, "__dict__", {"_value": p})

@singledispatch
def extract_papers(obj: Any) -> List[Dict]:
    """
    Extracts the 'papers' attribute from various types of research objects.
    """
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
    """
    Extract papers from a Research object.
    """
    papers_map = obj.papers or {}
    return [paper_to_dict(p) for p in papers_map.values()]

def _parse_year_month(text: str) -> tuple[int | None, int | None]:
    """
    Parse year and month from a date string.
    """
    if not text:
        return None, None
    s = str(text).strip().lower()
    
    m_year = _RE_YEAR.search(s)
    if m_year:
        year = int(m_year.group(1))
    else:
        year = None
    m_month = _RE_MONTH.search(s)
    if m_month:
        month = _MONTHS.get(m_month.group(1).lower())
    else:
        month = None
    return year, month

class PapersTransform:
    """
    Normalize research objects to a wide DataFrame (unique by DOI).
    """
    def __init__(self,*,doi_col:str="DOI",date_col:str="date",sep:str="."):
        self._doi_col  = doi_col
        self._date_col = date_col
        self._sep = sep

    @property
    def doi_col(self) -> str:
        return self._doi_col
    @property
    def date_col(self) -> str:
        return self._date_col
    @property
    def sep(self) -> str:
        return self._sep

    def _to_wide_unique(self,researches:List[Any]) -> pd.DataFrame:
        """
        Convert a list of research objects into a wide DataFrame, ensuring uniqueness by DOI.
        """
        p_rows: List[Dict] = []
        for r in researches:
            p_rows.extend(extract_papers(r))

        rows: List[Dict] = []
        for p in p_rows:
            if isinstance(p, dict) and p.get(self._doi_col):
                rows.append(p)

        seen: set[str] = set()
        unique: list[Dict] = []
        for p in rows:
            doi = str(p[self._doi_col]).strip()
            if doi not in seen:
                seen.add(doi)
                p[self._doi_col] = doi
                unique.append(p)
        
        for p in unique:
            date_val = p.get(self._date_col)
            if date_val is not None:
                year, month = _parse_year_month(date_val)
            else:
                year, month = None, None
            p["year"] = year
            p["month"] = month
            if year is not None and month is not None:
                p["year_month"] = f"{year:04d}-{month:02d}"
            else:
                p["year_month"] = None
        return pd.json_normalize(unique, sep=self._sep)
    
    def _validate_doi(self,df:pd.DataFrame,*,drop_invalid:bool=True) -> pd.DataFrame:
        """
        Validate DOI column in the DataFrame. 
        """
        dfc=df.copy()
        
        doi_column = dfc[self._doi_col].astype("string")
        is_valid_doi = doi_column.str.fullmatch(_DOI_RX.pattern, na=False, case=False)

        if drop_invalid:
            return dfc[is_valid_doi].reset_index(drop=True)
        else:
            return dfc.assign(doi_valid=is_valid_doi)
    
    def _select_rename(self,df:pd.DataFrame,*,keep:Sequence[str]|None=None,rename:Mapping[str,str]|None=None) -> pd.DataFrame:
        """
        Select and rename columns in the DataFrame.
        """
        dfx = df.copy()
        if rename:
            dfx = dfx.rename(columns=dict(rename))
        if keep:
            dfx = dfx[[c for c in keep if c in dfx.columns]]
        return dfx
    
    def _ensure_types(self,df:pd.DataFrame,schema:Mapping[str,str|type]) -> pd.DataFrame:
        """
        Ensure column types according to the schema (col: type).
        """
        dfc = df.copy()
        for col, typ in schema.items():
            if col in dfc.columns:
                try:
                    dfc[col] = dfc[col].astype(typ)
                except Exception as e:
                    logger.warning(f"Failed to convert column '{col}' to type '{typ}': {e}")
        return dfc
    
    def _add_counts(self,df:pd.DataFrame,*,count_cols:Sequence[str]=("keywords","authors")) -> pd.DataFrame:
        """
        Add count columns (e.g., n_keywords, n_authors) if the specified columns exist.
        """
        dfc = df.copy()
        for col in count_cols:
            if col in dfc.columns:
                count_col_name = f"n_{col}"
                dfc[count_col_name] = dfc[col].apply(lambda x: len(x) if isinstance(x, (list, tuple, set)) else 0)
        return dfc
    
    def transform(self,researches:List[Any],*,drop_invalid_doi:bool=True,keep:Sequence[str]|None=None,rename:Dict[str,str]|None=None,schema:Mapping[str,str|type]|None=None,count_cols:Sequence[str]=("keywords","authors")) -> pd.DataFrame:
        """
        Orchestrator method to transform research objects into a cleaned DataFrame.
        """
        df = self._to_wide_unique(researches)
        df = self._validate_doi(df, drop_invalid=drop_invalid_doi)
        df = self._select_rename(df, keep=keep, rename=rename)
        if schema:
            df = self._ensure_types(df, schema=schema)
        df = self._add_counts(df, count_cols=count_cols)
        return df