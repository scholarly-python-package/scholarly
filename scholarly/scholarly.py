"""scholarly.py"""

from __future__ import absolute_import, division, print_function, unicode_literals

from bs4 import BeautifulSoup

import arrow
import bibtexparser
import codecs
import pprint
import random
import re
import requests
import sys
import time
from abc import ABCMeta, abstractmethod
from stem import Signal
from stem.control import Controller
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from fake_useragent import UserAgent

if __name__ != '__main__':
    from .confs import *
    from .publication import Publication
    from .author import *
else:
	from confs import *
	from publication import Publication
	from author import Author

import hashlib
import random


_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36"
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': _USER_AGENT,
    'accept': 'text/html,application/xhtml+xml,application/xml'
    }
_HOST = "https://scholar.google.com"
_AUTHSEARCH = "/citations?view_op=search_authors&hl=en&mauthors={0}"
_CITATIONAUTH = "/citations?user={0}&hl=en"
_CITATIONPUB = "/citations?view_op=view_citation&citation_for_view={0}"
_KEYWORDSEARCH = "/citations?view_op=search_authors&hl=en&mauthors=label:{0}"
_PUBSEARCH = "/scholar?hl=en&q={0}"
_SCHOLARPUB = "/scholar?oi=bibs&hl=en&cites={0}"

_CAPTCHA = "iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']"

_CITATIONAUTHRE = r"user=([\w-]*)"
_CITATIONPUBRE = r"citation_for_view=([\w-]*:[\w-]*)"
_SCHOLARCITERE = r"gs_ocit\(event,\'([\w-]*)\'"
_SCHOLARPUBRE = r"cites=([\w-]*)"
_EMAILAUTHORRE = r"Verified email at "

_pAGESIZE = 100
_PROXY = "127.0.0.1:9150"

