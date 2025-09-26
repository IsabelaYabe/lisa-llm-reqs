import os, pickle
from dataclasses import asdict
import pandas as pd
import ast
import re
import unicodedata
from typing import Callable, Any

from lisa.sub_lisa.logger import logger

def _show(title: str, dfx: pd.DataFrame, max_rows: int = 10):
    """
    Print a title and the head of a DataFrame with a maximum number of rows.
    """
    print(f"\n[{title}] ({len(dfx)} lines)")
    print(dfx.head(max_rows))

def _norm_str(s: str) -> str | None:
    """
    Normalize a title by lowercasing, stripping whitespace, and removing punctuation.
    If the input is not a string, it returns an empty string.    
    """
    if not isinstance(s, str):
        return None

    s = unicodedata.normalize("NFKC", s)
        .casefold().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_str_col(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    Normalize a string column in the DataFrame by applying _norm_str function.
    """
    df[f"{col_name}_norm"] = df[col_name].apply(_norm_str)
    return df

def check_col(df: pd.DataFrame, col_name: str, 
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
    
    target_col = col_name
    if normalizer is not None:
        norm_col = f"{col_name}_norm"
        dfc[norm_col] = dfc[col_name].apply(normalizer)
        target_col = norm_col
    
    duplicated_rows = dfc[dfc.duplicated(subset=target_col, keep=False)].sort_values([target_col])
    df_clean = dfc.drop_duplicates(subset=target_col, keep="first").reset_index(drop=True)
    papers_without_value = dfc[dfc[target_col].isna()].copy()

    summary = {
        "total_rows": len(dfc),
        "duplicated_rows": len(duplicated_rows),
        "unique_values": dfc[target_col].nunique(dropna=True),
        "clean_rows": len(df_clean),
        "without_value": len(papers_without_value),
        "column_checked": target_col
    }

    print(
        f"Total: {summary['total_rows']} | Duplicated rows: {summary['duplicated_rows']} | "
        f"Unique values: {summary['unique_value']} | Clean rows: {summary['clean_rows']} | "
        f"Papers without value: {summary['without_value'] | Column: {summary['column_checked']}}"
    )

    if show_rows:
        _show(f"Duplicated by {target_col}", duplicated_rows[[col_name, target_col]], max_rows=max_rows)
        _show(f"Without value in {target_col}", papers_without_value[[col_name, target_col]], max_rows=max_rows)
    
    return df_clean if return_clean_data else None

def check_rows_conflicts(df: pd.DataFrame, col_a: str, col_b: str,
    *, normalize_a: Callable[[Any], Any] | None = None, 
    normalize_b: Callable[[Any], Any] | None = None,
    show_rows: bool = True, max_rows: int = 20,
    return_data: bool = True
):
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
        a_norm = f"{col_a}_norm"
        dfc[a_norm] = dfc[col_a].apply(normalize_a)
        a = a_norm
    
    if normalize_b is not None:
        b_norm = f"{col_b}_norm"
        dfc[b_norm] = dfc[col_b].apply(normalize_b)
        b = b_norm

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
        _show(f"Same {col_a} different {col_b}", same_a_diff_b[[col_a, col_b]], max_rows=max_rows)
        _show(f"Same {col_b} different {col_a}", same_b_diff_a[[col_b, col_a]], max_rows=max_rows)
    
    result_return = {
        "summary": summary,
        "same_a_diff_b": same_a_diff_b,
        "same_b_diff_a": same_b_diff_a,
        "dataframe": dfc
    }

    return result_return if return_data else None

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
    researches = []
    for papers in os.listdir(rot_dir):
        researches_results_path = os.path.join(rot_dir, papers)
        with open(researches_results_path, "rb") as file: 
            research = asdict(pickle.load(file))
            researches.append(research)
    return researches

def extract_papers(researches : list[dict]):            
    papers = []
    for results in researches:
        for paper in results["papers"].values():
            papers.append(paper)
    return papers

def _to_list(x: any) -> list[str] | None:
    """
    Convert input into a list of strings.
    Returns a list of strings in all cases.
    """

    if x is None or (isinstance(x, float)) and math.isnan(x):
        return None
    
    if isinstance(x, (list, tuple, set)):
        return list(x)
    
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple, set)):
                    return list(val)
                else:
                    logger.warning(f"String does not evaluate to a list-like structure: {s}")
                    return [s]
            except Exception as e:
                logger.error(f"Error parsing string to list: {e}")    
                return [s]
        return [s]
    return [x]

def _norm_token(s: str) -> str:
    if not isinstance(s, str): return ""
    tbl = str.maketrans("", "", r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")
    s = unicodedata.normalize("NFKC", s).lower().strip().translate(tbl)
    s = re.sub(r"\s+", " ", s)
    return s

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