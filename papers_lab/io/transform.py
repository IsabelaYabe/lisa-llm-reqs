from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List, Sequence, Mapping
import re
import pandas as pd
import unicodedata

from logger import logger
from ..providers.models import Research

from ..config import MONTH_MAPPING, YEAR_PATTERN, MONTH_PATTERN, DOI_PATTERN 

def _paper_to_dict(p: Any) -> Dict:
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
def _extract_papers(obj: Any) -> List[Dict]:
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
        return [_paper_to_dict(p) for p in papers.values()]
    if isinstance(papers, list):
        return [_paper_to_dict(p) for p in papers]
    return []

@_extract_papers.register
def _(obj: Research) -> List[Dict]:
    """
    Extract papers from a Research object.
    """
    papers_map = obj.papers or {}
    return [_paper_to_dict(p) for p in papers_map.values()]

def _parse_year_month(text: str) -> tuple[int | None, int | None]:
    """
    Parse year and month from a date string.
    """
    if not text:
        return None, None
    s = str(text).strip().lower()
    
    m_year = YEAR_PATTERN.search(s)
    if m_year:
        year = int(m_year.group(1))
    else:
        year = None
    m_month = MONTH_PATTERN.search(s)
    if m_month:
        month = MONTH_MAPPING.get(m_month.group(1).lower())
    else:
        month = None
    return year, month

def _normalize_keyword(word: str) -> str | None:
    if word is None:
        return None
    s = str(word)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s or None

def _to_list(x: Any) -> list[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return [str(e) for e in x]
    return [str(x)]

def _norm_list(x: Any) -> list[str]:
    items = _to_list(x)
    norm = {_normalize_keyword(i) for i in items}
    norm.discard(None)
    return sorted(norm)

def _count_words(txt):
    if not isinstance(txt, str):
        return 0
    return len(str(txt).split())

class PaperTransform:
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
            p_rows.extend(_extract_papers(r))

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
        is_valid_doi = doi_column.str.fullmatch(DOI_PATTERN.pattern, na=False, case=False)

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

    def _add_word_counts(self, df, cols: Sequence[str] = ["abstract"]) -> pd.DataFrame:
        """
        Count the number of words in the specified text column.
        Returns a Series aligned with the DataFrame index.
        """
        dfc = df.copy()
        for col in cols:
            if col in dfc.columns:
                dfc[f"n_{col}_words"] = dfc[col].apply(_count_words)
        
        return dfc

    def _add_counts(self,df:pd.DataFrame,*,count_cols:Sequence[str]=("keywords","authors","abstract")) -> pd.DataFrame:
        """
        Add count columns (e.g., n_keywords, n_authors) if the specified columns exist.
        """
        dfc = df.copy()
        for col in count_cols:
            if col in dfc.columns:
                count_col_name = f"n_{col}"
                dfc[count_col_name] = dfc[col].apply(lambda x: len(x) if isinstance(x, (list, tuple, set)) else 0)
        return dfc
        
    def _normalize_keywords(self,df: pd.DataFrame,*,keywords_col: str = "keywords",out_list_col: str = "keywords_norm") -> pd.DataFrame:
        """ 
        Normalize keywords in the specified column, creating a new column:
        - out_list_col: list of normalized keywords
        """
        dfc = df.copy()
        if keywords_col not in dfc.columns:
            return dfc

        dfc[out_list_col] = dfc[keywords_col].apply(_norm_list)
        return dfc

    def transform(self,
        researches:List[Any],
        *,
        drop_invalid_doi:bool=True,
        keep:Sequence[str]|None=None,
        rename:Dict[str,str]|None=None,
        schema:Mapping[str,str|type]|None=None,
        count_cols:Sequence[str]=("keywords","authors"),
        normalize_keywords:bool=True,
        keywords_col:str="keywords",
        out_keywords_col:str="keywords_norm",
        count_word_cols:Sequence[str]=["abstract"]
        ) -> pd.DataFrame:
        """
        Orchestrator method to transform research objects into a cleaned DataFrame.
        """
        df = self._to_wide_unique(researches)
        df = self._validate_doi(df, drop_invalid=drop_invalid_doi)
        
        if normalize_keywords:
            df = self._normalize_keywords(df, keywords_col=keywords_col, out_list_col=out_keywords_col)
        
        df = self._select_rename(df, keep=keep, rename=rename)
        
        if schema:
            df = self._ensure_types(df, schema=schema)

        cols_to_count = list(count_cols) if count_cols else []
        if normalize_keywords and out_keywords_col not in cols_to_count and out_keywords_col in df.columns:
            cols_to_count.append(out_keywords_col)
        df = self._add_counts(df, count_cols=tuple(cols_to_count))
        
        if count_word_cols:
            df = self._add_word_counts(df, cols=count_word_cols)
        return df