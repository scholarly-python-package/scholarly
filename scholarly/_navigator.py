from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from ._proxy_generator import ProxyGenerator

from typing import Callable
from bs4 import BeautifulSoup

import codecs
import hashlib
import logging
import random
import time
import requests
import tempfile
import stem.process
from requests.exceptions import Timeout
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import WebDriverException, UnexpectedAlertPresentException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlparse
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from .publication_parser import _SearchScholarIterator
from .author_parser import AuthorParser
from .publication_parser import PublicationParser
from .data_types import Author

class DOSException(Exception):
    """DOS attack was detected."""

class MaxTriesExceededException(Exception):
    pass

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class Navigator(object, metaclass=Singleton):
    """A class used to navigate pages on google scholar."""

    def __init__(self):
        super(Navigator, self).__init__()
        logging.basicConfig(filename='scholar.log', level=logging.CRITICAL)
        self.logger = logging.getLogger('scholarly')
        self._TIMEOUT = 5
        self._max_retries = 5
        self._session = None
        self.pm = ProxyGenerator()
        self._session = self.pm.get_session()
        self.got_403 = False


    def set_logger(self, enable: bool):
        """Enable or disable the logger for google scholar."""

        self.logger.setLevel((logging.INFO if enable else logging.CRITICAL))

    def set_timeout(self, timeout: int):
        """Set timeout period in seconds for scholarly"""
        if timeout >= 0:
            self._TIMEOUT = timeout

    def use_proxy(self, pg: ProxyGenerator):
        if pg is not None:
            self.pm = pg
        else:
            self.pm = ProxyGenerator()
        self._session = self.pm.get_session()

    def _new_session(self):
        self.got_403 = False
        self._session = self.pm._new_session()

    
    def _get_page(self, pagerequest: str) -> str:
        """Return the data from a webpage

        :param pagerequest: the page url
        :type pagerequest: str
        :returns: the text from a webpage
        :rtype: {str}
        :raises: Exception
        """
        self.logger.info("Getting %s", pagerequest)
        resp = None
        tries = 0
        timeout=self._TIMEOUT
        while tries < self._max_retries:
            try:
                w = random.uniform(1,2)
                time.sleep(w)
                resp = self._session.get(pagerequest, timeout=timeout)
                self.logger.info("Session proxy config is {}".format(self._session.proxies))

                has_captcha = self._requests_has_captcha(resp.text)

                if resp.status_code == 200 and not has_captcha:
                    return resp.text
                elif has_captcha:
                    self.logger.info("Got a captcha request.")
                    self._session = self.pm._handle_captcha2(pagerequest)
                    continue # Retry request within same session
                elif resp.status_code == 403:
                    self.logger.info(f"Got an access denied error (403).")
                    if not self.pm.has_proxy():
                        self.logger.info("No other connections possible.")
                        if not self.got_403:
                            self.logger.info("Retrying immediately with another session.")
                        else:
                            if not self.pm._use_luminati:
                                w = random.uniform(60, 2*60)
                                self.logger.info("Will retry after {} seconds (with another session).".format(w))
                                time.sleep(w)
                        self._new_session()
                        self.got_403 = True
                        
                        continue # Retry request within same session
                    else:
                        self.logger.info("We can use another connection... let's try that.")
                else:
                    self.logger.info(f"""Response code {resp.status_code}.
                                    Retrying...""")

            except DOSException:
                if not self.pm.has_proxy():
                    self.logger.info("No other connections possible.")
                    w = random.uniform(60, 2*60)
                    self.logger.info("Will retry after {} seconds (with the same session).".format(w))
                    time.sleep(w)
                    continue
            except Timeout as e:
                err = f"Timeout Exception %s while fetching page: %s" % (type(e).__name__, e.args)
                self.logger.info(err)
                if timeout < 3*self._TIMEOUT:
                    self.logger.info("Increasing timeout and retrying within same session.")
                    timeout = timeout + self._TIMEOUT
                    continue
                self.logger.info("Giving up this session.")
            except Exception as e:
                err = f"Exception %s while fetching page: %s" % (type(e).__name__, e.args)
                self.logger.info(err)
                self.logger.info("Retrying with a new session.")

            tries += 1
            self._session, timeout = self.pm.get_next_proxy(num_tries = tries, old_timeout = timeout)
        raise MaxTriesExceededException("Cannot Fetch from Google Scholar.")


    def _set_retries(self, num_retries: int) -> None:
        if (num_retries < 0):
            raise ValueError("num_retries must not be negative")
        self._max_retries = num_retries


    def _requests_has_captcha(self, text) -> bool:
        """Tests whether some html text contains a captcha.

        :param text: the webpage text
        :type text: str
        :returns: whether or not the site contains a captcha
        :rtype: {bool}
        """
        return self._has_captcha(
            lambda i : f'id="{i}"' in text,
            lambda c : f'class="{c}"' in text,
        )

    def _webdriver_has_captcha(self) -> bool:
        """Tests whether the current webdriver page contains a captcha.

        :returns: whether or not the site contains a captcha
        :rtype: {bool}
        """
        return self._has_captcha(
            lambda i : len(self.pm._get_webdriver().find_elements(By.ID, i)) > 0,
            lambda c : len(self.pm._get_webdriver().find_elements(By.CLASS_NAME, c)) > 0,
        )

    def _has_captcha(self, got_id, got_class) -> bool:
        _CAPTCHA_IDS = [
            "gs_captcha_ccl", # the normal captcha div
            "recaptcha", # the form used on full-page captchas
            "captcha-form", # another form used on full-page captchas
        ]
        _DOS_CLASSES = [
            "rc-doscaptcha-body",
        ]
        if any([got_class(c) for c in _DOS_CLASSES]):
            raise DOSException()
        return any([got_id(i) for i in _CAPTCHA_IDS])

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Return the BeautifulSoup for a page on scholar.google.com"""
        html = self._get_page('https://scholar.google.com{0}'.format(url))
        html = html.replace(u'\xa0', u' ')
        res = BeautifulSoup(html, 'html.parser')
        try:
            self.publib = res.find('div', id='gs_res_glb').get('data-sva')
        except Exception:
            pass
        return res

    def search_authors(self, url: str)->Author:
        """Generator that returns Author objects from the author search page"""
        soup = self._get_soup(url)
         
        author_parser = AuthorParser(self)
        while True:
            rows = soup.find_all('div', 'gsc_1usr')
            self.logger.info("Found %d authors", len(rows))
            for row in rows:
                yield author_parser.get_author(row)
            cls1 = 'gs_btnPR gs_in_ib gs_btn_half '
            cls2 = 'gs_btn_lsb gs_btn_srt gsc_pgn_pnx'
            next_button = soup.find(class_=cls1+cls2)  # Can be improved
            if next_button and 'disabled' not in next_button.attrs:
                self.logger.info("Loading next page of authors")
                url = next_button['onclick'][17:-1]
                url = codecs.getdecoder("unicode_escape")(url)[0]
                soup = self._get_soup(url)
            else:
                self.logger.info("No more author pages")
                break

    def search_publication(self, url: str,
                           filled: bool = False) -> PublicationParser:
        """Search by scholar query and return a single Publication object

        :param url: the url to be searched at
        :type url: str
        :param filled: Whether publication should be filled, defaults to False
        :type filled: bool, optional
        :returns: a publication object
        :rtype: {Publication}
        """
        soup = self._get_soup(url)
        res = PublicationParser(self, soup.find_all('div', 'gs_or')[0], 'scholar')
        if filled:
            res.fill()
        return res

    def search_publications(self, url: str) -> _SearchScholarIterator:
        """Returns a Publication Generator given a url

        :param url: the url where publications can be found.
        :type url: str
        :returns: An iterator of Publications
        :rtype: {_SearchScholarIterator}
        """
        return _SearchScholarIterator(self, url)

    def search_author_id(self, id: str, filled: bool = False) -> Author:
        """Search by author ID and return a Author object
        :param id: the Google Scholar id of a particular author
        :type url: str
        :param filled: If the returned Author object should be filled
        :type filled: bool, optional
        :returns: an Author object
        :rtype: {Author}
        """
        author_parser = AuthorParser(self)
        res = author_parser.get_author(id)
        if filled:
            res = author_parser.fill(res)
        else:
            res = author_parser.fill(res, sections=['basics'])
        return res

    def search_organization(self, url: str, fromauthor: bool) -> list:
        """Generate instiution object from author search page.
           if no results are found and `fromuthor` is True, then use the first author from the search
           to get institution/organization name.
        """
        soup = self._get_soup(url)
        rows = soup.find_all('h3', 'gsc_inst_res')
        if rows:
            self.logger.info("Found institution")

        res = []
        for row in rows:
            res.append({'Organization': row.a.text, 'id': row.a['href'].split('org=', 1)[1]})

        if rows == [] and fromauthor is True:
            try:
                auth = next(self.search_authors(url))
                authorg = self.search_author_id(auth.id).organization
                authorg['fromauthor'] = True
                res.append(authorg)
            except Exception:
                res = []

        return res
