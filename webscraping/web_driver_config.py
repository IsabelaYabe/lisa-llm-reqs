from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Optional
from lisa.sub_lisa.logger import logger
import pickle
import os

from dataclasses import dataclass, field 
from typing import List

@dataclass
class ResearchPaper:
    title: str
    date: Optional[str]
    abstract: Optional[str]  
    DOI: Optional[str]
    source_url: str
    authors: Optional[List[str]] = field(default_factory=list)
    keywords: Optional[List[str]] = field(default_factory=list)
    
@dataclass
class Research:
    num_results: int 
    keywords: str 
    years: str 
    publisher: str 
    url: str
    content_type: List[str] = field(default_factory=list) 
    papers_urls: List[str] = field(default_factory=list) 
    failed_urls: List[str] = field(default_factory=list)
    papers: dict = field(default_factory=dict)
    incomplete_papers: dict = field(default_factory=dict) 

class WebDriverConfig:
    def __init__(self, limit_showing=25, wait_time=17, headless=False):
        self._headless = headless
        self._chrome_options = None
        self._driver = None
        self._wait_time = wait_time
        self._driver_wait = WebDriverWait(self.driver, self.wait_time)
        self._limit_showing = limit_showing
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit_driver()
        
    def setup_chrome_options(self):
        os.environ['WDM_LOG_LEVEL'] = '0'
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            #chrome_options.add_argument("--no-sandbox")
            #chrome_options.add_argument("--disable-dev-shm-usage")
            #chrome_options.add_argument("--user-agent=Mozilla/5.0 (...) Safari/537.36")

        return chrome_options
    
    def initialize_driver(self):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=self.chrome_options)
        return driver
    
    def load_url(self, url, wait_xpath=None):
        self.driver.get(url)
        if wait_xpath:
            self.driver_wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
    
    def quit_driver(self):
        if self._driver is not None:
            try: 
                self._driver.quit()
            except Exception as e:
                logger.error(f"Erro ao finalizar o driver: {e}")
            finally:
                self._driver = None

    def restart_driver(self):
        self.quit_driver()
        self._driver = None
        self._driver_wait = WebDriverWait(self.driver, self.wait_time)
                    
    @property
    def chrome_options(self):
        if self._chrome_options is None:
            self._chrome_options = self.setup_chrome_options()
        return self._chrome_options
    
    @property
    def driver(self):
        if self._driver is None: 
            self._driver = self.initialize_driver()
        return self._driver 
    
    @property
    def  wait_time(self):
        return self._wait_time

    @wait_time.setter
    def wait_time(self, value):
        if isinstance(value, int) and value > 0:
            self._wait_time = value
            self._driver_wait = WebDriverWait(self.driver, self.wait_time)
        else:
            raise ValueError("wait_time must be a positive integer")
    
    @property
    def headless(self):
        return self._headless
    
    @property
    def driver_wait(self):
        return self._driver_wait    
    
    @property
    def showing_limit(self):
        return self._limit_showing
  
