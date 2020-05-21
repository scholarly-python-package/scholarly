"""scholarly.py"""
import requests
from ._navigator import Navigator

_AUTHSEARCH = '/citations?hl=en&view_op=search_authors&mauthors={0}'
_KEYWORDSEARCH = '/citations?hl=en&view_op=search_authors&mauthors=label:{0}'
_PUBSEARCH = '/scholar?hl=en&q={0}'


class _Scholarly(object):
    """docstring for scholarly"""
    def __init__(self):
        self.nav = Navigator()

    def use_proxy(self, http: str, https: str):
        """
        Defines a proxy to use for the network connection.
        If you use a Tor proxy without the appropriate setup for refreshing
        the id, then you can use this function to set the Tor SOCK proxy as the
        proxy for scholarly.
        """
        self.nav._use_proxy(http, https)

    def use_tor(self, tor_sock_port: int, tor_control_port: int, tor_password: str):
        """
        Use this function to use Tor, where it is possible to access a Control Port
        for refreshing the ID. If you do not have access to the control port,
        then simply set the proxy using the `use_proxy` method.

        Args:
            :param tor_sock_port: defines the port where the sock proxy will run.
            :param tor_control_port: defines the port where the control port will run.
            :param tor_password: the password for authenticating against the control port
        Returns:
            A dictionary whether the proxy works, and whether it is possible to refresh the id
        Example:
            scholarly.use_tor(9050, 9051, "scholarly_password")
        """
        self.nav._setup_tor(tor_sock_port, tor_control_port, tor_password)

    def launch_tor(self, tor_cmd: str, tor_sock_port=None, tor_control_port=None):
        """
        Use this method to launch a temporary Tor proxy that will be used only
        by scholarly. It is necessary to pass the location of the Tor executable
        in the `tor_cmd` parameter

        Args:
            :param tor_cmd: points to the Tor executable in your system
            :param tor_sock_port: (optional) defines the port where the sock proxy will run.
            :param tor_control_port: (optional) defines the port where the control port will run.
        Returns:
            A dictionary showing the ports where the Tor server is running,
            whether the proxy works, and whether it is possible to refresh the id
        Example:
            scholarly.launch_tor('/usr/bin/tor')
        """
        self.nav._launch_tor(tor_cmd, tor_sock_port, tor_control_port)

    def search_pubs(self, query, patents=True, citations=True, year_low=None, year_high=None):
        """
        Searches by query and returns a generator of Publication objects

        search_pubs(query, patents=True, year_low=None, year_high=None)
        Args:
            query: string with search terms
            patents: bool, whether to include patents in search results (default True)
            citations: bool, whether to include citations in search results (default True)
            year_low: int, if given, earliest year from which to include results (default None)
            year_high: int, if given, latest year from which to include results (default None)
        Returns:
            generator object with search results
        Example:
            s = scholarly.search_pubs_query('cancer', year_low=2015)
        """
        url = _PUBSEARCH.format(requests.utils.quote(query))
        yr_lo = '&as_ylo={0}'.format(year_low) if year_low is not None else ''
        yr_hi = '&as_yhi={0}'.format(year_high) if year_high is not None else ''
        citations = '&as_vis={0}'.format(1 - int(citations))
        patents = '&as_sdt={0},33'.format(1 - int(patents))
        url = url + yr_lo + yr_hi + citations + patents
        return self.nav.search_publications(url)

    def search_single_pub(self, pub_title: str, filled: bool = False):
        """Search by scholar query and return a single Publication object"""
        url = _PUBSEARCH.format(requests.utils.quote(pub_title))
        return self.nav.search_publication(url, filled)

    def search_author(self, name):
        """Search by author name and return a generator of Author objects"""
        url = _AUTHSEARCH.format(requests.utils.quote(name))
        return self.nav.search_authors(url)

    def search_keyword(self, keyword):
        """Search by keyword and return a generator of Author objects"""
        url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
        return self.nav.search_authors(url)

    def search_pubs_custom_url(self, url):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        return self.nav.search_publications(url)

    def search_author_custom_url(self, url):
        """Search by custom URL and return a generator of Author objects
        URL should be of the form '/citation?q=...'"""
        return self.nav.search_authors(url)