class Scholarly:
    __metaclass__ = ABCMeta

    def __init__(self, use_proxy, browser='chrome'):
        self.__use_proxy = use_proxy
        self.__session = None
        self.__browser = browser

    

    @abstractmethod
    def _get_page(self, pagerequest):
        pass

    def _get_soup(self, pagerequest:str):
        """Return the BeautifulSoup for a page on scholar.google.com"""
        html = self._get_page(pagerequest)
        html = html.replace(u'\xa0', u' ')
        return BeautifulSoup(html, 'html.parser')


    def _search_scholar_soup(self, soup):
        """Generator that returns Publication objects from the search page"""
        while True:
            for row in soup.find_all('div', 'gs_or'):
                yield Publication(row, self, 'scholar')
            if soup.find(class_='gs_ico gs_ico_nav_next'):
                url = soup.find(class_='gs_ico gs_ico_nav_next').parent['href']
                soup = self._get_soup(_HOST+url)
            else:
                break


    def _search_citation_soup(self, soup):
        """Generator that returns Author objects from the author search page"""
        while True:
            for row in soup.find_all('div', 'gsc_1usr'):
                yield Author(row, self)
            next_button = soup.find(class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
            if next_button and 'disabled' not in next_button.attrs:
                url = next_button['onclick'][17:-1]
                url = codecs.getdecoder("unicode_escape")(url)[0]
                soup = self._get_soup(_HOST+url)
            else:
                break

    def _find_tag_class_name(self, __data, tag, text):
        elements = __data.find_all(tag)
        for element in elements:
            if 'class' in element.attrs and text in element.attrs['class'][0]:
                return element.attrs['class'][0]


    def search_single_pub(self, paper_title:str) -> Publication:
        """Search by scholar query and return a single Publication object"""
        url = _PUBSEARCH.format(requests.utils.quote(paper_title))
        soup = self._get_soup(_HOST+url)
        return Publication(soup.find_all('div', 'gs_or')[0], self, 'scholar')


    def search_pubs_query(self, query:str):
        """Search by scholar query and return a generator of Publication objects"""
        url = _PUBSEARCH.format(requests.utils.quote(query))
        soup = self._get_soup(_HOST+url)
        return self.__search_scholar_soup(soup)


    def search_author(self, name:str):
        """Search by author name and return a generator of Author objects"""
        url = _AUTHSEARCH.format(requests.utils.quote(name))
        soup = self._get_soup(_HOST+url)
        return self.__search_citation_soup(soup)


    def search_keyword(self, keyword:str):
        """Search by keyword and return a generator of Author objects"""
        url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
        soup = self._get_soup(_HOST+url)
        return self.__search_citation_soup(soup)


    def search_pubs_custom_url(self, url:str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        soup = self._get_soup(_HOST+url)
        return self.__search_scholar_soup(soup)


    def search_author_custom_url(self, url:str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/citation?q=...'"""
        soup = self._get_soup(_HOST+url)
        return self.__search_citation_soup(soup)

class ScholarlyDefault(Scholarly):

    def __init__(self, use_proxy:bool):
        Scholarly.__init__(self, use_proxy)

        self.__session = requests.Session()
        if use_proxy:
            print("using proxy")
            self.__session.proxies = {
                "http": "socks5://{0}".format(_PROXY),
                "https": "socks5://{0}".format(_PROXY)
            }
    
    def _get_page(self, pagerequest:str) -> str:
        """Return the data for a page on scholar.google.com"""
        # Note that we include a sleep to avoid being kicked out by google
        time.sleep(5 + random.uniform(0, 5))
        resp = self.__session.get(pagerequest, headers=_HEADERS, cookies=_COOKIES)
        if resp.status_code == 200 and "captcha" not in resp.text:
            return resp.text
        elif resp.status_code == 503:
            raise Exception('Error: {0} {1}\nCaptcha detected, consider using scholarly with selenium'
                    .format(resp.status_code, resp.reason))
        elif resp.status_code == 429:
            self._handle_too_many_requests()
            self._get_page(pagerequest)
        elif resp.status_code == 200 and "captcha" in resp.text:
            raise NotImplementedError(
                    "Captcha detected, consider using scholarly with selenium")
        else:
            raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))

class ScholarlySelenium(Scholarly):

    def __init__(self, use_proxy:bool) -> None:
        print("Using Scholarly with Selenium")
        Scholarly.__init__(self, use_proxy)

        if use_proxy:
            print("And a proxy")
            self.__session = self.get_new_chrome_agent()
        else:
            self.__session = webdriver.Chrome()


    def get_new_chrome_agent(self) -> webdriver.Chrome:
        # if self.__session is not None:
        #     try:
        #         self.__session.quit()
        #     except:
        #         raise

        chrome_options = webdriver.ChromeOptions()
        
        chrome_options.add_argument(f"--proxy-server=socks5://{_PROXY}")
        
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(random.randint(100, 1025), random.randint(100, 1025))
        return driver


    def get_new_firefox_agent(self) -> webdriver.Firefox:
        options = webdriver.FirefoxProfile()
        options.set_preference('general.useragent.override', UserAgent().random)



    def _handle_too_many_requests(self):
        """ Google Scholar responded with status too many requests. If we are
        using TOR, renew your identity. If we are not using tor sleep until we
        are allowed to request again."""

        # if self.__use_proxy:
        if self.__session is not None:
            self.__session.close()
            self.__session.quit()
        
        with Controller.from_port(port = 9151) as controller:
            print("Refreshing proxy...")
            controller.authenticate(password = "")
            controller.signal(Signal.NEWNYM)
            #controller.new_circuit(await_build=True, timeout=60)
            #controller.signal(Signal.NEWNYM)
        self.__session = self.get_new_chrome_agent()

        # else:
        #     print("""Too many requests from scholarly. Consider using proxy
        #           and/or scholarly with selenium. Waiting till the end of the
        #           day to continue.""")
        #     now = datetime.now()
        #     now_sec = now.minute * 60 + now.second + now.hour * 3600
        #     time.sleep(24 * 3600 - now_sec)


    def _get_page(self, pagerequest:str) -> str:
        print(f"Retrieving: {pagerequest}")
        """Return the data for a page on scholar.google.com.
        Note that we include a sleep to avoid overloading the scholar server"""
        #wait_time = 5 + random.uniform(0, 5)
        flags = ["Please show you're not a robot",
        "but your computer or network may be sending automated queries",
        "have detected unusual traffic from your computer"]
        time.sleep(2)

        # Wait for captcha to show up
        while True:
            try:
                print(self.__session is None)
                self.__session.get(pagerequest)
                wait = WebDriverWait(self.__session, 100)
                text = self.__session.page_source
                #wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, _CAPTCHA)))
                if any([i in text for i in flags]):
                    self._handle_too_many_requests()
                else: 
                    break
            except TimeoutException:
                break

            # Wait for captcha to disapear, if no captcha has shown this does not block
            # wait = WebDriverWait(self.__session, 1000000000)
            # wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, _CAPTCHA)))

        # Obtain html body
        text = self.__session.page_source
        return text

def get_scholarly_instance(use_proxy:bool=False, use_selenium:bool=False) -> ScholarlySelenium or ScholarlyDefault:
    if use_selenium:
        return ScholarlySelenium(use_proxy)
    else:
        return ScholarlyDefault(use_proxy)
