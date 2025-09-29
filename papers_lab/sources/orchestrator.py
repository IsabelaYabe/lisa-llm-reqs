from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Tuple, List, Dict

from logger import logger
from papers_lab.providers import IEEESources, ACMSources
from papers_lab.io import Storage

def split_urls_by_domain(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Split a list of URLs into two lists based on their domain: IEEE and ACM (ignoring others).
    """
    ieee_list, acm_list = [], []
    for url in urls or []:
        if not url:
            continue

        netloc = urlparse(url).netloc.lower()
        if netloc.endswith("ieeexplore.ieee.org"):
            ieee_list.append(url)
        elif netloc.endswith("dl.acm.org"):
            acm_list.append(url)
        else:
            logger.warning(f"Unrecognized domain in URL: {url}")
    return ieee_list, acm_list

class SourcesOrchestrator:
    """
    Orchestrator for fetching research papers from IEEE and ACM sources.
    """
    def __init__(self, storage: Storage):
        self.storage = storage
    
    def _fetch_one_source(self,source_name: str,handler,urls: List[str],tag: str,save_dir: str | os.PathLike,
    ) -> Dict[str, str]:
        """
        Run queries for one source (IEEE/ACM), save pickled results and return mapping {path: url}.
        """
        # urls = [u for u in urls if u]
        # if not urls:
        #     return {}

        # out_dir = Path(save_dir) / source_name.lower()
        # out_dir.mkdir(parents=True, exist_ok=True)

        saved_files_by_path: Dict[str, str] = {}
        for i, url in enumerate(urls, start=1):
            try:
                research = handler.get_all_researches(url)
                if research:
                    file_path = self.storage.save(
                        research,
                        root=Path(save_dir) / source_name.lower(),
                        name=f"{source_name.lower()}_research_{tag}_{i}"
                    )
                    saved_files_by_path[str(file_path)] = url
                    
                    # logger.debug(f"Saved {source_name.upper()} research {tag}_{i}:\n len_papers={len(research.papers)}\n num_results={research.num_results}\n incomplete_papers={len(research.incomplete_papers)}")
                else:
                    logger.warning(f"No results for URL ({source_name.upper()}): {url}")
            except Exception:
                logger.exception(f"Error processing {source_name.upper()} research {tag}_{i} from URL: {url}", exc_info=True)
        return saved_files_by_path

    def fetch_all(self, urls: List[str], research_tag: str, save_dir: str | os.PathLike
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Orchestrate fetching for IEEE and ACM URLs. Returns tuple (ieee_results, acm_results).
        """
        ieee_urls, acm_urls = split_urls_by_domain(urls)

        with IEEESources() as ieee:
            saved_ieee = self._fetch_one_source("ieee", ieee, ieee_urls, research_tag, save_dir)

        with ACMSources() as acm:
            saved_acm = self._fetch_one_source("acm", acm, acm_urls, research_tag, save_dir)

        return saved_ieee, saved_acm