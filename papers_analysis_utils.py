from __future__ import annotations

import os, pickle, math, ast, re, unicodedata
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Callable, Any, Iterable

import pandas as pd
from logger import logger

def show_df(title: str, df: pd.DataFrame, max_rows: int = 10) -> None:
    """
    Print a titled preview of a DataFrame.
    """    
    print(f"\n[{title}] ({len(df)} rows)")
    print(df.head(max_rows))

def normalize_text(s: Any) -> str | None:
    """
    Lowercase, NFKC, strip, collapse spaces; remove punctuation. Non-str → None.
    """
    if not isinstance(s, str):
        return None
    s = unicodedata.normalize("NFKC", s).casefold().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None

def normalize_col(df: pd.DataFrame, col: str, out: str | None = None, fn: Callable[[Any], Any] = normalize_text) -> pd.DataFrame:
    """
    Create a normalized column from 'col' using 'fn' (defaults to normalize_text).
    """
    out = out or f"{col}_norm"
    df[out] = df[col].apply(fn)
    return df

def check_col(df: pd.DataFrame, col: str, 
    *, show_rows: bool = True, max_rows: int = 10, 
    normalizer: Callable[[Any], Any] | None = None, 
    return_clean_data: bool = False) 
    -> pd.DataFrame | None:
    """
    Check consistency of a column in a DataFrame of papers.
    
    It looks for:
      - Duplicated rows
      - Unique rows
      - Rows without value
      - Clean DataFrame with duplicates removed (if requested)
    """
    dfc = df.copy()
    
    target = col
    if normalizer is not None:
        target = f"{col}_norm"
        dfc[target] = dfc[col].apply(normalizer)
    
    duplicated_rows = dfc[dfc.duplicated(subset=target, keep=False)].sort_values([target])
    df_clean = dfc.drop_duplicates(subset=target, keep="first").reset_index(drop=True)
    missing = dfc[dfc[target].isna()].copy()

    summary = {
        "total_rows": len(dfc),
        "duplicated_rows": len(duplicated_rows),
        "unique_values": dfc[target].nunique(dropna=True),
        "clean_rows": len(df_clean),
        "missing_rows": len(missing),
        "column_checked": target
    }
    print(
        f"Total: {summary['total_rows']} | Duplicated: {summary['duplicated_rows']} | "
        f"Unique values: {summary['unique_values']} | Clean rows: {summary['clean_rows']} | "
        f"Missing: {summary['missing_rows']} | Column: {summary['column_checked']}"
    )
    if show_rows:
        show_df(f"Duplicated by {target}", dupe[[col] + ([target] if target != col else [])], max_rows)
        show_df(f"Missing in {target}", missing[[col] + ([target] if target != col else [])], max_rows)
    
    if return_clean:
        return clean  
    return None

def check_rows_conflicts(df: pd.DataFrame, col_a: str, col_b: str, *, normalize_a: Callable[[Any], Any] | None = None, normalize_b: Callable[[Any], Any] | None = None, show_rows: bool = True, max_rows: int = 20, return_data: bool = True) -> dict[str, Any] | None:
    """
    Check for conflicts between col_a and col_b in the DataFrame.
    It looks for:
        - Same col_0 with different col_1
        - Same col_1 with different col_0
    Prints the results of the checks.
    """
    dfc = df.copy()
    a = col_a
    b = col_b

    if normalize_a is not None:
        a = f"{col_a}_norm"
        dfc[a] = dfc[col_a].apply(normalize_a)
    if normalize_b is not None:
        b = f"{col_b}_norm"
        dfc[b] = dfc[col_b].apply(normalize_b)

    dup_a = dfc[dfc.duplicated(subset=a, keep=False)]
    same_a_diff_b = dup_a.groupby(a).filter(lambda x: x[b].nunique(dropna=True) > 1).sort_values([a, b])

    dup_b = dfc[dfc.duplicated(subset=b, keep=False)]
    same_b_diff_a = dup_b.groupby(b).filter(lambda x: x[a].nunique(dropna=True) > 1).sort_values([b, a])

    summary = {
        "total_rows": len(dfc),
        f"dup_{col_a}_rows": len(dup_a),
        f"same_{col_a}_diff_{col_b}": len(same_a_diff_b),
        f"dup_{col_b}_rows": len(dup_b),
        f"same_{col_b}_diff_{col_a}": len(same_b_diff_a),
        "used_columns": {"A": a, "B": b}
    }

    print(
        f"Total: {summary['total_rows']} | Duplicated {col_a} rows: {summary[f'dup_{col_a}_rows']} | "
        f"Same {col_a} different {col_b}: {summary[f'same_{col_a}_diff_{col_b}']} | "
        f"Duplicated {col_b} rows: {summary[f'dup_{col_b}_rows']} | "
        f"Same {col_b} different {col_a}: {summary[f'same_{col_b}_diff_{col_a}']} | "
        f"Used columns: {summary['used_columns']}"  
    )

    if show_rows:
        cols1 = [col_a, col_b] + ([a] if a != col_a else []) + ([b] if b != col_b else [])
        cols2 = [col_b, col_a] + ([b] if b != col_b else []) + ([a] if a != col_a else [])
        show_df(f"Same {col_a} with different {col_b}", same_a_diff_b[cols1], max_rows)
        show_df(f"Same {col_b} with different {col_a}", same_b_diff_a[cols2], max_rows)

    result_return = {
        "summary": summary,
        "same_a_diff_b": same_a_diff_b,
        "same_b_diff_a": same_b_diff_a,
        "dataframe": dfc
    }

    if return_data:
        return result_return  
    return None

