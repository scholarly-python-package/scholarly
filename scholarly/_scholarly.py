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

    def search_pubs(self, query):
        """Search by query and returns a generator of Publication objects"""
        url = _PUBSEARCH.format(requests.utils.quote(query))
        return self.nav.search_publications(url)

    def search_pub_list(self, publist: list, filled=False):
        """Searches for the first publication for each term in the list"""
        assert isinstance(publist, list)
        for i in publist:
            yield self.search_single_pub(i, filled)

    def search_terms(self, termlist: list, filled=False) -> dict:
        """Searches for each term in a list an returns dict of generators"""
        assert isinstance(termlist, list)
        return {i: self.search_pubs(i) for i in termlist}

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
