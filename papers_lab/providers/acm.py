from __future__ import annotations
from typing import Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_source import BaseSource

class ACMSources(BaseSource):
    """
    ACM collector (documents + metadata) using Selenium.
    Depends on WebDriverConfig (base) for lifecycle/navigation/waits.
    """
    RESULTS_INFO = "//div[@class='search__acm-results']//span[@class='suffix__info']"
    RESULTS_LIST_1 = "//div[@class='search-result doSearch']//ul[@class='search-result__xsl-body  items-results rlist--inline ']/li"
    RESULTS_LIST_2 = "//div[@class='search-result doSearch']//ul[@class='search-result__xsl-body items-results rlist--inline']/li"
    PAG_NEXT = "//div[@class='search-result doSearch']//nav[@class='pagination']//span//a[@class='pagination__btn--next']"

    TITLE = "//div[@class='core-container']/h1"
    AUTHORS = "//div[@class='contributors']//span[@class='authors']//span[@property='author']"
    ABSTRACT = "//div[@id='abstracts']//section[@id='abstract']//div"
    DATE = "//div[@class='core-published']//span[@class='core-date-published']"
    TERMS_SECTION_ID = "sec-terms"
    TERMS_LIST = "//section[@id='sec-terms']//div[@class='citation article__section article__index-terms']//ol[@class='rlist organizational-chart']/li"
    ALLOW_COOKIES = "//div[@id='CybotCookiebotDialogBodyButtonsWrapper']//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']"
    
    def __init__(self, **cfg):
        cfg.setdefault("show_limit", 20)
        super().__init__(**cfg)

    @property
    def publisher(self) -> str:
        """
        Name of the publisher/source.
        """
        return "ACM"

    @property
    def search_ready_xpath(self) -> str:
        """
        XPath to wait for search results to load.
        """
        return "//div[@class='pull-right search-showing-results']"

    def _parse_search_header(self) -> dict[str, Any]:
        """
        Parse the search results header to extract number of results, keywords, and years.
        """
        text = self.driver.find_element(By.XPATH, self.RESULTS_INFO).text
        i_res = text.find("Results for: ")
        kw_start = i_res + len("Results for: ")
        i_date = text.find("AND [E-Publication Date: ")
        date_start = i_date + len("AND [E-Publication Date: ")
        return {
            "num_results": int(text[:i_res]),
            "keywords": text[kw_start:i_date],
            "years": text[date_start:-1],
        }

    def _list_items_one_page(self):
        """
        Get list items (papers) on the current search results page.
        """ 
        ul = self.driver.find_elements(By.XPATH, self.RESULTS_LIST_1)
        if not ul:
            ul = self.driver.find_elements(By.XPATH, self.RESULTS_LIST_2)
        return ul

    def _collect_search_ids_one_page(self) -> list[str]:
        """
        Collect document IDs (DOI suffixes) from the current search results page.
        """
        ids: list[str] = []
        for li in self._list_items_one_page():
            for ln in li.text.split("\n"):
                if "https://doi.org/" in ln:
                    idx = ln.find("https://doi.org/") + len("https://doi.org/")
                    ids.append(ln[idx:])
        return ids

    def _goto_next_page(self, page_idx: int) -> None:
        """
        Navigate to the next page of search results.
        """
        self.wait_click(self.ALLOW_COOKIES)
        href = self.driver.find_element(By.XPATH, self.PAG_NEXT).get_attribute("href")
        self.restart()
        self.load(href)

    def _parse_title(self) -> str:
        """
        Parse the title of the current paper.
        """
        elems = self.wait_all(self.TITLE)
        if len(elems) != 1:
            raise ValueError(f"Expected 1 <h1>, found {len(elems)}")
        return elems[0].text

    def _parse_authors(self) -> list[str]:
        """
        Parse the list of authors of the current paper.
        """
        return [e.text for e in self.driver.find_elements(By.XPATH, self.AUTHORS)]

    def _parse_abstract(self) -> Optional[str]:
        """
        Parse the abstract of the current paper.
        """
        return self.driver.find_element(By.XPATH, self.ABSTRACT).text

    def _parse_date(self) -> Optional[str]:
        """
        Parse the publication date of the current paper.
        """
        return self.driver.find_element(By.XPATH, self.DATE).text

    def _parse_doi(self, doc_id: str) -> Optional[str]:
        """
        Parse the DOI of the current paper.
        """
        return doc_id

    def _parse_keywords(self) -> list[str]:
        """
        Parse the keywords (terms) of the current paper.
        """
        sec = self.driver.find_element(By.ID, self.TERMS_SECTION_ID)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", sec)
        items = self.wait_all(self.TERMS_LIST)
        kws: list[str] = []

        for li in items:
            kws.extend(t for t in li.text.split("\n") if t)
        
        kws = kws[1:] if kws else []
        return list(dict.fromkeys(kws))

    def _paper_url(self, doc_id: str) -> str:
        """
        Construct the full URL of the paper given its document ID (DOI suffix).
        """
        return f"https://dl.acm.org/doi/{doc_id}"