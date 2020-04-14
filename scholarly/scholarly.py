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
import hashlib
import random
import json
from .publication.publication import Publication
from .author.author import Author


class Scholarly:
    __metaclass__ = ABCMeta

    def __init__(self, use_proxy, browser='chrome'):
        self.__use_proxy = use_proxy
        self.__session = None
        self.__browser = browser
        self.__URLS = json.load(open('./scholarly/urls.json', 'r'))
        gid = hashlib.md5(str(random.random()).encode('utf-8'))
        gid = gid.hexdigest()[:16]
        self.__URLS["COOKIES"] = {'GSP': 'ID={0}:CF=4'.format(gid)}


    def force_quit(self):
        self.__session.close()
        self.__session.quit()

    def URLS(self, address:str) -> str:
        return self.__URLS[address]
    
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
                soup = self._get_soup(self.URLS('HOST').format(url))
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
                soup = self._get_soup(self.URLS('HOST').format(url))
            else:
                break


    def _find_tag_class_name(self, __data, tag, text):
        elements = __data.find_all(tag)
        for element in elements:
            if 'class' in element.attrs and text in element.attrs['class'][0]:
                return element.attrs['class'][0]


    def search_single_pub(self, paper_title:str) -> Publication:
        """Search by scholar query and return a single Publication object"""
        url = self.URLS('PUBSEARCH').format(requests.utils.quote(paper_title))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return Publication(soup.find_all('div', 'gs_or')[0], self, 'scholar')


    def search_pubs_query(self, query:str):
        """Search by scholar query and return a generator of Publication objects"""
        url = self.URLS('PUBSEARCH').format(requests.utils.quote(query))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_scholar_soup(soup)


    def search_author(self, name:str):
        """Search by author name and return a generator of Author objects"""
        url = self.URLS('AUTHSEARCH').format(requests.utils.quote(name))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)


    def search_keyword(self, keyword:str):
        """Search by keyword and return a generator of Author objects"""
        url = self.URLS('KEYWORDSEARCH').format(requests.utils.quote(keyword))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)


    def search_pubs_custom_url(self, url:str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_scholar_soup(soup)


    def search_author_custom_url(self, url:str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/citation?q=...'"""
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)

class ScholarlyDefault(Scholarly):

    def __init__(self, use_proxy:bool):
        Scholarly.__init__(self, use_proxy)

        self.__session = requests.Session()
        if use_proxy:
            print("using proxy")
            self.__session.proxies = {
                "http": "socks5://{0}".format(self.URLS('PROXY')),
                "https": "socks5://{0}".format(self.URLS('PROXY'))
            }
    
    def _get_page(self, pagerequest:str) -> str:
        """Return the data for a page on scholar.google.com"""
        # Note that we include a sleep to avoid being kicked out by google
        time.sleep(5 + random.uniform(0, 5))
        resp = self.__session.get(
            pagerequest, 
            headers=self.URLS("HEADERS"), 
            cookies=self.URLS("COOKIES"))
        if resp.status_code == 200 and "captcha" not in resp.text:
            return resp.text
        elif resp.status_code == 503:
            raise Exception('Error: {0} {1}\n Captcha detected, consider using scholarly with selenium'
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
        super().__init__(self, use_proxy)

        if use_proxy:
            print("And a proxy")
            self.__session = self.get_new_chrome_agent()
        else:
            self.__session = webdriver.Chrome()


    def get_new_chrome_agent(self) -> webdriver.Chrome:

        chrome_options = webdriver.ChromeOptions()
        
        chrome_options.add_argument(self.URLS('PROXY'))
        
        #Makes the agent less predictable so it can't be detected easily
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_experimental_option(
            "excludeSwitches", 
            ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(
            random.randint(100, 1025), 
            random.randint(100, 1025))
        return driver


    def get_new_firefox_agent(self) -> webdriver.Firefox:
        #TODO implement firefox randomization
        options = webdriver.FirefoxProfile()
        options.set_preference('general.useragent.override', UserAgent().random)
        return webdriver.Firefox()


    def _handle_too_many_requests(self):
        """ Google Scholar responded with status too many requests. If we are
        using TOR, renew your identity. If we are not using tor sleep until we
        are allowed to request again."""

        if self.__session is not None:
            self.__session.close()
            self.__session.quit()
        
        with Controller.from_port(port = 9151) as controller:
            print("Refreshing proxy...")
            controller.authenticate(password = "")
            controller.signal(Signal.NEWNYM)
        self.__session = self.get_new_chrome_agent()


    def _get_page(self, pagerequest:str) -> str:
        flags = ["Please show you're not a robot",
        "but your computer or network may be sending automated queries",
        "have detected unusual traffic from your computer"]
        time.sleep(2) #just in case we get a good TOR server we wait to not overload it

        # Tries to retrieve the paper until no captcha is shown
        while True:
            try:
                self.__session.get(pagerequest)
                wait = WebDriverWait(self.__session, 100)
                text = self.__session.page_source
                if any([i in text for i in flags]):
                    self._handle_too_many_requests()
                else: 
                    break
            except TimeoutException:
                break

        return self.__session.page_source

def get_scholarly_instance(use_proxy:bool=False, use_selenium:bool=False) -> ScholarlySelenium or ScholarlyDefault:
    if use_selenium:
        return ScholarlySelenium(use_proxy)
    else:
        return ScholarlyDefault(use_proxy)
