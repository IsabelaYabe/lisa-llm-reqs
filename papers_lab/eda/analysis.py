import pandas as pd
from typing import List, Sequence
from collections import Counter
from itertools import combinations
import numpy as np
import re

class Analysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def _iter_listcol(self, col: str):
        """
        Iterate over a DataFrame column containing lists, yielding lists or empty lists.
        """
        if col not in self.df.columns:
            return
        for x in self.df.get(col, []):
            if isinstance(x, (list, tuple, set)):
                yield list(x)
            else:
                yield [] 

    def frequency(self, col: str) -> pd.Series:
        """
        Frequency for either a scalar column (value_counts) or a list column (explode → value_counts).
        """
        if col not in self.df.columns:
            return pd.Series(dtype=int)
        s = self.df[col]
        if s.map(lambda v: isinstance(v, (list, tuple, set)) or pd.isna(v)).all():
            s = s.explode().dropna()
        return s.value_counts()
    
    def cooccurrence_matrix(self, col="keywords_norm", top_n: int | None = 50, normalize: bool = False) -> pd.DataFrame:
        """
        Compute co-occurrence matrix for items in a list column.
        Only the top_n most frequent items are considered if top_n is specified. 
        """
        freq = self.frequency(col)
        if freq.empty:
            return pd.DataFrame()
        labels = list(freq.head(top_n).index) if top_n else list(freq.index)
        idx = {k: i for i, k in enumerate(labels)}
        M = np.zeros((len(labels), len(labels)), dtype=float)

        if col not in self.df.columns:
            return pd.DataFrame(M, index=labels, columns=labels)

        for lst in self._iter_listcol(col):
            xs = [k for k in lst if k in idx]
            for a, b in combinations(xs, 2):
                i, j = idx[a], idx[b]
                M[i, j] += 1
                M[j, i] += 1

        if normalize and M.sum() > 0:
            M = M / M.sum()
        return pd.DataFrame(M, index=labels, columns=labels)

    def trends_over_time(self, list_col: str, time_col: str = "year", top_k: int | None = None) -> pd.DataFrame:
        """
        Pivot (time × item) for a list column. If top_k, filter by the most frequent.
        """
        if list_col not in self.df.columns or time_col not in self.df.columns:
            return pd.DataFrame()

        df2 = self.df[[time_col, list_col]].dropna(subset=[time_col]).copy()
        df2[list_col] = df2[list_col].apply(lambda v: list(v) if isinstance(v,(list,tuple,set)) else [])
        df2 = df2.explode(list_col)

        if df2.empty:
            return pd.DataFrame()

        if top_k:
            top = set(self.frequency(list_col).head(top_k).index)
            df2 = df2[df2[list_col].isin(top)]
            if df2.empty:
                return pd.DataFrame()

        return pd.crosstab(df2[time_col].astype("Int64"), df2[list_col]).sort_index()


    def topics_over_time(self, topics_col="topics", year_col="year") -> pd.DataFrame:
        """
        Analyze distribution of topics over years.
        """
        if topics_col not in self.df.columns or year_col not in self.df.columns:
            return pd.DataFrame()
        df2 = self.df[[year_col, topics_col]].dropna(subset=[year_col]).copy()
        df2[topics_col] = df2[topics_col].apply(lambda v: list(v) if isinstance(v, (list, tuple, set)) else ([v] if pd.notna(v) else []))
        df2 = df2.explode(topics_col)
        if df2.empty:
            return pd.DataFrame()
        return pd.crosstab(df2[year_col].astype("Int64"), df2[topics_col]).sort_index()

    def bag_of_listcol(self, col: str) -> pd.DataFrame:
        """
        Create a bag-of-words DataFrame for a list column.
        """
        if col not in self.df.columns:
            return pd.DataFrame(index=self.df.index)
        df2 = self.df[[col]].copy()
        df2[col] = df2[col].apply(lambda v: list(v) if isinstance(v,(list,tuple,set)) else [])
        exploded = df2.explode(col)
        if exploded.empty:
            return pd.DataFrame(index=self.df.index)
        X = pd.crosstab(exploded.index, exploded[col]).astype(int)
        return X.reindex(self.df.index, fill_value=0)