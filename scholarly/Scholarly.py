"""scholarly.py"""

from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
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
if __name__ == '__main__':
    from Author import Author
    from Publication import Publication
    from templates import urls
else:
    from .Author import Author
    from .Publication import Publication
    from .templates import urls


class Scholarly:
    """[summary]

    [description]
    :param __metaclass__: ABCMeta
    :type __metaclass__: ABCMeta
    """
    __metaclass__ = ABCMeta

    def __init__(self, use_proxy:bool=True, browser:str='chrome'):
        """Constructor Method
        :param use_proxy: whether or not to use proxy
        :type use_proxy: bool, optional
        :param browser: browser to be used, defaults to 'chrome'
        :type browser: str, optional
        """
        self.__use_proxy = use_proxy
        self.__session = None
        self.__browser = browser
        self.__URLS = urls
        gid = hashlib.md5(str(random.random()).encode('utf-8'))
        gid = gid.hexdigest()[:16]
        self.__URLS["COOKIES"] = {'GSP': 'ID={0}:CF=4'.format(gid)}

    @property
    def use_proxy(self) -> bool:
        """Gets use proxy value
        
        [description]
        :returns: a boolean indicating if proxy is being used
        :rtype: {bool}
        """
        return self.__use_proxy

    def URLS(self, address: str) -> str:
        """[summary]
        
        [description]
        :param address: the id of the url to be retrieved
        :type address: str
        :returns: an url
        :rtype: {str}
        """
        return self.__URLS[address]

    def force_quit(self):
        """Quits the session"""
        try:
            self.session.quit()
        except Exception as e:
            raise

    @abstractmethod
    def _get_page(self, pagerequest):
        pass

    @abstractmethod
    def _get_new_session(self):
        pass

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, value):
        """Sets the value of session
        :param value: a webdriver instance or Session instance
        :type value: {webdriver.Firefox, webdriver.Chrome, requests.Session}
        """
        assert (isinstance(value, webdriver.Firefox) or
                isinstance(value, webdriver.Chrome) or
                isinstance(value, requests.Session))
        self.__session = value

    def _has_captcha(self, text):
        flags = ["Please show you're not a robot",
                 "network may be sending automated queries",
                 "have detected unusual traffic from your computer"]

        if any([i in text for i in flags]):
            return True
        return False

    def _tor_refresher(self, ) -> webdriver:
        """Refreshes TOR node"""
        with Controller.from_port(port=9151) as controller:
            print("Refreshing proxy...")
            controller.authenticate(password="")
            controller.signal(Signal.NEWNYM)

    def _get_soup(self, pagerequest: str) -> BeautifulSoup:
        """Returns an html page parsed as a BeautifulSoup

        Arguments:
           pagerequest {str} -- a string with the address to be retrieved

        Returns:
            BeautifulSoup -- a parsed html
        """
        html = self._get_page(pagerequest)
        html = html.replace(u'\xa0', u' ')
        return BeautifulSoup(html, 'html.parser')

    def __search_scholar_soup(self, soup):
        """Generator that returns Publication objects from the search page"""
        while True:
            for row in soup.find_all('div', 'gs_or'):
                yield Publication(row, self, 'scholar')
            if soup.find(class_='gs_ico gs_ico_nav_next'):
                url = soup.find(class_='gs_ico gs_ico_nav_next').parent['href']
                soup = self._get_soup(self.URLS('HOST').format(url))
            else:
                break

    def __search_citation_soup(self, soup):
        """Generator that returns Author objects from the author search page"""
        while True:
            for row in soup.find_all('div', 'gsc_1usr'):
                yield Author(row, self)
            next_button = soup.find(
                class_="""gs_btnPR gs_in_ib gs_btn_half
                gs_btn_lsb gs_btn_srt gsc_pgn_pnx""")
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

    def search_single_pub(self, paper_title: str) -> Publication:
        """Search by scholar query and return a single Publication object"""
        url = self.URLS('PUBSEARCH').format(requests.utils.quote(paper_title))
        soup = self._get_soup(self.URLS('HOST').format(url))
        self.__URLS['PUBLIB'] = soup.find(
            'div', id='gs_res_glb').get('data-sva')
        return Publication(soup.find_all('div', 'gs_or')[0], self, 'scholar')

    def search_pubs_query(self, query: str):
        """Run query and return a generator of Publication objects"""
        url = self.URLS('PUBSEARCH').format(requests.utils.quote(query))
        soup = self._get_soup(self.URLS('HOST').format(url))
        self.__URLS['PUBLIB'] = soup.find(
            'div', id='gs_res_glb').get('data-sva')
        return self.__search_scholar_soup(soup)

    def search_author(self, name: str):
        """Search by author name and return a generator of Author objects"""
        url = self.URLS('AUTHSEARCH').format(requests.utils.quote(name))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)

    def search_keyword(self, keyword: str):
        """Search by keyword and return a generator of Author objects"""
        url = self.URLS('KEYWORDSEARCH').format(requests.utils.quote(keyword))
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)

    def search_pubs_custom_url(self, url: str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_scholar_soup(soup)

    def search_author_custom_url(self, url: str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/citation?q=...'"""
        soup = self._get_soup(self.URLS('HOST').format(url))
        return self.__search_citation_soup(soup)


class _ScholarlyDefault(Scholarly):

    def __init__(self, use_proxy: bool):
        print("Using Scholarly with Requests")
        super().__init__(self, use_proxy)
        self.session = self._get_new_session(browser)

    def _get_new_session(self):
        self._tor_refresher()

        sess = requests.Session()

        if self.use_proxy:
            print("Using proxy")
            sess.proxies = {
                "http": self.URLS('PROXY'),
                "https": self.URLS('PROXY')
            }

        return sess

    def _handle_too_many_requests(self):
        if self.use_proxy:
            self._tor_refresher()
            return self.get_new_session
        else:
            print("""Too many requests from scholarly. Consider using proxy
                      and/or scholarly with selenium. See you tomorrow...""")
            now = datetime.now()
            now_sec = now.minute * 60 + now.second + now.hour * 3600
            time.sleep(24 * 3600 - now_sec)

    def _get_page(self, pagerequest: str) -> str:
        time.sleep(2 + random.uniform(0, 3))
        searching = True
        resp = None

        while searching:
            resp = self.session.get(
                pagerequest,
                headers={'User-agent': UserAgent().random},
                cookies=self.URLS("COOKIES"))

            searching = self._has_captcha(resp.text)
            if searching:
                print("""Captcha or error detected,
                    consider using scholarly with Selenium and a proxy""")
                self.session = self._handle_too_many_requests()

        return resp.text


class _ScholarlySelenium(Scholarly):

    def __init__(self, use_proxy: bool, browser='chrome'):
        print("Using Scholarly with Selenium")
        super().__init__(self, use_proxy)
        self.__browser = browser
        self.session = self._get_new_session(browser)

    def _get_new_session(self, browser: str = 'chrome') -> webdriver:
        """Creates a new webdriver according to the browser selected
        
        :param browser: the browser to be used, either
            'chrome' or 'firefox', defaults to 'chrome'
        :type browser: str, optional
        :returns: an instance of a webdriver.Chrome or webdriver.Firefox
        :rtype: {webdriver}
        :raises: Exception
        """
        if browser == 'chrome':
            return self._get_new_chrome_agent(self.use_proxy)
        elif browser == 'firefox':
            return self._get_new_firefox_agent(self.use_proxy)
        else:
            raise Exception(
                "Browser not supported, please use 'chrome' or 'firefox'")

    def _get_new_chrome_agent(self,
                              use_proxy: bool = True) -> webdriver.Chrome:
        """Creates a Chrome based agent

        The agent receives a randomized window and agent.
        Optimized to minimized detection by the scraped server
        :param use_proxy: whether or not to use proxy, defaults to True
        :type use_proxy: bool, optional
        :returns: a chrome based webdriver
        :rtype: {webdriver.Chrome}
        """
        chrome_options = webdriver.ChromeOptions()

        if use_proxy:
            chrome_options.add_argument(
                '--proxy-server={}'.format(self.URLS('PROXY')))

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

    def _get_new_firefox_agent(self,
                               use_proxy: bool = True) -> webdriver.Firefox:
        """Creates a Firefox based agent

        The agent receives a randomized window and agent.
        Optimized to minimized detection by the scraped server

        Keyword Arguments:
            use_proxy {bool} -- whether or not to use proxy (default: {True})

        Returns:
            webdriver.Firefox -- a chrome based webdriver
        """
        proxy = Proxy({
            "proxyType": ProxyType.MANUAL,
            "httpProxy": self.URLS('PROXY'),
            "httpsProxy": self.URLS('PROXY'),
            "socksProxy": self.URLS('PROXY'),
            "sslProxy": self.URLS('PROXY'),
            "ftpProxy": self.URLS('PROXY'),
            "noProxy": ""
        })

        profile = webdriver.FirefoxProfile()
        profile.set_preference("dom.webdriver.enabled", False)
        profile.set_preference('useAutomationExtension', False)
        profile.set_preference(
            "general.useragent.override", UserAgent().random)
        profile.update_preferences()

        if use_proxy:
            return webdriver.Firefox(firefox_profile=profile, proxy=proxy)
        else:
            return webdriver.Firefox(firefox_profile=profile)

    def _webdrive_refresher(self):
        if self.session is not None:
            self.session.quit()

        self._tor_refresher()

        return self._get_new_session(self.__browser)

    def _get_page(self, pagerequest: str) -> str:

        # just in case we get a good TOR server we wait to not overload it
        time.sleep(2)
        searching = True
        # Tries to retrieve the page until no captcha is shown
        while searching:
            try:
                self.session.get(pagerequest)
                wait = WebDriverWait(self.session, 100)
                text = self.session.page_source
                if self._has_captcha(text):
                    self._tor_refresher()
                    self.session = self._get_new_session(browser)
                else:
                    searching = False
            except TimeoutException:
                raise Exception("Server is too slow, stopping search")

        return self.session.page_source


def get_scholarly_instance(use_proxy: bool = True,
                           use_selenium: bool = True,
                           browser: str = 'chrome') -> Scholarly:
    """Returns Selenium or Session version of Scholarly
    
    :param use_proxy: whether or not to use a proxy, defaults to False
    :type use_proxy: bool, optional
    :param use_selenium: wether or not to use Selenium, defaults to True
    :type use_selenium: bool, optional
    :param browser: browser to be used [chrome, firefox], defaults to 'chrome'
    :type browser: str, optional
    """
    
    if use_selenium:
        return _ScholarlySelenium(use_proxy, browser)
    else:
        return _ScholarlyDefault(use_proxy)
