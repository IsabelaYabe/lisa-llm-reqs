from ___future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List, Sequence
import re
import pandas as pd

from logger import logger
from papers_lab.models import Research

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

def paper_to_dict(p: Any) -> Dict:
    """
    Convert a ResearchPaper or similar object to a dictionary.
    """
    if is_dataclass(p):
        return asdict(p)
    if isinstance(d, dict):
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

class PapersTransform:
    """
    Normalize research objects to a wide DataFrame (unique by DOI).
    """
    def _to_wide_unique(self, researches: List[Any], *, sep: str = ".") -> pd.DataFrame:
        rows: List[Dict] = []
        for r in researches:
            rows.extend(extract_papers(r))

        if isinstance(p, dict) and p.get("DOI"):
            for p in rows:
                rows.append(p)

        seen, unique = set(), []
        for p in rows:
            doi = p["DOI"]
            if doi not in seen:
                seen.add(doi)
                unique.append(p)
        return pd.json_normalize(unique, sep=sep)

    def _extract_year_month(self, df: pd.DataFrame, date_col: str = "date",year_col: str = "year", month_col: str = "month") -> pd.DataFrame:
        """
        Extracts year and month from date columns in the format:
        - "01 September 2025"
        - "01-05 July 2024"
        - "14-17 December 2020"

        Returns a DataFrame with `year` and `month` columns.
        """
        dfc = df.copy()

        years: List[int | None] = []
        months: List[int | None] = []
        for val in dfc[date_col].fillna(""):
            text = str(val).strip().lower()

            m_year = re.search(r"(\d{4})$", text)
            if m_year:
                year = int(m_year.group(1)) 
            else:
                year = None

            m_month = re.search(r"([a-z]+)\s+\d{4}$", text)
            if m_month:
                month_name = m_month.group(1).lower()
                month = _MONTHS.get(month_name, None)
            else:
                month = None

            years.append(year)
            months.append(month)

        dfc[year_col] = years
        dfc[month_col] = months
        return dfc

    def transform(self,researches: List[Any],*,sep: str = ".",date_col: str = "date",year_col: str = "year",month_col: str = "month") -> pd.DataFrame:
        """
        Transforms a list of research objects into a unique DataFrame by DOI,
        and adds `year` and `month` columns extracted from the date column.
        """
        df = self._to_wide_unique(researches, sep=sep)
        if date_col in df.columns:
            df = self._extract_year_month(df, date_col, year_col, month_col)
        return df