def _norm(kw: str) -> str | None:
    """
    Normalize a keyword by stripping whitespace and converting to lowercase.
    If the input is None or NaN, it returns None.
    """
    if pd.notna(kw):   
        return str(kw).strip().lower()
    return None

def normalize_titles(df: pd.DataFrame, title_column: str = "title") -> pd.DataFrame:
    """
    Normalize the titles in the DataFrame by stripping whitespace and converting to lowercase.
    """
    df[title_column] = df[title_column].apply(_norm)
    return df

def extract_researches_results(rot_dir: str | os.PathLike): 
    """
    Extract research results from pickled files in the specified directory.
    Each file in the directory is expected to be a pickled object that can be converted to a dictionary.
    The function loads each file, converts it to a dictionary using asdict, and appends
    it to a list of researches.
    """
    researches = []
    for papers in os.listdir(rot_dir):
        researches_results_path = os.path.join(rot_dir, papers)
        with open(researches_results_path, "rb") as file: 
            research = asdict(pickle.load(file))
            researches.append(research)
    return researches

def extract_papers(researches : list[dict]) -> list[dict]:
    """ 
    Extract all papers from a list of research results.
    Each research result is expected to be a dictionary with a "papers" key containing a dictionary of papers.
    The function aggregates all papers into a single list and returns it.
    """            
    papers = []
    for results in researches:
        for paper in results["papers"].values():
            papers.append(paper)
    return papers

def to_list(x: Any) -> list[str] | None:
    """Convert input to list[str]. None/NaN → None; scalar → [str]; list/tuple/set → list[str]."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, (list, tuple, set)):
        return [str(e) for e in x]
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple, set)):
                    return [str(e) for e in val]
                logger.warning(f"String is bracketed but not list-like: {s!r}")
                return [s]
            except Exception as e:
                logger.error(f"Error literal_eval on {s!r}: {e}")
                return [s]
        return [s]
    return [str(x)]

def normalize_keywords_col(df: pd.DataFrame, col: str, out: str | None = None) -> pd.DataFrame:
    """
    Ensure 'col' is list-like and create a normalized set-of-tokens column.
    'out' defaults to f"{col}_normset".
    """
    out = out or f"{col}_normset"
    def _norm_listlike(x: Any) -> set[str]:
        lst = to_list(x) or []
        normed = {t for t in (normalize_token(k) for k in lst) if t}
        return normed
    df[out] = df[col].apply(_norm_listlike)
    return df

def _norm_list(lst: list[list[str]]) -> list[set]:
    """
    Normalize a list of lists of keywords into a list of sets of normalized keywords.
    """
    sets_kw = []
    for lst in lists_kw:
        set_keys_inner = set()  
        for keyword in lst:  
            if str(keyword).strip() != "":
                set_keys_inner.add(_norm(keyword))
        sets_kw.append(set_keys_inner)
    return sets_kw