class IEEESources(WebDriverConfig):
    def  __init__(self):
        super().__init__()
        self.limit_showing_per_page=25        

    def __research_datas(self):
        xpath = "//div[@class='Dashboard-section Dashboard-section-gray text-base-md-lh']"
        div = self.driver.find_elements(By.XPATH, xpath)
        
        if len(div) != 1:
            raise ValueError(f"Expected exactly 1 matching div, but found {len(div)}.")
        div = div[0]
        
        split_text = div.text.split("\n")
        num_of_results_and_keywords = split_text[0].split(" ")
        years = split_text[1].split(" ")
        content_type = split_text[2:]
            
        research = {
            "num_results": int(num_of_results_and_keywords[3]),  
            "keywords": " ".join(num_of_results_and_keywords[5:]),
            "years": " ".join(years[2:]),  
            "content_type": " ".join(content_type) 
        }
        
        return research
    
    def __searches_on_page(self):
        xpath = "//xpl-results-list/div[@class='List-results-items']"
        researches = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        researches_id = [x.get_attribute("id") for x in researches]
        
        return researches_id
    
    def __next_page(self, num_pag):
        xpath = f"//div[@class='pagination-bar hide-mobile text-base-md-lh']//button[@class='stats-Pagination_arrow_next_{num_pag}']"
        next_button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        next_button.click()
        time.sleep(1.5)
        
    def __all_searches_ids(self, num_researches): 
        if isinstance(num_researches, list):
            logger.warning("The argument type is a list, which is not ideal. The ideal type is an integer. The value will be converted to the number of elements in the list.")
            num_researches = len(num_researches)
            
        num_pag_next = num_researches//self.limit_showing_per_page
        researches_id = []
        for i in range(num_pag_next):
            researches_id.extend(self.__searches_on_page())
            self.__next_page(i+2)
        researches_id.extend(self.__searches_on_page())
        return researches_id

    def __paper_title(self):
        xpath = "//h1[contains(@class, 'document-title')]//span"
        span_title = self.driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        title = span_title.text
        
        return title
    
    def __paper_authors(self): 
        xpath = "//div[contains(@class, 'authors-container')]//span[contains(@class, 'authors-info')]"
        span_authors = self.driver.find_elements(By.XPATH, xpath)
        
        authors = []
        for author in span_authors:
            author = author.text
            if author[-1] == ";":
                author = author[:-1]
            authors.append(author)
        
        return authors
    
    def __paper_abstract(self):        
        xpath = "//div[@class='u-mb-1']"
        span_abstract = self.driver.find_element(By.XPATH, xpath)
        full_text = span_abstract.text
        abstract_text = full_text.split("\n")[1]
        
        return abstract_text
    
    def __paper_date(self): 
        xpath = "//div[contains(@class, 'u-pb-1 doc-abstract-')]"
        
        div_date = self.driver.find_element(By.XPATH, xpath)
        date_text = div_date.text
        if "Publication" in date_text:
             date = div_date.text.replace("Date of Publication: ", "")
        elif "Conference" in date_text:
            date = div_date.text.replace("Date of Conference: ", "")
        else:
            logger.debug(date_text)
        return date
        
    def __paper_doi(self):
        xpath = "//div[@class='u-pb-1 stats-document-abstract-doi']"
        div_doi = self.driver.find_element(By.XPATH, xpath)
        doi = div_doi.text.replace("DOI: ", "")

        return doi
    
    def __paper_keywords(self):
        xpath = "//button[@id='keywords']"
        keywords_button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", keywords_button)
        keywords_button = self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        keywords_button.click()
        
        xpath = "//ul[@class='doc-keywords-list stats-keywords-list']/li[@class='doc-keywords-list-item']//ul[@class='u-mt-1 u-p-0 List--no-style List--inline']"
        
        ul_elem_temp = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        all_keywords = []
        
        for ul in ul_elem_temp:
            ul_text = ul.text.strip()
            if ul_text != "":
                keywords = ul_text.split("\n,\n") 
                all_keywords.append(keywords)
        
        return all_keywords
                
    def __research_paper(self, id): 
        source_url = f"https://ieeexplore.ieee.org/document/{id}"
        self.load_url(source_url)   
        
        incomplete = False 
        try:
            keywords = self.__paper_keywords()
        except:
            logger.warning(f"[{id}] Failed to collect keywords.")
            keywords = None
            incomplete = True
            
        try:
            date = self.__paper_date()
        except:
            logger.warning(f"[{id}] Failed to collect date.")
            date = None
            incomplete = True

        try:
            abstract = self.__paper_abstract()
        except:
            logger.warning(f"[{id}] Failed to collect abstract.")
            abstract = None
            incomplete = True

        try:
            doi = self.__paper_doi()
        except:
            logger.warning(f"[{id}] Failed to collect DOI.")
            doi = None
            incomplete = True

        try:
            authors = self.__paper_authors()
        except:
            logger.warning(f"[{id}] Failed to collect authors.")
            authors = None
            incomplete = True

        research_paper = ResearchPaper(
            title=self.__paper_title(),
            date=date,
            abstract=abstract,
            DOI=doi,
            source_url=source_url,
            authors=authors,
            keywords=keywords
        )
        self.quit_driver()
        return research_paper, incomplete

    def __fetch_paper(self, id, failed_urls, incomplete_papers): 
        url = f"https://ieeexplore.ieee.org/document/{id}"
        try:
            with IEEESources() as temp_ieee:
                paper, incomplete = temp_ieee.__research_paper(id)
                if incomplete:
                    incomplete_papers[id] = paper
                    logger.warning(f"Paper de id={id} processado, porém incompleto.  URL: {url}")
                logger.debug(f"Paper de id={id} processado!")
                return paper
        except Exception as e:
            failed_urls.append(url)
            logger.error(f"Error processing role ID={id}| URL: {url} | Erro: {e}", exc_info=True)
            return None
            
    def __max_workers(self, num_elements): 
        max_workers_by_cpu = os.cpu_count() * 2
        if num_elements > max_workers_by_cpu:
            max_workers = max_workers_by_cpu
            return max_workers
        
        odd_numbers = [2,3,5,7]
        lower_value = None
        max_workers = None
        for odd in odd_numbers:
            lower_temp = num_elements//odd
            if lower_value is None:
                lower_value = lower_temp
                max_workers = odd
            elif lower_temp < lower_value:
                lower_value = lower_temp
                max_workers = odd
        
        if max_workers < max_workers_by_cpu:
            return max_workers

    def get_all_researches(self, url, max_workers=None): 
        self.load_url(url, wait_xpath="//div[@class='personal-login-header']")
        research_datas = self.__research_datas() 
        num_researches = research_datas["num_results"] 
        papers_ids = self.__all_searches_ids(num_researches) 
        
        if max_workers is None:
            max_workers = self.__max_workers(num_researches)
            
        papers = {}
        failed_urls = [] 
        incomplete_papers = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_id = {ex.submit(self.__fetch_paper, id, failed_urls, incomplete_papers): id for id in papers_ids}
            for future in as_completed(future_to_id):
                paper_id = future_to_id[future]
                paper = future.result()
                if paper:
                    papers[paper_id] = paper
        
        research = Research(
            num_results = research_datas["num_results"],
            keywords = research_datas["keywords"],
            years = research_datas["years"],
            publisher = "IEEE",
            url = url,
            content_type = research_datas["content_type"],
            papers_urls = papers_ids,
            failed_urls = failed_urls,
            papers = papers,
            incomplete_papers = incomplete_papers
        )        
        
        if failed_urls:
            logger.warning(f"Total URLs with error: {len(failed_urls)}")
            for fail in failed_urls:
                logger.warning(f"Failed to parse: {fail}")
                
        return research
    
