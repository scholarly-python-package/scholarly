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
        self.nav._use_proxy(http, https)        
        
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
        citations = '&as_vis={0}'.format(1- int(citations))
        patents = '&as_sdt={0},33'.format(1- int(patents))
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
