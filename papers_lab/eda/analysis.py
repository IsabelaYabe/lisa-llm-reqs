import pandas as pd
from typing import List
from collections import Counter

class PapersAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def top_keywords(self, n=20):
        """
        Get the top N keywords by frequency.
        """
        all_kws: List[str] = []
        for kws in self.df.get("keywords", []):
            if isinstance(kws, list):
                all_kws.extend(kws)
        counter = Counter(all_kws)
        return counter.most_common(n)
            