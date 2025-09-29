from __future__ import annotations

import os
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from logger import logger

class WebDriverConfig:
    """
    Configuration and management of a Selenium WebDriver for web scraping.
    """
    def __init__(self, *, headless: bool = False, wait_time: int = 17, show_limit: int = 25):
        """
        Initialize the WebDriverConfig with options for headless mode, wait time, and show limit.
        """
        self._headless = bool(headless)
        self._wait_time = int(wait_time)
        self._show_limit = int(show_limit)
        self._options: Optional[Options] = None
        self._driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None
    
    def __enter__(self): 
        return self
    
    def __exit__(self, *_): 
        self.quit()
        
    @property
    def options(self) -> Options:
        """
        Get or create the Chrome options for the WebDriver.
        """
        if self._options is None:
            os.environ["WDM_LOG_LEVEL"] = "0"
            o = Options()
            if self._headless:
                o.add_argument("--headless=new")
                o.add_argument("--disable-gpu")
            o.add_argument("--disable-dev-shm-usage")
            o.add_argument("--no-sandbox")
            self._options = o
        return self._options

    def _new_driver(self) -> webdriver.Chrome:
        """
        Create and return a new instance of Chrome WebDriver with the configured options.
        """
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=self.options)
    
    @property
    def driver(self) -> webdriver.Chrome:
        """
        Get the WebDriver instance, creating it if it doesn't exist.
        """
        if self._driver is None:
            try:
                self._driver = self._new_driver()
                self._wait = WebDriverWait(self._driver, self._wait_time)
            except Exception as e:
                logger.error(f"Error while creating the driver: {e}", exc_info=True)
        return self._driver
    
    @property
    def wait(self) -> WebDriverWait:
        """
        Get the WebDriverWait instance, creating it if it doesn't exist.
        """
        if self._wait is None: 
            self._wait = WebDriverWait(self.driver, self._wait_time)
        return self._wait
    
    def quit(self) -> None:
        """
        Quit the WebDriver and clean up resources.
        """
        driver = self._driver 
        self._driver = None
        self._wait = None

        if driver is None:
            return
        
        try:
            driver.quit()
        except Exception as e:
            logger.warning(f"Error while closing the driver: {e}")
        
    def restart(self) -> None:
        """
        Close and re-create the driver and wait objects.
        """
        self.quit()
        _ = self.driver

    def load(self, url: str, *, wait_xpath: str | None = None) -> None:
        """
        Load a URL in the WebDriver and optionally wait for an element specified by wait_xpath.
        """
        self.driver.get(url)
        if wait_xpath:
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
            except Exception as e:
                logger.error(f"Error while waiting for element {wait_xpath}: {e}")
            
    def wait_click(self, xpath: str, ) -> None:
        """
        Wait until element is clickable, scroll into view, and click.
        """
        try:
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
            el.click()
        except Exception as e:
            logger.error(f"Error while clicking element {xpath}: {e}")

    def wait_all(self, xpath: str)-> list[webdriver.remote.webelement.WebElement]:
        """
        Wait until all elements located by XPATH are present and return them.
        """
        return self.wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))

    @property
    def show_limit(self) -> int: 
        """
        Get the show limit for search results.
        """
        return self._show_limit

    @staticmethod
    def compute_workers(n: int) -> int:
        """
        Compute an optimal number of worker threads based on CPU count and input n.
        """
        cap = max((os.cpu_count() or 2) * 2, 2)
        if n <= 1: return 1
        if n >= cap: return cap
        for k in (8,7,6,5,4,3,2):
            if n % k == 0: return min(k, cap)
        return min(n, cap)