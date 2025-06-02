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
from lisa.sub_lisa.logger import logger
import os

from dataclasses import dataclass, field 
from typing import List

@dataclass
class ResearchPaper:
    title: str
    date: int
    abstract: str
    publisher: str    
    DOI: str
    source_url: str
    authors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
@dataclass
class Research:
    num_results: int # ok
    keywords: str # ok
    years: str # ok
    publisher: str 
    url: str
    content_type: List[str] = field(default_factory=list) # ok
    papers: List[ResearchPaper] = field(default_factory=list)

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

    def research_datas(self): # Ok
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
    
    def searches_on_page(self):
        xpath = "//xpl-results-list/div[@class='List-results-items']"
        researches = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        researches_id = [x.get_attribute("id") for x in researches]
        
        return researches_id
    
    def next_page(self, num_pag):
        xpath = f"//div[@class='pagination-bar hide-mobile text-base-md-lh']//button[@class='stats-Pagination_arrow_next_{num_pag}']"
        next_button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        next_button.click()
        
    def all_searches_ids(self, num_researches): #OK
        if isinstance(num_researches, list):
            logger.info("The argument type is a list, which is not ideal. The ideal type is an integer. The value will be converted to the number of elements in the list.")
            num_researches = len(num_researches)
            
        num_pag_next = num_researches//self.limit_showing_per_page
        researches_id = []
        for i in range(num_pag_next):
            researches_id.extend(self.searches_on_page())
            self.next_page(i+2)
        researches_id.extend(self.searches_on_page())
        return researches_id

    def paper_title(self):
        xpath = "//h1[contains(@class, 'document-title')]//span"
        span_title = self.driver_wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        
        title = span_title.text
        return title
    
    def paper_authors(self): 
        xpath = "//div[contains(@class, 'authors-container')]//span[contains(@class, 'authors-info')]"
        span_authors = self.driver.find_elements(By.XPATH, xpath)
        
        authors = []
        for author in span_authors:
            author = author.text
            if author[-1] == ";":
                author = author[:-1]
            authors.append(author)
        
        return authors
    
    def paper_abstract(self):        
        xpath = "//div[@class='u-mb-1']"
        span_abstract = self.driver.find_element(By.XPATH, xpath)
        full_text = span_abstract.text
        abstract_text = full_text.split("\n")[1]
        
        return abstract_text
    
    def paper_date(self): 
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
        
    def paper_doi(self):
        xpath = "//div[@class='u-pb-1 stats-document-abstract-doi']"
        div_doi = self.driver.find_element(By.XPATH, xpath)
        doi = div_doi.text.replace("DOI: ", "")

        return doi
    
    def paper_publisher(self):
        xpath = "//div[@class='u-pb-1 doc-abstract-publisher']//button//span"
        span_publisher = self.driver.find_elements(By.XPATH, xpath)
        publisher = span_publisher[0].text
        
        return publisher
    
    def __close_cookie_banner(self):
        try: 
            xpath ="//button[contains(., 'Accept')]"
            accept_button = self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            accept_button.click()
        except NoSuchElementException:
            pass  
    
    def paper_keywords(self):
        xpath = "//button[@id='keywords']"
        keywords_button = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", keywords_button)
        keywords_button = self.driver_wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        #self.__close_cookie_banner()
        keywords_button.click()
        
        xpath = "//ul[@class='doc-keywords-list stats-keywords-list']/li[@class='doc-keywords-list-item']//ul[@class='u-mt-1 u-p-0 List--no-style List--inline']"
        
        ul_elem_temp = self.driver_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        all_keywords = []
        
        for ul in ul_elem_temp:
            ul_text = ul.text.strip()
            if ul_text != "":
                keywords = ul_text.split("\n,\n") #Error em https://ieeexplore.ieee.org/document/10143519 
                all_keywords.append(keywords)
        
        return all_keywords
                
    def research_paper(self, id):
        source_url = f"https://ieeexplore.ieee.org/document/{id}"
        self.load_url(source_url)
        
        keywords = self.paper_keywords()
 
        research_paper = ResearchPaper(
            title = self.paper_title(),
            date = self.paper_date(),
            abstract = self.paper_abstract(),
            publisher = self.paper_publisher(),    
            DOI = self.paper_doi(),
            source_url = source_url, 
            authors = self.paper_authors(),
            keywords = keywords
        )
        
        return research_paper

    def __fetch_paper(self, id, failed_urls): 
        try:
            with IEEESources() as temp_ieee:
                paper = temp_ieee.research_paper(id)
                logger.debug(f"Paper de id={id} processado!")
                return paper
        except Exception as e:
            url = f"https://ieeexplore.ieee.org/document/{id}"
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
        research_datas = self.research_datas() #ok
        num_researches = research_datas["num_results"] #ok
        papers_ids = self.all_searches_ids(num_researches) #ok
        
        if max_workers is None:
            max_workers = self.__max_workers(num_researches)
            
        papers = []
        failed_urls = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_id = {ex.submit(self.__fetch_paper, id, failed_urls): id for id in papers_ids}
            for future in as_completed(future_to_id):
                paper = future.result()
                if paper:
                    papers.append(paper)
        
        research = Research(
            num_results = research_datas["num_results"],
            keywords = research_datas["keywords"],
            years = research_datas["years"],
            publisher = "IEEE",
            url = url,
            content_type= research_datas["content_type"],
            papers=papers
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
        url = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Full%20Text%20.AND.%20Metadata%22:requirements%20elicitation)%20AND%20(%22All%20Metadata%22:language%20model)%20AND%20(%22Abstract%22:agile)&highlight=true&returnType=SEARCH&matchPubs=true&pageNumber=1&ranges=2020_2025_Year&returnFacets=ALL"

        with IEEESources() as ieee:
            research = ieee.get_all_researches(url)
            logger.info(f"Total de resultados: {research.num_results}")
            logger.info(f"Palavras-chave: {research.keywords}")
            logger.info(f"Anos: {research.years}")
            logger.info(f"Publisher: {research.publisher}")
            logger.info(f"Tipo de conteúdo: {research.content_type}")
            logger.info(f"URL: {research.url}")
            logger.info(f"Número de artigos encontrados: {len(research.papers)}")
    
        elapsed_time = time.time() - start_time
        logger.debug(f"Tempo total de execução: {elapsed_time:.2f} segundos")
    
    except Exception as e:
        logger.error(f"Erro ao executar scraping: {e}", exc_info=True)