class ACMSources(WebDriverConfig):
    def  __init__(self):
        super().__init__()
        self.limit_showing_per_page=20     

    def __research_datas(self):
        xpath = "//div[@class='search__acm-results']//span[@class='suffix__info']"
        span_text = self.driver.find_element(By.XPATH, xpath).text
        index_results_for = span_text.find("Results for: ")
        end_index_result = index_results_for + len("Results for: ")
        index_date = span_text.find("AND [E-Publication Date: ")
        end_index_date = index_date + len("AND [E-Publication Date: ")
        num_results =  int(span_text[:index_results_for])
        keywords = span_text[end_index_result:index_date]
        years = span_text[end_index_date:-1]
        
        research = {
            "num_results": num_results,
            "keywords": keywords,
            "years": years
        }
        
        return research
    
    def __searches_on_page(self):
        ul_class = "search-result__xsl-body  items-results rlist--inline "
        xpath = f"//div[@class='search-result doSearch']//ul[@class='{ul_class}']/li"
        ul = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        if not ul:
            ul_class = "search-result__xsl-body items-results rlist--inline"
            xpath = f"//div[@class='search-result doSearch']//ul[@class='{ul_class}']/li"
            ul = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            
        ids = []
        for li in ul:
            li_text = li.text 
            if li_text != "":  
                text_split = li_text.split("\n")
                for text in text_split:
                    if "https://doi.org/" in text:
                        index = text.find("https://doi.org/")
                        end_index = index + len("https://doi.org/")
                        text = text[end_index:]
                        ids.append(text)

        return ids
    
    def __allow_all_cookies(self):
        xpath = "//div[@id='CybotCookiebotDialogBodyButtonsWrapper']//button[@id='CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll']"
        allow = self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        allow.click()
        logger.debug("Cookies autorizados")

    def __next_page(self):
        self.__allow_all_cookies()
        xpath = "//div[@class='search-result doSearch']//nav[@class='pagination']//span//a[@class='pagination__btn--next']"
        next_button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        next_button = self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        url = next_button.get_attribute("href")
        logger.debug(f"Próxima página: {url}")
        self.restart_driver()
        time.sleep(1)
        self.load_url(url)
        #next_button.click()
        time.sleep(1)

    def __all_searches_ids(self, num_researches): 
        if isinstance(num_researches, list):
            logger.warning("The argument type is a list, which is not ideal. The ideal type is an integer. The value will be converted to the number of elements in the list.")
            num_researches = len(num_researches)
        
        num_pag_next = num_researches//self.limit_showing_per_page
        researches_id = []
        for i in range(num_pag_next):
            researches_id.extend(self.__searches_on_page())
            self.__next_page()

        researches_id.extend(self.__searches_on_page())

        logger.debug(f"ids encontrados: {len(researches_id)}")
        logger.debug(f"ids encontrados na página: {researches_id}")
        return researches_id
    
    def __paper_title(self):
        xpath = "//div[@class='core-container']/h1"
        h1_title = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        
        if len(h1_title) != 1:
            raise ValueError(f"Expected exactly 1 matching div, but found {len(h1_title)}.")
        h1_title = h1_title[0]
        
        title = h1_title.text
        logger.debug(f"Title: {title}")
        return title
    
    def __paper_authors(self): 
        xpath = "//div[@class='contributors']//span[@class='authors']//span[@property='author']"
        span_authors = self.driver.find_elements(By.XPATH, xpath)
        authors = [author.text for author in span_authors]

        return authors
    
    def __paper_abstract(self):        
        xpath = "//div[@id='abstracts']//section[@id='abstract']//div"
        div_abstract = self.driver.find_element(By.XPATH, xpath)
        abstract = div_abstract.text
        
        return abstract

    def __paper_date(self): 
        xpath = "//div[@class='core-published']//span[@class='core-date-published']"
        span_date = self.driver.find_element(By.XPATH, xpath)
        date = span_date.text
        
        return date
        
    def __paper_doi(self):
        self.load_url("https://dl.acm.org/doi/10.1145/3691620.3695591")
        self.__allow_all_cookies()
    
    def __paper_keywords(self):
        section_terms = self.driver.find_element(By.ID, "sec-terms")
        self.driver.execute_script("arguments[0].scrollIntoView(true)", section_terms)

        xpath = "//section[@id='sec-terms']//div[@class='citation article__section article__index-terms']//ol[@class='rlist organizational-chart']/li"
        li_terms = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        
        keywords = []
        for li in li_terms:
            terms = li.text.split("\n")
            for term in terms:
                keywords.append(term)
        
        return keywords
                
    def __research_paper(self, id): 
        source_url = f"https://dl.acm.org/doi/{id}"
        self.restart_driver
        self.load_url(source_url)
        self.__allow_all_cookies()
        logger.debug("="*90)

        incomplete = False
        try:
            keywords = self.__paper_keywords() 
            logger.debug(f"Keywords: {keywords}") # OK
        except:
            logger.warning(f"[{id}] Failed to collect keywords.")
            keywords = None
            incomplete = True

        try: 
            date = self.__paper_date()
            logger.debug(f"Date: {date}") # OK
        except:
            logger.warning(f"[{id}] Failed to collect date.")
            date = None
            incomplete = True
        
        try:
            abstract = self.__paper_abstract()
            logger.debug(f"Abstract: {abstract}") # OK
        except:
            logger.warning(f"[{id}] Failed to collect abstract.")
            abstract = None
            incomplete = True
        
        try:
            authors = self.__paper_authors()
            logger.debug(f"Authors: {authors}") # OK
        except:  
            logger.warning(f"[{id}] Failed to collect authors.")
            authors = None
            incomplete = True
        
        research_paper = ResearchPaper(
            title=self.__paper_title(),
            date=date,
            abstract=abstract,
            DOI=id,
            source_url=source_url,
            authors=authors,
            keywords=keywords
        )
        self.quit_driver()
        return research_paper, incomplete

    def __fetch_paper(self, id, failed_urls, incomplete_papers): 
        url = f"https://dl.acm.org/doi/{id}"
        try:    
            with ACMSources() as temp_acm:
                paper, incomplete = temp_acm.__research_paper(id)
                if incomplete:
                    incomplete_papers[id] = paper
                    logger.warning(f"Paper de id={id} processado, porém incompleto.  URL: {url}")
                logger.debug(f"Paper de id={id} processado!")
                return paper
        except Exception as e:
            failed_urls.append(url)
            logger.error(f"Error processing role ID={id}| URL: {url} | Erro: {e}", exc_info=True)
            return None
            
    def __max_workers(self, num_elements): 
        max_workers_by_cpu = os.cpu_count() * 2
        if num_elements > max_workers_by_cpu:
            max_workers = max_workers_by_cpu
            return max_workers
        
        odd_numbers = [2,3,5,7]
        lower_value = None
        max_workers = None
        for odd in odd_numbers:
            lower_temp = num_elements//odd
            if lower_value is None:
                lower_value = lower_temp
                max_workers = odd
            elif lower_temp < lower_value:
                lower_value = lower_temp
                max_workers = odd
        
        if max_workers < max_workers_by_cpu:
            return max_workers

    def get_all_researches(self, url, max_workers=None): 
        self.load_url(url, wait_xpath="//div[@class='pull-right search-showing-results']")
        research_datas = self.__research_datas()
        num_researches = research_datas["num_results"]
        papers_ids = self.__all_searches_ids(num_researches)

        if max_workers is None:
            max_workers = self.__max_workers(num_researches)

        papers = {}
        failed_urls = []
        incomplete_papers = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_id = {ex.submit(self.__fetch_paper, id, failed_urls, incomplete_papers): id for id in papers_ids}
            for future in as_completed(future_to_id):
                paper_id = future_to_id[future]
                paper = future.result()
                if paper:
                    papers[paper_id] = paper

        research = Research(
            num_results = research_datas["num_results"],
            keywords = research_datas["keywords"],
            years = research_datas["years"],
            publisher = "ACM",
            url = url,
            content_type = ["Article", "Conference Paper", "Journal Article"],
            papers_urls = papers_ids,
            failed_urls = failed_urls,
            papers = papers,
            incomplete_papers = incomplete_papers
        )

        if failed_urls:
            logger.warning(f"Total URLs with error: {len(failed_urls)}")
            for fail in failed_urls:
                logger.warning(f"Failed to parse: {fail}")
        
        return research
    
