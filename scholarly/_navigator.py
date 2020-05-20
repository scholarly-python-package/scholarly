from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bs4 import BeautifulSoup

import codecs
import hashlib
import logging
import random
import requests
import tempfile
import stem.process
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from .publication import _SearchScholarIterator
from .author import Author
from .publication import Publication
import sys

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_HEADERS = {
    'accept-language': 'en-US,en',
    'accept': 'text/html,application/xhtml+xml,application/xml'
}
_HOST = 'https://scholar.google.com{0}'

_PUBSEARCH = '"/scholar?hl=en&q={0}"'
_SCHOLARCITERE = r'gs_ocit\(event,\'([\w-]*)\''

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
        self._tor = False
        self._proxy = False
        self._setup_tor()
        self._TIMEOUT = 10
        self._SCHOLAR_TOR_SOCK_PORT = 9600
        self._SCHOLAR_TOR_CONTROL_PORT = 9601        

    def _setup_tor(self):
        """Initialized ToR Proxy"""

        # Tor uses the 9050 port as the default socks port
        # on windows 9150 for socks and 9151 for control
        if sys.platform.startswith("linux"):
            self._TOR_SOCK = "socks5://127.0.0.1:9050"
            self._TOR_CONTROL = 9051
        elif sys.platform.startswith("win"):
            self._TOR_SOCK = "socks5://127.0.0.1:9150"
            self._TOR_CONTROL = 9151

        self.proxies = {'http': self._TOR_SOCK,
                        'https': self._TOR_SOCK}

        self._tor = self._proxy_works()

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
        while True:
            # Use ToR by default. If proxy was setup, use it.
            # Otherwise the local IP is used
            session = requests.Session()
            if self._tor or self._proxy:
                session.proxies = self.proxies

            try:
                _HEADERS['User-Agent'] = UserAgent().random

                resp = session.get(pagerequest,
                                   headers=_HEADERS,
                                   cookies=_COOKIES,
                                   timeout=self._TIMEOUT)

                if resp.status_code == 200:
                    if self._has_captcha(resp.text):
                        raise Exception("Got a CAPTCHA. Retrying.")
                    else:
                        session.close()
                        return resp.text
                else:
                    self.logger.info(f"""Response code {resp.status_code}.
                                    Retrying...""")
                    raise Exception(f"Status code {resp.status_code}")

            except Exception as e:
                err = f"Exception {e} while fetching page. Retrying."
                self.logger.info(err)
                # Check if Tor is running and refresh it
                self.logger.info("Refreshing Tor ID...")
                session.close()
                if self._tor:
                    self._refresh_tor_id()

    def _proxy_works(self) -> bool:
        """Checks if a proxy is working

        :returns: whether the proxy is working or not
        :rtype: {bool}
        """
        with requests.Session() as session:
            session.proxies = self.proxies
            try:
                # Changed to twitter so we dont ping google twice every time
                resp = session.get("http://www.twitter.com")
                self.logger.info("Proxy Works!")
                return resp.status_code == 200
            except Exception as e:
                self.logger.info(f"Proxy not working: Exception {e}")
                return False

    def _refresh_tor_id(self) -> bool:
        """Refreshes the id by using a new ToR node

        :returns: Whether or not the refresh was succesfull
        :rtype: {bool}
        """
        try:
            with Controller.from_port(port=self._TOR_CONTROL) as controller:
                controller.authenticate(password="scholarly_password")
                controller.signal(Signal.NEWNYM)
            return True
        except Exception as e:
            err = f"Exception {e} while refreshing TOR. Retrying..."
            self.logger.info(err)
            return False

    def _use_proxy(self, http: str, https: str):
        """Allows user to use their own proxy

        By using this function the user will be using their own proxy and not
        ToR. The proxy must be running. ToR will be disabled.
        :param http: the http proxy
        :type http: str
        :param https: the https proxy
        :type https: str
        """
        self.logger.info("Enabling proxies: http=%r https=%r", http, https)
        self.proxies = {'http': http, 'https': https}
        self._tor = False
        self._proxy = self._proxy_works()

    def _use_tor(self, tor_cmd=None, 
                 tor_sock_port=self._SCHOLAR_TOR_CONTROL_PORT, 
                 tor_control_port=self._SCHOLAR_TOR_CONTROL_PORT):
        '''
        Starts a Tor client running in a schoar-specific port, together with a 
        scholar-specific control port.
        '''
        self.logger.info("Starting tor as the proxy")
        
        if tor_cmd is None:
            if sys.platform.startswith("linux"):
                tor_cmd = '/usr/sbin/tor'
            elif sys.platform.startswith("win"):
                tor_cmd = 'C:\\Tor\tor.exe'

        self._tor_sock_port = tor_sock_port
        self._tor_control_port = tor_control_port

        # TODO: Check that the launched Tor process stops after scholar is done
        tor_process = stem.process.launch_tor_with_config(
            tor_cmd=tor_cmd,
            config={
                'ControlPort': str(self._tor_control_port),
                'SocksPort': str(self._tor_sock_port),
                'DataDirectory': tempfile.mkdtemp()
            },
            # take_ownership = True
        )        
        self._tor_sock_proxy = f"socks5://127.0.0.1:{self._tor_sock_port}"
        if self._tor_works():
            self._use_proxy(http=self._tor_sock_proxy, https=self._tor_sock_proxy)
            self._tor = True
            return True
        else:
            return False


    def _has_captcha(self, text: str) -> bool:
        """Tests whether an error or captcha was shown.

        :param text: the webpage text
        :type text: str
        :returns: whether or not an error occurred
        :rtype: {bool}
        """
        flags = ["Please show you're not a robot",
                 "network may be sending automated queries",
                 "have detected unusual traffic from your computer",
                 "scholarly_captcha",
                 "/sorry/image",
                 "enable JavaScript"]
        return any([i in text for i in flags])

    def _get_soup(self, url: str) -> BeautifulSoup:
        """Return the BeautifulSoup for a page on scholar.google.com"""
        html = self._get_page(_HOST.format(url))
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
