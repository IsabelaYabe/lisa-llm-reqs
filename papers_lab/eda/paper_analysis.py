from __future__ import annotations

import pandas as pd
from typing import Optional
from .analysis import Analysis

class PaperAnalysis(Analysis):
    """
    Domain-specific helpers for papers. Thin wrappers around generic Analysis methods.
    """

    def keyword_frequency(self,
        col: str = "keywords_norm",
        *,
        top: Optional[int] = None) -> pd.Series:
        """
        Frequency of keywords (normalized by default).
        """
        s = self.frequency(col)
        return s.head(top) if top else s

    def top_keywords(self,
        n: int = 20,
        col: str = "keywords_norm") -> pd.Series:
        """
        Alias: top-N keywords.
        """
        return self.keyword_frequency(col=col,top=n)

    def cooccurrence_keywords(self,
        *,
        top_n: Optional[int] = 50,
        normalize: bool = False,
        col: str = "keywords_norm") -> pd.DataFrame:
        """
        Co-occurrence matrix for keywords.
        """
        return self.cooccurrence_matrix(col=col, top_n=top_n, normalize=normalize)

    def keyword_trends(self,
        *,
        year_col: str = "year",
        top_k: int = 15,
        col: str = "keywords_norm") -> pd.DataFrame:
        """
        Year × keyword (top-K) pivot.
        """
        return self.trends_over_time(list_col=col, time_col=year_col, top_k=top_k)

    def bag_of_keywords(self,
        col: str = "keywords_norm") -> pd.DataFrame:
        """
        Binary papers × keyword matrix.
        """
        return self.bag_of_listcol(col)

    def author_frequency(self,
        col: str = "authors",
        *,
        top: Optional[int] = None) -> pd.Series:
        """
        Frequency of authors.
        """
        s = self.frequency(col)
        return s.head(top) if top else s

    def papers_per_year(self,
        year_col: str = "year") -> pd.Series:
        """
        Number of papers per year (sorted).
        """
        s = self.frequency(year_col)
        return s.sort_index().rename("n_papers")

    def papers_per_month(self,
        month_col: str = "month") -> pd.Series:
        """
        Number of papers per month (sorted).
        """
        s = self.frequency(month_col)
        return s.sort_index().rename("n_papers")
    
    def papers_per_year_month(self,
        year_month_col: str = "year_month") -> pd.Series:
        """
        Number of papers per year-month (sorted).
        """
        s = self.frequency(year_month_col)
        return s.sort_index().rename("n_papers")

    def topics_over_time(self,
        topics_col: str = "topics",
        year_col: str = "year") -> pd.DataFrame:
        """
        Year × topic pivot.
        """
        return super().topics_over_time(topics_col=topics_col, year_col=year_col)
