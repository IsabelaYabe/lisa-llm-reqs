from ___future__import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any, Dict, List
import pandas as pd
from papers_lab.models import Research

from logger import logger

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
    def to_wide_unique(self, researches: List[Any], *, sep: str = ".") -> pd.DataFrame:
        rows: List[Dict] = []
        for r in researches:
            rows.extend(extract_papers(r))

        rows = [p for p in rows if isinstance(p, dict) and p.get("DOI")]
        seen, unique = set(), []
        for p in rows:
            doi = p["DOI"]
            if doi not in seen:
                seen.add(doi)
                unique.append(p)
        return pd.json_normalize(unique, sep=sep)