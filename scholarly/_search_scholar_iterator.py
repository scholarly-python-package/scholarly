import re
from .data_types import PublicationSource
from .publication_parser import PublicationParser

class _SearchScholarIterator(object):
    """Iterator that returns Publication objects from the search page
    I have removed all logging from here for simplicity. -V
    """

    def __init__(self, nav, url: str):
        self._url = url
        self._pubtype = PublicationSource.PUBLICATION_SEARCH_SNIPPET if "/scholar?" in url else PublicationSource.JOURNAL_CITATION_LIST
        self._nav = nav
        self._load_url(url)
        self.total_results = self._get_total_results()
        self.pub_parser = PublicationParser(self._nav)

    def _load_url(self, url: str):
        # this is temporary until setup json file
        self._soup = self._nav._get_soup(url)
        self._pos = 0
        self._rows = self._soup.find_all('div', class_='gs_r gs_or gs_scl') + self._soup.find_all('div', class_='gsc_mpat_ttl')

    def _get_total_results(self):
        if self._soup.find("div", class_="gs_pda"):
            return None

        for x in self._soup.find_all('div', class_='gs_ab_mdw'):
            # Accounting for different thousands separators:
            # comma, dot, space, apostrophe
            match = re.match(pattern=r'(^|\s*About)\s*([0-9,\.\s’]+)', string=x.text)
            if match:
                return int(re.sub(pattern=r'[,\.\s’]',repl='', string=match.group(2)))
        return 0

    # Iterator protocol

    def __iter__(self):
        return self

    def __next__(self):
        if self._pos < len(self._rows):
            row = self._rows[self._pos]
            self._pos += 1
            res = self.pub_parser.get_publication(row, self._pubtype)
            return res
        elif self._soup.find(class_='gs_ico gs_ico_nav_next'):
            url = self._soup.find(
                class_='gs_ico gs_ico_nav_next').parent['href']
            self._url = url
            self._load_url(url)
            return self.__next__()
        else:
            raise StopIteration

    # Pickle protocol
    def __getstate__(self):
        return {'url': self._url, 'pos': self._pos}

    def __setstate__(self, state):
        # this needs validation -V
        self._load_url(state['url'])
        self._pos = state['pos']

