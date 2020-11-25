from typing import Callable
from fp.fp import FreeProxy
import random
import logging
import time
import requests
import stem.process
import tempfile
import os 

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
from dotenv import load_dotenv, find_dotenv

class DOSException(Exception):
    """DOS attack was detected."""


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]

class ProxyGenerator(object):
    def __init__(self):

        # setting up logger 
        logging.basicConfig(filename='scholar.log', level=logging.INFO)
        self.logger = logging.getLogger('scholarly')

        self._proxy_gen = None
        # If we use a proxy or Tor, we set this to True
        self._proxy_works = False
        self._use_luminati = False
        # If we h:ve a Tor server that we can refresh, we set this to True
        self._tor_process = None
        self._can_refresh_tor = False
        self._tor_control_port = None
        self._tor_password = None
        self._session = None
        self._TIMEOUT = 5
        self._new_session()

    def __del__(self):
        if self._tor_process:
            self._tor_process.kill()
            self._tor_process.wait()
        self._close_session()

    def get_session(self):
        return self._session

    def Luminati(self, usr , passwd, proxy_port):
        """ Setups a luminati proxy without refreshing capabilities.

        :param usr: scholarly username, optional by default None
        :type usr: string
        :param passwd: scholarly password, optional by default None
        :type passwd: string
        :param proxy_port: port for the proxy,optional by default None
        :type proxy_port: integer
        
        :Example::
            pg = ProxyGenerator()
            pg.Luminati(usr = foo, passwd = bar, port = 1200)
        """
        if (usr != None and passwd != None and proxy_port != None):
            username = usr
            password = passwd
            port = proxy_port 
        else:
            self.logger.info("Not enough parameters were provided for the Luminati proxy. Reverting to a local connection.")
            return
        session_id = random.random()
        proxy = f"http://{username}-session-{session_id}:{password}@zproxy.lum-superproxy.io:{port}"
        self._use_proxy(http=proxy, https=proxy)

    def SingleProxy(self, http = None, https = None):
        """
        Use proxy of your choice
        :param http: http proxy address
        type http: string
        :param https: https proxy adress 
        :type https: string

        :Example::
            pg = ProxyGenerator()
            pg.SingleProxy(http = <http proxy adress>, https = <https proxy adress>)
        """
        self._use_proxy(http=http,https=https)

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
            return (True, self._session)
        except Exception as e:
            err = f"Exception {e} while refreshing TOR. Retrying..."
            self.logger.info(err)
            return (False, None)

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
        # check if the proxy url contains luminati
        self._use_luminati = (True if "lum" in http else False)
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

    def Tor_External(self, tor_sock_port: int, tor_control_port: int, tor_password: str):
        """
        Setting up Tor Proxy. A tor service should be already running on the system. Otherwise you might want to use Tor_Internal

        :param tor_sock_port: the port where the Tor sock proxy is running
        :type tor_sock_port: int
        :param tor_control_port: the port where the Tor control server is running
        :type tor_control_port: int
        :param tor_password: the password for the Tor control server
        :type tor_password: str
    
        :Example::
            pg = ProxyGenerator()
            pg.Tor_External(tor_sock_port = 9050, tor_control_port = 9051, tor_password = "scholarly_password")
        """
        self._TIMEOUT = 10

        proxy = f"socks5://127.0.0.1:{tor_sock_port}"
        self._use_proxy(http=proxy, https=proxy)

        self._can_refresh_tor, _ = self._refresh_tor_id(tor_control_port, tor_password)
        if self._can_refresh_tor:
            self._tor_control_port = tor_control_port
            self._tor_password = tor_password
        else:
            self._tor_control_port = None
            self._tor_password = None

        # Setting requests timeout to be reasonably long
        # to accommodate slowness of the Tor network
        return {
            "proxy_works": self._proxy_works,
            "refresh_works": self._can_refresh_tor,
            "tor_control_port": tor_control_port,
            "tor_sock_port": tor_sock_port
        }

    def Tor_Internal(self, tor_cmd=None, tor_sock_port=None, tor_control_port=None):
        '''
        Starts a Tor client running in a scholarly-specific port, together with a scholarly-specific control port.
        If no arguments are passed for the tor_sock_port and the tor_control_port they are automatically generated in the following ranges
        - tor_sock_port: (9000, 9500)
        - tor_control_port: (9500, 9999)

        :param tor_cmd: tor executable location (absolute path if its not exported in PATH)
        :type tor_cmd: string
        :param tor_sock_port: tor socket port 
        :type tor_sock_port: int
        :param tor_control_port: tor control port
        :type tor_control_port: int

        :Example::
            pg = ProxyGenerator()
            pg.Tor_Internal(tor_cmd = 'tor')
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
        return self.Tor_External(tor_sock_port, tor_control_port, tor_password=None)

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

    def _webdriver_has_captcha(self) -> bool:
        """Tests whether the current webdriver page contains a captcha.

        :returns: whether or not the site contains a captcha
        :rtype: {bool}
        """
        return self._has_captcha(
            lambda i : len(self._get_webdriver().find_elements(By.ID, i)) > 0,
            lambda c : len(self._get_webdriver().find_elements(By.CLASS_NAME, c)) > 0,
        )

    def _get_webdriver(self):
        if self._webdriver:
            return self._webdriver

        if self._proxy_works:
            # Redirect webdriver through proxy
            webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
                "httpProxy": self._session.proxies['http'],
                "ftpProxy": self._session.proxies['http'],
                "sslProxy": self._session.proxies['https'],
                "proxyType":"MANUAL",
            }
        
        self._webdriver = webdriver.Firefox()
        self._webdriver.get("https://scholar.google.com") # Need to pre-load to set cookies later

        # It might make sense to (pre)set cookies as well, e.g., to set a GSP ID.
        # However, a limitation of webdriver makes it impossible to set cookies for
        # domains other than the current active one, cf. https://github.com/w3c/webdriver/issues/1238
        # Therefore setting cookies in the session instance for other domains than the on set above
        # (e.g., via self._session.cookies.set) will create problems when transferring them to the
        # webdriver when handling captchas.

        return self._webdriver

    def _handle_captcha2(self, url):
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

        return self._session

    def _new_session(self):
        proxies = {}
        if self._session:
            proxies = self._session.proxies
            self._close_session()
        self._session = requests.Session()
        self.got_403 = False

        _HEADERS = {
            'accept-language': 'en-US,en',
            'accept': 'text/html,application/xhtml+xml,application/xml',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }
        self._session.headers.update(_HEADERS)

        if self._proxy_works:
            self._session.proxies = proxies
        self._webdriver = None

        return self._session

    def _close_session(self):
        if self._session:
            self._session.close()
        if self._webdriver:
            self._webdriver.quit()
    
    def FreeProxies(self):
        """
        Sets up a proxy from the free-proxy library

        :Example::
            pg = ProxyGenerator()
            pg.FreeProxies()
        """
        while True:
            proxy = FreeProxy(rand=True, timeout=1).get()
            proxy_works = self._use_proxy(http=proxy, https=proxy)
            if proxy_works:
                break

    def has_proxy(self)-> bool:
        return self._proxy_gen or self._can_refresh_tor

    def _set_proxy_generator(self, gen: Callable[..., str]) -> bool:
        self._proxy_gen = gen
        return True

    def get_next_proxy(self, num_tries = None, old_timeout = 3):
        new_timeout = old_timeout
        if self._can_refresh_tor:
            # Check if Tor is running and refresh it
            self.logger.info("Refreshing Tor ID...")
            self._refresh_tor_id(self._tor_control_port, self._tor_password)
            time.sleep(5) # wait for the refresh to happen
            new_timeout = self._TIMEOUT # Reset timeout to default
        elif self._proxy_gen:
            if (num_tries):
                self.logger.info(f"Try #{num_tries} failed. Switching proxy.") # TODO: add tries
            # Try to get another proxy
            new_proxy = self._proxy_gen()
            while (not self._use_proxy(new_proxy)):
                new_proxy = self._proxy_gen()
            new_timeout = self._TIMEOUT # Reset timeout to default
        else:
            self._new_session()

        return self._session, new_timeout

