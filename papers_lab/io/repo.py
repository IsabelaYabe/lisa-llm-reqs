from __future__ import annotations
import pickle
import pandas as pd
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Iterator, Optional
from functools import singledispatch

from papers_lab.providers import Research, ResearchPaper
from logger import logger

def paper_to_dict(p: Any) -> Dict:
    """
    Convert a ResearchPaper or similar object to a dictionary. 
    """
    if is_dataclass(p):
        return asdict(p)
    if isinstance(p, dict):
        return p
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
        return [paper_to_df(p) for p in papers.values()]
    elif isinstance(papers, list):
        return [paper_to_df(p) for p in papers]
    return []

@extract_papers.register
def _(obj:Research) -> pd.DataFrame:
    """
    Extract papers from a Research object.
    """
    papers_map = obj.papers or {}
    rows = [paper_to_df(p) for p in papers_map.values()]
    if rows:
        return pd.json_normalize(rows, sep=".")
    return pd.DataFrame()

class PapersRepo:
    """
    Utility repository for persisting and loading research data (Research)
    and materializing papers into a DataFrame for EDA.
    """

    def save_research(self, research: Any, root: str | Path, name: str = "research", suffix: str = ".pkl") -> str:
        """
        Save research data to a pickle file.
        """
        root = Path(root) 
        root.mkdir(parents=True, exist_ok=True)
        
        base = name.strip().replace(" ", "_")
        path = root / f"{base}{suffix}"
        with open(path, "wb") as f:
            pickle.dump(research, f)
        return str(path)

    def load_research(self, path: str | Path) -> Any:
        """
        Load research data from a pickle file.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    def iter_dir(self,root: str | Path,*,pattern: str = "*.pkl",recursive: bool = True,
    ) -> Iterator[Any]:
        """
        Iterate over research files in a folder (and subfolders if recursive=True), loading .pkl files matching the pattern.
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
                    logger.error(f"Error loading {p}: {e}", exc_info=True)

    def load_dir(self,root: str | Path,*,pattern: str = "*.pkl",recursive: bool = True,limit: Optional[int] = None,
    ) -> list[Any]:
        """
        Load all .pkl files under root (optionally limited).
        """
        items: list[Any] = []
        for i, obj in enumerate(self.iter_dir(root, pattern=pattern, recursive=recursive), start=1):
            items.append(obj)
            if limit and i >= limit:
                break
        return items

    def flatten_papers(self, root: str | Path, *, pattern: str= "*.pkl", recursive: bool = True, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Flatten all papers from research files in a directory into a single DataFrame.
        """
        researches = self.load_dir(root, pattern=pattern, recursive=recursive, limit=limit)
        return self.flatten_papers(researches)