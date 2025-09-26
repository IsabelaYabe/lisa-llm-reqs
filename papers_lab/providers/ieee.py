from __future__ import annotations
from typing import Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from lisa.sub_lisa.logger import logger
from .base_source import BaseSource


class IEEESources(BaseSource):
    """
    IEEE Xplore collector (documents + metadata) using Selenium.
    Inherits from BaseSource and implements only the specific parsers/XPaths.
    """

    DASHBOARD = "//div[@class='Dashboard-section Dashboard-section-gray text-base-md-lh']"
    RESULTS_LIST = "//xpl-results-list/div[@class='List-results-items']"
    PAG_NEXT = "//div[@class='pagination-bar hide-mobile text-base-md-lh']//button[@class='stats-Pagination_arrow_next_{num}']"

    TITLE = "//h1[contains(@class, 'document-title')]//span"
    AUTHORS = "//div[contains(@class, 'authors-container')]//span[contains(@class, 'authors-info')]"
    ABSTRACT = "//div[@class='u-mb-1']"
    DATE = "//div[contains(@class, 'u-pb-1 doc-abstract-')]"
    DOI = "//div[@class='u-pb-1 stats-document-abstract-doi']"

    KEYWORDS_BTN = "//button[@id='keywords']"
    KEYWORDS_LIST = ("//ul[@class='doc-keywords-list stats-keywords-list']"
                     "/li[@class='doc-keywords-list-item']"
                     "//ul[@class='u-mt-1 u-p-0 List--no-style List--inline']")
    
    def __init__(self, **cfg):
        cfg.setdefault("show_limit", 25)
        super().__init__(**cfg)

    @property
    def publisher(self) -> str:
        """
        Name of the publisher/source.
        """
        return "IEEE"

    @property
    def search_ready_xpath(self) -> str:
        """
        XPath to wait for search results to load.
        """
        return "//div[@class='personal-login-header']"

    def _parse_search_header(self) -> dict[str, Any]:
        """
        Parse the search results header to extract number of results, keywords, and years.
        """
        divs = self.driver.find_elements(By.XPATH, self.DASHBOARD)
        
        if len(divs) != 1:
            raise ValueError(f"Expected 1 header, found {len(divs)}.")
        
        lines = divs[0].text.split("\n")
        top = lines[0].split(" ")
        yrs = lines[1].split(" ")
        content = lines[2:]
        
        return {
            "num_results": int(top[3]),
            "keywords": " ".join(top[5:]),
            "years": " ".join(yrs[2:]),
            "content_type": " ".join(content),
        }

    def _collect_search_ids_one_page(self) -> list[str]:
        """
        Collect document IDs (DOI suffixes) from the current search results page.
        """
        elems = self.wait_all(self.RESULTS_LIST)
        return [e.get_attribute("id") for e in elems]

    def _goto_next_page(self, page_idx: int) -> None:
        """
        Navigate to the next page of search results.
        """
        xp = self.PAG_NEXT.format(num=page_idx + 1)  
        self.wait_click(xp)

    def _parse_title(self) -> str:
        """
        Parse the title of the current paper.
        """
        span_title = self.wait.until(EC.presence_of_element_located((By.XPATH, self.TITLE)))
        return span_title.text

    def _parse_authors(self) -> list[str]:
        """
        Parse the list of authors of the current paper.
        """
        authors: list[str] = []
        for el in self.driver.find_elements(By.XPATH, self.AUTHORS):
            author = (el.text or "").strip()
            if author.endswith(";"):
                author = author[:-1]
            if author:
                authors.append(author)
        return authors

    def _parse_abstract(self) -> Optional[str]:
        """
        Parse the abstract of the current paper.
        """
        div = self.driver.find_element(By.XPATH, self.ABSTRACT)
        parts = (div.text or "").split("\n")
        if len(parts) > 1:
            return parts[1]  
        else:
            None

    def _parse_date(self) -> Optional[str]:
        """
        Parse the publication date of the current paper.
        """
        txt = self.driver.find_element(By.XPATH, self.DATE).text
        if "Publication" in txt:
            return txt.replace("Date of Publication: ", "")
        if "Conference" in txt:
            return txt.replace("Date of Conference: ", "")
        logger.debug(txt)
        return None

    def _parse_doi(self, doc_id: Optional[str]) -> Optional[str]:
        """
        Parse the DOI of the current paper.
        """
        try:
            el = self.driver.find_element(By.XPATH, self.DOI)
            doi = el.text.replace("DOI:", "").strip()
            return doi
        except Exception as e:
            logger.warning(f"Could not parse DOI: {e}")
            return None

    def _parse_keywords(self) -> list[str]:
        """
        Parse the list of keywords of the current paper.
        """
        self.wait_click(self.KEYWORDS_BTN)
        groups = self.wait_all(self.KEYWORDS_LIST)

        kws: list[str] = []
        for g in groups:
            txt = (g.text or "").strip()
            if txt:
                kws += txt.split("\n,\n")
    
        return list(dict.fromkeys(kws))
    
    def _paper_url(self, doc_id: str) -> str:
        """
        Construct the URL of the paper given its document ID.
        """
        return f"https://ieeexplore.ieee.org/document/{doc_id}/"