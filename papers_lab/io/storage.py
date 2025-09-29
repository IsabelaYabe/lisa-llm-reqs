from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Iterator, Optional, List
from logger import logger

class Storage:
    """
    Utility repository for persisting and loading research data.        
    """

    def save(self, research: Any, root: str | Path, name: str = "research", suffix: str = ".pkl") -> str:
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

    def load(self, path: str | Path) -> Any:
        """
        Load research data from a pickle file.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    def iter_dir(self,root: str | Path,*,pattern: str = "*.pkl",recursive: bool = True) -> Iterator[Any]:
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
                    yield self.load(p)
                except Exception as e:
                    logger.error(f"Error loading {p}: {e}", exc_info=True)

    def load_dir(self,root: str | Path,*,pattern: str = "*.pkl",recursive: bool = True,limit: Optional[int] = None) -> list[Any]:
        """
        Load all .pkl files under root (optionally limited).
        """
        items: List[Any] = []
        for i, obj in enumerate(self.iter_dir(root, pattern=pattern, recursive=recursive), start=1):
            items.append(obj)
            if limit and i >= limit:
                break
        return items