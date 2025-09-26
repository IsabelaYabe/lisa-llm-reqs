from __future__ import annotations
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

class PapersRepo:
    """
    Persists and retrieves research data using pickle serialization.
    """

    def save_research(self, research: Any, root: str | Path, name: str) -> str:
        """
        Save research data to a pickle file.
        """
        root = Path(root) 
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{name}.pkl"
        with open(path, "wb") as f:
            pickle.dump(research, f)
        return str(path)

    def load_research(self, path: str | Path) -> Any:
        """
        Load research data from a pickle file.
        """
        with open(path, "rb") as f:
            return pickle.load(f)

    def flatten_papers(self, research_list: List[Dict]) -> List[Dict]:
        """
        Flatten a list of research dictionaries into a single list of paper dictionaries.
        """
        papers: List[Dict] = []
        for r in research_list:
            r_dict = asdict(r) if hasattr(r, "__dataclass_fields__") else r
            for p in r_dict.get("papers", {}).values():
                papers.append(p)
        return papers
