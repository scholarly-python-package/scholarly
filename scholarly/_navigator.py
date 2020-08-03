from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
from .publication import _SearchScholarIterator
from .author import Author
from .publication import Publication

class DOSException(Exception):
    """DOS attack was detected."""


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
        logging.basicConfig(filename='scholar.log', level=logging.INFO)
        self.logger = logging.getLogger('scholarly')
        self._proxy_gen = None
        # If we use a proxy or Tor, we set this to True
        self._proxy_works = False
        self._use_luminaty = False
        # If we have a Tor server that we can refresh, we set this to True
        self._tor_process = None
        self._can_refresh_tor = False
        self._tor_control_port = None
        self._tor_password = None
        self._TIMEOUT = 5
        self._max_retries = 5
        self._session = None
        self._new_session()

    def __del__(self):
        if self._tor_process:
            self._tor_process.kill()
        self._close_session()

    def _get_webdriver(self):
        if self._webdriver:
            return self._webdriver

        if self._proxy_works:
            # Redirect webdriver through proxy
            caps = DesiredCapabilities.FIREFOX.copy()
            caps['proxy'] = {
                "httpProxy": self._session.proxies['http'],
                "ftpProxy": self._session.proxies['http'],
                "sslProxy": self._session.proxies['https'],
                "proxyType":"MANUAL",
            }
            self._webdriver = webdriver.Firefox(desired_capabilities = caps)
        else:
            self._webdriver = webdriver.Firefox()
        self._webdriver.get("https://scholar.google.com") # Need to pre-load to set cookies later

        # It might make sense to (pre)set cookies as well, e.g., to set a GSP ID.
        # However, a limitation of webdriver makes it impossible to set cookies for
        # domains other than the current active one, cf. https://github.com/w3c/webdriver/issues/1238
        # Therefore setting cookies in the session instance for other domains than the on set above
        # (e.g., via self._session.cookies.set) will create problems when transferring them to the
        # webdriver when handling captchas.

        return self._webdriver


    def _new_session(self):
        proxies = {}
        if self._session:
            proxies = self._session.proxies
            self._close_session()
        self._session = requests.Session()
        self.got_403 = False

        _HEADERS = {
            'accept-language': 'en-US,en',
            'accept': 'text/html,application/xhtml+xml,application/xml'
        }
        _HEADERS['User-Agent'] = UserAgent().random
        self._session.headers.update(_HEADERS)

        if self._proxy_works:
            self._session.proxies = proxies
        self._webdriver = None

    def _close_session(self):
        if self._session:
            self._session.close()
        if self._webdriver:
            self._webdriver.quit()

    def _handle_captcha2(self, url, session):
        cur_host = urlparse(self._get_webdriver().current_url).hostname
        for cookie in self._session.cookies:
            # Only set cookies matching the current domain, cf. https://github.com/w3c/webdriver/issues/1238
            if cur_host is cookie.domain.lstrip('.'):
                self._get_webdriver().add_cookie({
                    'name': cookie.name,
                    'value': cookie.value,
                    'path': cookie.path,
                    'domain':cookie.domain,
                })
        self._get_webdriver().get(url)

        log_interval = 10
        cur = 0
        timeout = 60*60*24*7 # 1 week
        while cur < timeout:
            try:
                cur = cur + log_interval # Update before exceptions can happen
                WebDriverWait(self._get_webdriver(), log_interval).until_not(lambda drv : self._webdriver_has_captcha())
                break
            except TimeoutException:
                self.logger.info(f"Solving the captcha took already {cur} seconds (of maximum {timeout} s).")
            except UnexpectedAlertPresentException as e:
                # This can apparently happen when reCAPTCHA has hiccups:
                # "Cannot contact reCAPTCHA. Check your connection and try again."
                self.logger.info(f"Unexpected alert while waiting for captcha completion: {e.args}")
                time.sleep(15)
            except DOSException as e:
                self.logger.info(f"Google thinks we are DOSing the captcha.")
                raise e
            except (WebDriverException) as e:
                self.logger.info(f"Browser seems to be disfunctional - closed by user?")
                raise e
            except Exception as e:
                # TODO: This exception handler should eventually be removed when
                # we know the "typical" (non-error) exceptions that can occur.
                self.logger.info(f"Unhandled {type(e).__name__} while waiting for captcha completion: {e.args}")
        else:
            raise TimeoutException(f"Could not solve captcha in time (within {timeout} s).")
        self.logger.info(f"Solved captcha in less than {cur} seconds.")

        for cookie in self._get_webdriver().get_cookies():
            cookie.pop("httpOnly", None)
            cookie.pop("expiry", None)
            self._session.cookies.set(**cookie)

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
                has_captcha = self._requests_has_captcha(resp.text)

                if resp.status_code == 200 and not has_captcha:
                    return resp.text
                elif has_captcha:
                    self.logger.info("Got a captcha request.")
                    self._handle_captcha2(pagerequest, self._session)
                    continue # Retry request within same session
                elif resp.status_code == 403:
                    self.logger.info(f"Got an access denied error (403).")
                    if not self._can_refresh_tor and not self._proxy_gen:
                        self.logger.info("No other connections possible.")
                        if not self.got_403:
                            self.logger.info("Retrying immediately with another session.")
                        else:
                            if not self._use_luminaty:
                                w = random.uniform(60, 2*60)
                                self.logger.info("Will retry after {} seconds (with another session).".format(w))
                                time.sleep(w)
                            else:
                                self.logger.info("Using luminaty service retrying immediately")
                        self._new_session()
                        self.got_403 = True
                        
                        continue # Retry request within same session
                    else:
                        self.logger.info("We can use another connection... let's try that.")
                else:
                    self.logger.info(f"""Response code {resp.status_code}.
                                    Retrying...""")

            except DOSException:
                if not self._can_refresh_tor and not self._proxy_gen:
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
            if self._can_refresh_tor:
                # Check if Tor is running and refresh it
                self.logger.info("Refreshing Tor ID...")
                self._refresh_tor_id(self._tor_control_port, self._tor_password)
                time.sleep(5) # wait for the refresh to happen
                timeout=self._TIMEOUT # Reset timeout to default
            elif self._proxy_gen:
                self.logger.info(f"Try #{tries} failed. Switching proxy.")
                # Try to get another proxy
                new_proxy = self._proxy_gen()
                while (not self._use_proxy(new_proxy)):
                    new_proxy = self._proxy_gen()
                timeout=self._TIMEOUT # Reset timeout to default
            else:
                self._new_session()

        raise Exception("Cannot fetch the page from Google Scholar.")

    def _check_proxy(self, proxies) -> bool:
        """Checks if a proxy is working.
        :param proxies: A dictionary {'http': url1, 'https': url1}
                        with the urls of the proxies
        :returns: whether the proxy is working or not
        :rtype: {bool}
        """
        with requests.Session() as session:
            session.proxies = proxies
            try:
                # Netflix assets CDN should have very low latency for about everybody
                resp = session.get("http://assets.nflxext.com", timeout=self._TIMEOUT)
                if resp.status_code == 200:
                    self.logger.info("Proxy works!")
                    return True
            except Exception as e:
                self.logger.info(f"Exception while testing proxy: {e}")

            return False

    def _refresh_tor_id(self, tor_control_port: int, password: str) -> bool:
        """Refreshes the id by using a new Tor node.

        :returns: Whether or not the refresh was succesful
        :rtype: {bool}
        """
        try:
            with Controller.from_port(port=tor_control_port) as controller:
                if password:
                    controller.authenticate(password=password)
                else:
                    controller.authenticate()
                controller.signal(Signal.NEWNYM)
                self._new_session()
            return True
        except Exception as e:
            err = f"Exception {e} while refreshing TOR. Retrying..."
            self.logger.info(err)
            return False

    def _set_retries(self, num_retries: int) -> None:
        if (num_retries < 0):
            raise ValueError("num_retries must not be negative")
        self._max_retries = num_retries

    def _set_proxy_generator(self, gen: Callable[..., str]) -> bool:
        self._proxy_gen = gen
        return True

    def _use_proxy(self, http: str, https: str = None) -> bool:
        """Allows user to set their own proxy for the connection session.
        Sets the proxy, and checks if it works.

        :param http: the http proxy
        :type http: str
        :param https: the https proxy (default to the same as http)
        :type https: str
        :returns: if the proxy works
        :rtype: {bool}
        """
        # check if the proxy url contains luminaty
        self._use_luminaty = (True if "lum" in http else False)
        if https is None:
            https = http

        proxies = {'http': http, 'https': https}
        self._proxy_works = self._check_proxy(proxies)
        if self._proxy_works:
            self.logger.info(f"Enabling proxies: http={http} https={https}")
            self._session.proxies = proxies
            self._new_session()
        else:
            self.logger.info(f"Proxy {http} does not seem to work.")
        return self._proxy_works

    def _setup_tor(self, tor_sock_port: int, tor_control_port: int, tor_password: str):
        """
        Setting up Tor Proxy

        :param tor_sock_port: the port where the Tor sock proxy is running
        :type tor_sock_port: int
        :param tor_control_port: the port where the Tor control server is running
        :type tor_control_port: int
        :param tor_password: the password for the Tor control server
        :type tor_password: str
        """

        proxy = f"socks5://127.0.0.1:{tor_sock_port}"
        self._use_proxy(http=proxy, https=proxy)

        self._can_refresh_tor = self._refresh_tor_id(tor_control_port, tor_password)
        if self._can_refresh_tor:
            self._tor_control_port = tor_control_port
            self._tor_password = tor_password
        else:
            self._tor_control_port = None
            self._tor_password = None

        # Setting requests timeout to be reasonably long
        # to accommodate slowness of the Tor network
        self._TIMEOUT = 10

        return {
            "proxy_works": self._proxy_works,
            "refresh_works": self._can_refresh_tor,
            "tor_control_port": tor_control_port,
            "tor_sock_port": tor_sock_port
        }

    def _launch_tor(self, tor_cmd=None, tor_sock_port=None, tor_control_port=None):
        '''
        Starts a Tor client running in a scholarly-specific port,
        together with a scholarly-specific control port.
        '''
        self.logger.info("Attempting to start owned Tor as the proxy")

        if tor_cmd is None:
            self.logger.info("No tor_cmd argument passed. This should point to the location of Tor executable.")
            return {
                "proxy_works": False,
                "refresh_works": False,
                "tor_control_port": None,
                "tor_sock_port": None
            }

        if tor_sock_port is None:
            # Picking a random port to avoid conflicts
            # with simultaneous runs of scholarly
            tor_sock_port = random.randrange(9000, 9500)

        if tor_control_port is None:
            # Picking a random port to avoid conflicts
            # with simultaneous runs of scholarly
            tor_control_port = random.randrange(9500, 9999)

        # TODO: Check that the launched Tor process stops after scholar is done
        self._tor_process = stem.process.launch_tor_with_config(
            tor_cmd=tor_cmd,
            config={
                'ControlPort': str(tor_control_port),
                'SocksPort': str(tor_sock_port),
                'DataDirectory': tempfile.mkdtemp()
                # TODO Perhaps we want to also set a password here
            },
            # take_ownership=True # Taking this out for now, as it seems to cause trouble
        )
        return self._setup_tor(tor_sock_port, tor_control_port, tor_password=None)

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
            lambda i : len(self._get_webdriver().find_elements(By.ID, i)) > 0,
            lambda c : len(self._get_webdriver().find_elements(By.CLASS_NAME, c)) > 0,
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

    def search_authors(self, url: str):
        """Generator that returns Author objects from the author search page"""
        soup = self._get_soup(url)

        while True:
            rows = soup.find_all('div', 'gsc_1usr')
            self.logger.info("Found %d authors", len(rows))
            for row in rows:
                yield Author(self, row)
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
                           filled: bool = False) -> Publication:
        """Search by scholar query and return a single Publication object

        :param url: the url to be searched at
        :type url: str
        :param filled: Whether publication should be filled, defaults to False
        :type filled: bool, optional
        :returns: a publication object
        :rtype: {Publication}
        """
        soup = self._get_soup(url)
        res = Publication(self, soup.find_all('div', 'gs_or')[0], 'scholar')
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
        if filled:
            res = Author(self, id).fill()
        else:
            res = Author(self, id).fill(sections=['basics'])
        return res