if __name__ == "__main__":
    import time
    try: 
        start_time = time.time()
        # IEEE
        ##############################################################################
        #url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Full%20Text%20.AND.%20Metadata%22:requirements%20elicitation)%20AND%20(%22All%20Metadata%22:language%20model)%20AND%20(%22Abstract%22:agile)&highlight=true&returnType=SEARCH&matchPubs=true&pageNumber=1&ranges=2020_2025_Year&returnFacets=ALL"
        #url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Abstract%22:gile%20requirements)%20AND%20(%22Full%20Text%20.AND.%20Metadata%22:usage%20scenario)%20OR%20(%22Full%20Text%20.AND.%20Metadata%22:user%20stories)%20AND%20(%22Abstract%22:language%20models)%20AND%20(%22All%20Metadata%22:elicitation)&ranges=2020_2025_Year"
        #url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Abstract%22:requirements%20elicitation)%20AND%20(%22All%20Metadata%22:language%20model)%20AND%20(%22Abstract%22:agile)&ranges=2020_2025_Year"
        url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Full%20Text%20.AND.%20Metadata%22:requirements%20elicitation)%20AND%20(%22Abstract%22:language%20model)%20AND%20(%22Abstract%22:requirements%20generation)&ranges=2022_2025_Year"
        
        #with IEEESources() as ieee:
        #    research = ieee.get_all_researches(url)
        #    logger.info(f"Total de resultados: {research.num_results}")
        #    logger.info(f"Palavras-chave: {research.keywords}")
        #    logger.info(f"Anos: {research.years}")
        #    logger.info(f"Publisher: {research.publisher}")
        #    logger.info(f"Tipo de conteúdo: {research.content_type}")
        #    logger.info(f"URL: {research.url}")
        #    logger.info(f"Número de artigos encontrados: {len(research.papers)}")
        #############################################################################
        
        #url = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=all&field1=AllField&text1=requirements+elicitation&field2=Abstract&text2=language+model&field3=Abstract&text3=agile&AfterMonth=5&AfterYear=2020&BeforeMonth=5&BeforeYear=2025"
        url = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&field1=AllField&text1=requirements+elicitation&field2=Abstract&text2=language+model&field3=Abstract&text3=requirements+generation&field4=Fulltext&text4=user+stories&field5=Fulltext&text5=user+story&field6=Fulltext&text6=agile&AfterMonth=1&AfterYear=2022&BeforeMonth=5&BeforeYear=2025"
        with ACMSources() as acm:
            research = acm.get_all_researches(url)
            logger.info(f"Total de resultados: {research.num_results}")
            logger.info(f"Palavras-chave: {research.keywords}")
            logger.info(f"Anos: {research.years}")
            logger.info(f"Publisher: {research.publisher}")
            logger.info(f"Tipo de conteúdo: {research.content_type}")
            logger.info(f"URL: {research.url}")
            logger.info(f"Número de artigos encontrados: {len(research.papers)}")
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Tempo total de execução: {elapsed_time:.2f} segundos")
        
        with open(os.path.join("webscraping", "data","acm_research_data_1.pkl"), "wb") as file:
            pickle.dump(research, file)
    
    except Exception as e:
        logger.error(f"Erro ao executar scraping: {e}", exc_info=True)