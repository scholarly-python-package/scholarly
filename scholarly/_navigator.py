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
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from .publication import _SearchScholarIterator
from .author import Author
import sys

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_HEADERS = {
    'accept-language': 'en-US,en',
    'accept': 'text/html,application/xhtml+xml,application/xml'
}
_HOST = 'https://scholar.google.com{0}'

_SCHOLARCITERE = r'gs_ocit\(event,\'([\w-]*)\''

_TIMEOUT = 2

_PROXIES = {
    "http": None,
    "https": None,
}

_HTTP_PROXY = None
_HTTPS_PROXY = None

_TOR_SOCK = None
_TOR_CONTROL = None


if sys.platform.startswith("linux"):
    _TOR_SOCK = "socks5://127.0.0.1:9050"
    _TOR_CONTROL = 9051
elif sys.platform.startswith("win"):
    _TOR_SOCK = "socks5://127.0.0.1:9150"
    _TOR_CONTROL = 9151


class Navigator(object):
    """I did not call it browser because there are other packages with
    that exact name. -Victor
    """
    def __init__(self):
        # TODO: Implement Singleton pattern since we don't need multiple navs.
        super(Navigator, self).__init__()
        logging.basicConfig(filename='scholar.log', level=logging.INFO)
        self.logger = logging.getLogger('scholarly')
        self._tor = self._tor_works()

    def _get_page(self, pagerequest: str):
        """Return the data for a page on scholar.google.com"""
        self.logger.info("Getting %s", pagerequest)
        resp = None
        while True:
            # If Tor is running we use the proxy
            # Did not use with for shorter indented lines -V
            session = requests.Session()
            if self._tor:

                # Tor uses the 9050 port as the default socks port
                # on windows 9150 for socks and 9151 for control
                session.proxies = {'http':  _TOR_SOCK,
                                   'https': _TOR_SOCK}
            else:
                session.proxies = _PROXIES

            try:
                _HEADERS['User-Agent'] = UserAgent().random

                resp = session.get(pagerequest,
                                   headers=_HEADERS,
                                   cookies=_COOKIES,
                                   timeout=_TIMEOUT)

                if resp.status_code == 200:
                    if self._has_captcha(resp.text):
                        raise Exception("Got a CAPTCHA. Retrying.")
                    else:
                        session.close()
                        return resp.text
                else:
                    self.logger.info(f"""Got a response code {resp.status_code}.
                                    Retrying...""")
                    raise Exception(f"Status code {resp.status_code}")

            except Exception as e:
                err = f"Exception {e} while fetching page. Retrying."
                self.logger.info(err)
                # Check if Tor is running and refresh it
                self.logger.info("Refreshing Tor ID...")
                if self._tor:
                    self._refresh_tor_id()
                session.close()

    def _tor_works(self) -> bool:
        """ Checks if Tor is working"""
        with requests.Session() as session:
            session.proxies = {
                'http': _TOR_SOCK,
                'https': _TOR_SOCK
            }
            try:
                # Changed to twitter so we dont ping google twice every time
                resp = session.get("http://www.twitter.com")
                self.logger.info("TOR Works!")
                return resp.status_code == 200
            except Exception as e:
                self.logger.info(f"Tor not working: Exception {e}")
                return False

    def _refresh_tor_id(self) -> bool:
        try:
            with Controller.from_port(port=_TOR_CONTROL) as controller:
                controller.authenticate(password="scholarly_password")
                controller.signal(Signal.NEWNYM)
            return True
        except Exception as e:
            err = f"Exception {e} while refreshing TOR. Retrying..."
            self.logger.info(err)
            return False

    def use_proxy(self, http: str, https: str):
        """ Routes scholarly through a proxy (e.g. tor).
            Requires pysocks
            Proxy must be running."""
        self.logger.info("Enabling proxies: http=%r https=%r", http, https)
        _PROXIES = {
            "http": http,
            "https": https,
        }

    def use_tor(self):
        self.logger.info("Setting tor as the proxy")
        self._use_proxy(http=_TOR_SOCK,
                        https=_TOR_SOCK)

    def _has_captcha(self, text: str) -> bool:
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
        except:
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
            next_button = soup.find(
                class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
            if next_button and 'disabled' not in next_button.attrs:
                self.logger.info("Loading next page of authors")
                url = next_button['onclick'][17:-1]
                url = codecs.getdecoder("unicode_escape")(url)[0]
                soup = self._get_soup(url)
            else:
                self.logger.info("No more author pages")
                break

    def search_publications(self, url: str) -> _SearchScholarIterator:
        return _SearchScholarIterator(self, url)
