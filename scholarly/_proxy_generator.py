from typing import Callable
from fp.fp import FreeProxy
import random
import logging
import time
import requests
import tempfile
import urllib3

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, UnexpectedAlertPresentException
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from urllib.parse import urlparse
from fake_useragent import UserAgent
from contextlib import contextmanager
from deprecated import deprecated
try:
    import stem.process
    from stem import Signal
    from stem.control import Controller
except ImportError:
    stem = None

from .data_types import ProxyMode


class DOSException(Exception):
    """DOS attack was detected."""


class MaxTriesExceededException(Exception):
    """Maximum number of tries by scholarly reached"""


class ProxyGenerator(object):
    def __init__(self):
        # setting up logger
        self.logger = logging.getLogger('scholarly')

        self._proxy_gen = None
        # If we use a proxy or Tor, we set this to True
        self._proxy_works = False
        self.proxy_mode = None
        # If we have a Tor server that we can refresh, we set this to True
        self._tor_process = None
        self._can_refresh_tor = False
        self._tor_control_port = None
        self._tor_password = None
        self._session = None
        self._webdriver = None
        self._TIMEOUT = 5
        self._new_session()

    def __del__(self):
        if self._tor_process:
            self._tor_process.kill()
            self._tor_process.wait()
        self._close_session()

    def get_session(self):
        return self._session

    def Luminati(self, usr, passwd, proxy_port):
        """ Setups a luminati proxy without refreshing capabilities.

        :param usr: scholarly username, optional by default None
        :type usr: string
        :param passwd: scholarly password, optional by default None
        :type passwd: string
        :param proxy_port: port for the proxy,optional by default None
        :type proxy_port: integer
        :returns: whether or not the proxy was set up successfully
        :rtype: {bool}

        :Example::
            >>> pg = ProxyGenerator()
            >>> success = pg.Luminati(usr = foo, passwd = bar, port = 1200)
        """
        if (usr is not None and passwd is not None and proxy_port is not None):
            username = usr
            password = passwd
            port = proxy_port
        else:
            self.logger.warning("Not enough parameters were provided for the Luminati proxy. Reverting to a local connection.")
            return
        session_id = random.random()
        proxy = f"http://{username}-session-{session_id}:{password}@zproxy.lum-superproxy.io:{port}"
        proxy_works = self._use_proxy(http=proxy, https=proxy)
        if proxy_works:
            self.logger.info("Luminati proxy setup successfully")
            self.proxy_mode = ProxyMode.LUMINATI
        else:
            self.logger.warning("Luminati does not seem to work. Reason unknown.")
        return proxy_works

    def SingleProxy(self, http=None, https=None):
        """
        Use proxy of your choice

        :param http: http proxy address
        :type http: string
        :param https: https proxy adress
        :type https: string
        :returns: whether or not the proxy was set up successfully
        :rtype: {bool}

        :Example::

            >>> pg = ProxyGenerator()
            >>> success = pg.SingleProxy(http = <http proxy adress>, https = <https proxy adress>)
        """
        self.logger.info("Enabling proxies: http=%s https=%s", http, https)
        proxy_works = self._use_proxy(http=http, https=https)
        if proxy_works:
            self.proxy_mode = ProxyMode.SINGLEPROXY
            self.logger.info("Proxy setup successfully")
        else:
            self.logger.warning("Unable to setup the proxy: http=%s https=%s. Reason unknown." , http, https)
        return proxy_works

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
                resp = session.get("http://httpbin.org/ip", timeout=self._TIMEOUT)
                if resp.status_code == 200:
                    self.logger.info("Proxy works! IP address: %s",
                                     resp.json()["origin"])
                    return True
                elif resp.status_code == 401:
                    self.logger.warning("Incorrect credentials for proxy!")
                    return False
            except (TimeoutException, TimeoutError):
                time.sleep(self._TIMEOUT)
            except Exception as e:
                # Failure is common and expected with free proxy.
                # Do not log at warning level and annoy users.
                level = logging.DEBUG if self.proxy_mode is ProxyMode.FREE_PROXIES else logging.WARNING
                self.logger.log(level, "Exception while testing proxy: %s", e)
                if self.proxy_mode in (ProxyMode.LUMINATI, ProxyMode.SCRAPERAPI):
                    self.logger.warning("Double check your credentials and try increasing the timeout")

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
        Sets the proxy if it works.

        :param http: the http proxy
        :type http: str
        :param https: the https proxy (default to the same as http)
        :type https: str
        :returns: whether or not the proxy was set up successfully
        :rtype: {bool}
        """
        if https is None:
            https = http

        proxies = {'http': http, 'https': https}
        if self.proxy_mode == ProxyMode.SCRAPERAPI:
            r = requests.get("http://api.scraperapi.com/account", params={'api_key': self._API_KEY}).json()
            if "error" in r:
                self.logger.warning(r["error"])
                self._proxy_works = False
            else:
                self._proxy_works = r["requestCount"] < int(r["requestLimit"])
                self.logger.info("Successful ScraperAPI requests %d / %d",
                                 r["requestCount"], r["requestLimit"])
        else:
            self._proxy_works = self._check_proxy(proxies)

        if self._proxy_works:
            self._session.proxies = proxies
            self._new_session()

        return self._proxy_works

    @deprecated(version='1.5', reason="Tor methods are deprecated and are not actively tested.")
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

        Note: This method is deprecated since v1.5
        """
        if stem is None:
            raise RuntimeError("Tor methods are not supported with basic version of the package. "
                               "Please install scholarly[tor] to use this method.")

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

        self.proxy_mode = ProxyMode.TOR_EXTERNAL
        # Setting requests timeout to be reasonably long
        # to accommodate slowness of the Tor network
        return {
            "proxy_works": self._proxy_works,
            "refresh_works": self._can_refresh_tor,
            "tor_control_port": tor_control_port,
            "tor_sock_port": tor_sock_port
        }

    @deprecated(version='1.5', reason="Tor methods are deprecated and are not actively tested")
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

        Note: This method is deprecated since v1.5
        '''
        if stem is None:
            raise RuntimeError("Tor methods are not supported with basic version of the package. "
                               "Please install scholarly[tor] to use this method.")

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
        self.proxy_mode = ProxyMode.TOR_INTERNAL
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
            try:
                _ = self._webdriver.current_url
                return self._webdriver
            except Exception as e:
                self.logger.debug(e)

        try:
            return self._get_firefox_webdriver()
        except Exception as err:
            self.logger.debug("Cannot open Firefox/Geckodriver: %s", err)
            try:
                return self._get_chrome_webdriver()
            except Exception as err:
                self.logger.debug("Cannot open Chrome: %s", err)
                self.logger.info("Neither Chrome nor Firefox/Geckodriver found in PATH")

    def _get_chrome_webdriver(self):
        if self._proxy_works:
            webdriver.DesiredCapabilities.CHROME['proxy'] = {
                "httpProxy": self._session.proxies['http'],
                "sslProxy": self._session.proxies['https'],
                "proxyType": "MANUAL"
            }

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self._webdriver = webdriver.Chrome('chromedriver', options=options)
        self._webdriver.get("https://scholar.google.com")  # Need to pre-load to set cookies later

        return self._webdriver

    def _get_firefox_webdriver(self):
        if self._proxy_works:
            # Redirect webdriver through proxy
            webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
                "httpProxy": self._session.proxies['http'],
                "sslProxy": self._session.proxies['https'],
                "proxyType": "MANUAL",
            }

        options = FirefoxOptions()
        options.add_argument('--headless')
        self._webdriver = webdriver.Firefox(options=options)
        self._webdriver.get("https://scholar.google.com")  # Need to pre-load to set cookies later

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
                self.logger.info("Google thinks we are DOSing the captcha.")
                raise e
            except (WebDriverException) as e:
                self.logger.info("Browser seems to be disfunctional - closed by user?")
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
            cookie.pop("sameSite", None)
            self._session.cookies.set(**cookie)

        return self._session

    def _new_session(self):
        proxies = {}
        if self._session:
            proxies = self._session.proxies
            self._close_session()
        self._session = requests.Session()
        self.got_403 = False

        # Suppress the misleading traceback from UserAgent()
        with self._suppress_logger('fake_useragent'):
            _HEADERS = {
                'accept-language': 'en-US,en',
                'accept': 'text/html,application/xhtml+xml,application/xml',
                'User-Agent': UserAgent().random,
            }
        self._session.headers.update(_HEADERS)

        if self._proxy_works:
            self._session.proxies = proxies
            if self.proxy_mode is ProxyMode.SCRAPERAPI:
                # SSL Certificate verification must be disabled for
                # ScraperAPI requests to work.
                # https://www.scraperapi.com/documentation/
                self._session.verify = False
        self._webdriver = None

        return self._session

    def _close_session(self):
        if self._session:
            self._session.close()
        if self._webdriver:
            try:
                self._webdriver.quit()
            except Exception as e:
                self.logger.warning("Could not close webdriver cleanly: %s", e)

    def _fp_coroutine(self, timeout=1, wait_time=120):
        """A coroutine to continuosly yield free proxies

        It takes back the proxies that stopped working and marks it as dirty.
        """
        freeproxy = FreeProxy(rand=False, timeout=timeout)
        if not hasattr(self, '_dirty_freeproxies'):
            self._dirty_freeproxies = set()
        try:
            all_proxies = freeproxy.get_proxy_list(repeat=False)  # free-proxy >= 1.1.0
        except TypeError:
            all_proxies = freeproxy.get_proxy_list()  # free-proxy < 1.1.0
        all_proxies.reverse()  # Try the older proxies first

        t1 = time.time()
        while (time.time()-t1 < wait_time):
            proxy = all_proxies.pop()
            if not all_proxies:
                all_proxies = freeproxy.get_proxy_list()
            if proxy in self._dirty_freeproxies:
                continue
            proxies = {'http': proxy, 'https': proxy}
            proxy_works = self._check_proxy(proxies)
            if proxy_works:
                dirty_proxy = (yield proxy)
                t1 = time.time()
            else:
                dirty_proxy = proxy
            self._dirty_freeproxies.add(dirty_proxy)

    def FreeProxies(self, timeout=1, wait_time=120):
        """
        Sets up continuously rotating proxies from the free-proxy library

        :param timeout: Timeout for a single proxy in seconds, optional
        :type timeout: float
        :param wait_time: Maximum time (in seconds) to wait until newer set of proxies become available at https://sslproxies.org/
        :type wait_time: float
        :returns: whether or not the proxy was set up successfully
        :rtype: {bool}

        :Example::
            >>> pg = ProxyGenerator()
            >>> success = pg.FreeProxies()
        """
        self.proxy_mode = ProxyMode.FREE_PROXIES
        # FreeProxies is the only mode that is assigned regardless of setup successfully or not.

        self._fp_gen = self._fp_coroutine(timeout=timeout, wait_time=wait_time)
        self._proxy_gen = self._fp_gen.send
        proxy = self._proxy_gen(None)  # prime the generator
        self.logger.debug("Trying with proxy %s", proxy)
        proxy_works = self._use_proxy(proxy)
        n_retries = 200
        n_tries = 0

        while (not proxy_works) and (n_tries < n_retries):
            self.logger.debug("Trying with proxy %s", proxy)
            proxy_works = self._use_proxy(proxy)
            n_tries += 1
            if not proxy_works:
                proxy = self._proxy_gen(proxy)

        if n_tries == n_retries:
            n_dirty = len(self._dirty_freeproxies)
            self._fp_gen.close()
            msg = ("None of the free proxies are working at the moment. "
                  f"Marked {n_dirty} proxies dirty. Try again after a few minutes."
                  )
            raise MaxTriesExceededException(msg)
        else:
            return True

    def ScraperAPI(self, API_KEY, country_code=None, premium=False, render=False):
        """
        Sets up a proxy using ScraperAPI

        The optional parameters are only for Business and Enterprise plans with
        ScraperAPI. For more details, https://www.scraperapi.com/documentation/

        :Example::
            >>> pg = ProxyGenerator()
            >>> success = pg.ScraperAPI(API_KEY)

        :param API_KEY: ScraperAPI API Key value.
        :type API_KEY: string
        :type country_code: string, optional by default None
        :type premium: bool, optional by default False
        :type render: bool, optional by default False
        :returns: whether or not the proxy was set up successfully
        :rtype: {bool}
        """
        if API_KEY is None:
            raise ValueError("ScraperAPI API Key is required.")

        # Get basic account information. This will NOT be counted towards successful API requests.
        r = requests.get("http://api.scraperapi.com/account", params={'api_key': API_KEY}).json()
        if "error" in r:
            self.logger.warning(r["error"])
            return False

        self._API_KEY = API_KEY
        self.proxy_mode = ProxyMode.SCRAPERAPI

        r["requestLimit"] = int(r["requestLimit"])
        self.logger.info("Successful ScraperAPI requests %d / %d",
                         r["requestCount"], r["requestLimit"])

        # ScraperAPI documentation recommends setting the timeout to 60 seconds
        # so it has had a chance to try out all the retries.
        # https://www.scraperapi.com/documentation/
        self._TIMEOUT = 60

        prefix = "http://scraperapi"
        if country_code is not None:
            prefix += ".country_code=" + country_code
        if premium:
            prefix += ".premium=true"
        if render:
            prefix += ".render=true"

        # Suppress the unavoidable insecure request warnings with ScraperAPI
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        for _ in range(3):
            proxy_works = self._use_proxy(http=f'{prefix}:{API_KEY}@proxy-server.scraperapi.com:8001')
            if proxy_works:
                self.logger.info("ScraperAPI proxy setup successfully")
                self._session.verify = False
                return proxy_works

        if (r["requestCount"] >= r["requestLimit"]):
            self.logger.warning("ScraperAPI account limit reached.")
        else:
            self.logger.warning("ScraperAPI does not seem to work. Reason unknown.")

        return False

    def has_proxy(self) -> bool:
        return self._proxy_gen or self._can_refresh_tor

    def _set_proxy_generator(self, gen: Callable[..., str]) -> bool:
        self._proxy_gen = gen
        return True

    def get_next_proxy(self, num_tries = None, old_timeout = 3, old_proxy=None):
        new_timeout = old_timeout
        if self._can_refresh_tor:
            # Check if Tor is running and refresh it
            self.logger.info("Refreshing Tor ID...")
            self._refresh_tor_id(self._tor_control_port, self._tor_password)
            time.sleep(5) # wait for the refresh to happen
            new_timeout = self._TIMEOUT # Reset timeout to default
        elif self._proxy_gen:
            if (num_tries):
                self.logger.info("Try #%d failed. Switching proxy.", num_tries)
            # Try to get another proxy
            new_proxy = self._proxy_gen(old_proxy)
            while (not self._use_proxy(new_proxy)):
                new_proxy = self._proxy_gen(new_proxy)
            new_timeout = self._TIMEOUT # Reset timeout to default
            self._new_session()
        else:
            self._new_session()

        return self._session, new_timeout

    # A context manager to suppress the misleading traceback from UserAgent()
    # Based on https://thesmithfam.org/blog/2012/10/25/temporarily-suppress-console-output-in-python/
    @staticmethod
    @contextmanager
    def _suppress_logger(loggerName: str, level=logging.CRITICAL):
        """Temporarily suppress logging output from a specific logger.
        """
        logger = logging.getLogger(loggerName)
        original_level = logger.getEffectiveLevel()
        logger.setLevel(level)
        try:
            yield
        finally:
            logger.setLevel(original_level)
