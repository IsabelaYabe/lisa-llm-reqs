from __future__ import annotations
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any, Iterable, Callable, Tuple
from math import ceil

from logger import logger
from .base import WebDriverConfig
from .models import Research, ResearchPaper


class BaseSource(WebDriverConfig, ABC):
    """Template for providers (IEEE/ACM). Defines the flow; subclasses implement the parsers."""
    @property
    @abstractmethod
    def publisher(self) -> str: 
        """
        Get the name of the publisher.
        """
    @property
    @abstractmethod
    def search_ready_xpath(self) -> str: 
        """
        Get the XPath to wait for when loading a search results page.
        """

    @abstractmethod
    def _parse_search_header(self) -> dict[str, Any]:
        """ 
        Parse the search results header to extract metadata like number of results, keywords, and years.
        """
    @abstractmethod
    def _collect_search_ids_one_page(self) -> list[str]: 
        """
        Collect document IDs (e.g., DOI suffixes) from the current search results page.
        """
    @abstractmethod
    def _goto_next_page(self, page_idx: int) -> None: 
        """
        Navigate to the next page of search results.
        """

    @abstractmethod
    def _parse_title(self) -> str: 
        """
        Parse the title of the current paper.
        """
    @abstractmethod
    def _parse_authors(self) -> list[str]: 
        """
        Parse the list of authors of the current paper.
        """
    @abstractmethod
    def _parse_abstract(self) -> Optional[str]: 
        """
        Parse the abstract of the current paper.
        """
    @abstractmethod
    def _parse_date(self) -> Optional[str]: 
        """
        Parse the publication date of the current paper.
        """
    @abstractmethod
    def _parse_doi(self, doc_id: Optional[str]) -> Optional[str]: 
        """
        Parse the DOI of the current paper, optionally using the document ID.
        """
    @abstractmethod
    def _parse_keywords(self) -> list[str]: 
        """
        Parse the list of keywords of the current paper.
        """
    @abstractmethod
    def _paper_url(self, doc_id: str) -> str:
        """
        Construct the URL for a paper given its document ID.
        """

    def _safe_parse_item(self, parser: Callable[..., Any] , *args: Any, default: Any = None, field_name: str = "field", doc_id_for_log: Optional[str] = None) -> Tuple[Any, bool]:
        """
        Safely call a parsing function, logging any exceptions and returning a default value if needed.
        Returns a tuple of (parsed_value, success_flag).
        """
        try:
            result = parser(*args)
            if result is None:
                logger.warning(f"{self.publisher}:{doc_id_for_log or ''} Parsing returned None for {field_name}")
                return default, False
            return result, True
        except Exception as e:
            logger.warning(f"{self.publisher}:{doc_id_for_log or ''} Error parsing {field_name}: {e}", exc_info=True)
            return default, False
            
    def _collect_all_ids(self, total: int | Iterable[Any]) -> list[str]:
        """
        Collect all paper IDs from the search results, handling pagination as needed.
        """
        if not isinstance(total, int):
            total = len(list(total))
        ids: list[str] = []
        pages = total // self.show_limit
        for i in range(pages):
            ids += self._collect_search_ids_one_page()
            self._goto_next_page(i + 1)  
        ids += self._collect_search_ids_one_page()
        return ids

    @staticmethod
    def _chunks(seq: Iterable[Any], size: int):
        """
        Generator function that splits a sequence into chunks of a specified size.
        """
        data = list(seq)
        size = max(1, int(size))
        for i in range(0, len(data), size):
            yield data[i:i + size]

    def _fetch_many(self, ids: list[str]) -> tuple[dict[str, ResearchPaper], dict[str, ResearchPaper], list[str]]:
        """
        Fetch and parse multiple papers given their IDs, returning dictionaries of successful and incomplete papers, and a list of failed URLs.
        """
        papers: dict[str, ResearchPaper] = {}
        incomplete: dict[str, ResearchPaper] = {}
        failed: list[str] = []

        with self.__class__(headless=self._headless, wait_time=self._wait_time, show_limit=self.show_limit) as tmp:
            for doc_id in ids:
                url = self._paper_url(doc_id)
                try:
                    tmp.load(url)

                    kws, ok_kw = self._safe_parse_item(tmp._parse_keywords, field_name="keywords", doc_id_for_log=doc_id)
                    date, ok_dt = self._safe_parse_item(tmp._parse_date, field_name="date", doc_id_for_log=doc_id)
                    abstract, ok_abs = self._safe_parse_item(tmp._parse_abstract, field_name="abstract", doc_id_for_log=doc_id)
                    doi, ok_doi = self._safe_parse_item(tmp._parse_doi, doc_id, field_name="DOI", doc_id_for_log=doc_id)
                    authors, ok_auth = self._safe_parse_item(tmp._parse_authors, field_name="authors", doc_id_for_log=doc_id)

                    title = tmp._parse_title()
                    inc = not all([ok_kw, ok_dt, ok_abs, ok_doi, ok_auth])

                    paper = ResearchPaper(
                        title=title,
                        date=date,
                        abstract=abstract,
                        DOI=doi,
                        source_url=url, 
                        authors=authors,
                        keywords=kws
                        )

                    papers[doc_id] = paper
                    if inc:
                        incomplete[doc_id] = paper
                except Exception as e:
                    failed.append(url)
                    logger.error(f"{self.publisher} erro em ID={doc_id} | URL={url} | {e}", exc_info=True)
        return papers, incomplete, failed

    def get_all_researches(self, url: str, *, max_workers: int | None = None, chunk_size: int = 5,
    ) -> Optional[Research]:
        """
        Main method to fetch all research papers from a search results URL.
        """
        self.load(url, wait_xpath=self.search_ready_xpath)
        meta = self._parse_search_header()
        total = int(meta.get("num_results", 0))
        if total <= 0:
            logger.warning(f"{self.publisher}: sem resultados para {url}")
            return None

        ids = self._collect_all_ids(total)
        workers = max_workers or self.compute_workers(len(ids))

        papers: dict[str, ResearchPaper] = {}
        failed: list[str] = []
        incomplete: dict[str, ResearchPaper] = {}
        
        chunks = list(self._chunks(ids, max(1, int(chunk_size))))
        with ThreadPoolExecutor(max_workers=min(workers, len(chunks))) as ex:
            futures = {ex.submit(self._fetch_many, chunk): tuple(chunk) for chunk in chunks}
            for fut in as_completed(futures):
                p_ok, inc, fl = fut.result()
                papers.update(p_ok)
                incomplete.update(inc)
                failed.extend(fl)
    
        if failed:
            logger.warning(f"{self.publisher}: {len(failed)} URLs encountered errors")

        return Research(
            num_results=total,
            keywords=meta.get("keywords", ""),
            years=meta.get("years", ""),
            publisher=self.publisher,
            url=url,
            content_type=[meta.get("content_type", "")] if meta.get("content_type") else [],
            papers_urls=ids,
            failed_urls=failed,
            papers=papers,
            incomplete_papers=incomplete,
        )