import re
import bibtexparser
import arrow
import pprint
from bibtexparser.bibdatabase import BibDatabase
import inspect

_HOST = 'https://scholar.google.com{0}'
_SCHOLARPUBRE = r'cites=([\w-]*)'
_CITATIONPUB = '/citations?hl=en&view_op=view_citation&citation_for_view={0}'
_SCHOLARPUB = '/scholar?hl=en&oi=bibs&cites={0}'
_CITATIONPUBRE = r'citation_for_view=([\w-]*:[\w-]*)'
_BIBCITE = '/scholar?q=info:{0}:scholar.google.com/\
&output=cite&scirp={1}&hl=en'


class _SearchScholarIterator(object):
    """Iterator that returns Publication objects from the search page
    I have removed all logging from here for simplicity. -V
    """

    def __init__(self, nav, url: str):
        self._url = url
        self.__nav = nav
        self._load_url(url)
        nav.logger.info(url)

    def _load_url(self, url: str):
        # this is temporary until setup json file
        self._soup = self.__nav._get_soup(url, False)
        self._pos = 0
        self._rows = self._soup.find_all('div', class_='gs_r gs_or gs_scl')

    # Iterator protocol

    def __iter__(self):
        return self

    def __next__(self):
        if self._pos < len(self._rows):
            row = self._rows[self._pos]
            self._pos += 1
            return Publication(self.__nav, row, 'scholar')
        elif self._soup.find(class_='gs_ico gs_ico_nav_next'):
            url = self._soup.find(
                class_='gs_ico gs_ico_nav_next').parent['href']
            self._load_url(_HOST.format(url))
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


class Publication(object):
    """Returns an object for a single publication"""

    def __init__(self, nav, __data, pubtype=None):
        self.__nav = nav
        self._bib = dict()
        self._source = pubtype
        self._citedby = None
        if self._source == 'citations':
            self._citation_pub(__data)
        elif self._source == 'scholar':
            self._scholar_pub(__data)
        self._filled = False

    def _citation_pub(self, __data):
        self._bib['title'] = __data.find('a', class_='gsc_a_at').text
        self.id_citations = re.findall(_CITATIONPUBRE, __data.find(
            'a', class_='gsc_a_at')['data-href'])[0]
        citedby = __data.find(class_='gsc_a_ac')

        self.citation_count = 0
        self.citations_link = ""

        if citedby and not (citedby.text.isspace() or citedby.text == ''):
            self.citation_count = int(citedby.text.strip())
            self.citations_link = _HOST.format(citedby.get('href'))

        year = __data.find(class_='gsc_a_y')
        if (year and year.text
                and not year.text.isspace()
                and len(year.text) > 0):
            self._bib['year'] = year.text.strip()

    def _get_authorlist(self, authorinfo):
        authorlist = list()
        text = authorinfo.text.replace(u'\xa0', u' ')
        text = text.split(' - ')[0]
        for i in text.split(','):
            i = i.strip()
            if bool(re.search(r'\d', i)):
                continue
            if ("Proceedings" in i or "Conference" in i or "Journal" in i or
                    "(" in i or ")" in i or "[" in i or "]" in i or
                    "Transactions" in i):
                continue
            i = i.replace("…", "")
            authorlist.append(i)
        return authorlist

    def _scholar_pub(self, __data):
        databox = __data.find('div', class_='gs_ri')
        title = databox.find('h3', class_='gs_rt')

        cid = __data.get('data-cid')
        pos = __data.get('data-rp')

        self._gsrank = str(int(pos) + 1)

        if title.find('span', class_='gs_ctu'):  # A citation
            title.span.extract()
        elif title.find('span', class_='gs_ctc'):  # A book or PDF
            title.span.extract()

        self._bib['title'] = title.text.strip()

        if title.find('a'):
            self._url = title.find('a')['href']

        authorinfo = databox.find('div', class_='gs_a')
        self._bib["author"] = self._get_authorlist(authorinfo)

        try:
            self._bib['venue'], self._bib['year'] = authorinfo.text.split(
                ' - ')[1].split(',')
        except Exception:
            self._bib['venue'], self._bib['year'] = 'NA', 'NA'

        if databox.find('div', class_='gs_rs'):
            self._abstract = databox.find('div', class_='gs_rs').text
            self._abstract = self._abstract.replace(u'\u2026', u'')
            self._abstract = self._abstract.replace(u'\n', u' ')
            self._abstract = self._abstract.strip()

            if self._abstract[0:8].lower() == 'abstract':
                self._abstract = self._abstract[9:].strip()

        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')

        self._citation_count = 0

        for link in lowerlinks:
            if (link is not None and
                    link.get('title') is not None and
                    'cite' == link.get('title').lower()):
                self.url_scholarbib = self._get_bibtex(cid, pos)
                sclib = self.__nav.publib.format(id=cid)
                self.url_add_sclib = _HOST.format(sclib)

            if 'cited by' in link.text.lower():
                self.citation_count = int(
                    re.findall(r'\d+', link.text)[0].strip())
                self.citations_link = _HOST.format(link.get("href"))

        eprint = __data.find('div', class_='gs_ggs gs_fl')
        if eprint:
            self._bib['eprint'] = eprint.a['href']

    @property
    def filled(self) -> bool:
        """Indicates whether a publication has been filled

        :getter: `True` if publication is filled, `False` otherwise.
        :type: bool

        # TODO: Example
        """
        return self._filled

    def fill(self):
        """Populate the Publication with information from its profile"""
        if self._source == 'citations':
            url = _CITATIONPUB.format(self.id_citations)
            soup = self.__nav._get_soup(url)
            # print(soup)
            self._bib['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                self._bib['url'] = soup.find(
                    'a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text.strip().lower()
                val = item.find(class_='gsc_vcd_value')
                if key == 'authors':
                    self._bib['author'] = ' and '.join(
                        [i.strip() for i in val.text.split(',')])
                elif key == 'journal':
                    self._bib['journal'] = val.text
                elif key == 'volume':
                    self._bib['volume'] = val.text
                elif key == 'issue':
                    self._bib['number'] = val.text
                elif key == 'pages':
                    self._bib['pages'] = val.text
                elif key == 'publisher':
                    self._bib['publisher'] = val.text
                elif key == 'Publication date':
                    patterns = ['YYYY/M',
                                'YYYY/MM/DD',
                                'YYYY',
                                'YYYY/M/DD',
                                'YYYY/M/D',
                                'YYYY/MM/D']
                    self._bib['year'] = arrow.get(val.text, patterns).year
                elif key == 'description':
                    if val.text[0:8].lower() == 'abstract':
                        val = val.text[9:].strip()
                    abstract = val.find(class_='gsh_csp')
                    if abstract is None:
                        abstract = val.find(class_='gsh_small')
                    self._abstract = abstract.text
                elif key == 'total citations':
                    self.citation_count = int(re.findall(
                        _SCHOLARPUBRE, val.a['href'])[0])

            # number of citation per year
            
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            self.cites_per_year = dict(zip(years, cites))
            eprint = soup.find('div', class_='gsc_vcd_title_ggi')
            if eprint:
                self._bib['eprint'] = eprint.a['href']
        elif self._source == 'scholar':
            bibtex = self.__nav._get_page(self.url_scholarbib)
            self._bib.update(bibtexparser.loads(bibtex).entries[0])

        if self._citedby is None:
            self._citedby = _SearchScholarIterator(self.__nav, 
                self.citations_link)

        self._filled = True
        return self

    @property
    def citedby(self) -> _SearchScholarIterator or list:
        """Searches GScholar for other articles that cite this Publication and
        returns a Publication generator.

        :getter: Returns a Generator of Publications that cited the current.
        :type: Iterator[:class:`Publication`]
        """
        if not self.filled:
            return "Run fill() to get citedby"

        return self._citedby

    @property
    def bibtex(self) -> str:
        """Returns the publication as a bibtex entry

        :getter: Returns a bibtex entry in text format
        :type: str
        """
        if self._source == "citations" or not self._filled:
            return self._bib
        a = BibDatabase()
        a.entries = [self._bib]
        return bibtexparser.dumps(a)

    def _get_bibtex(self, cid: str, pos: str) -> str:
        if self._source == "citations":
            return ""

        bib_url = _BIBCITE.format(cid, pos)
        soup = self.__nav._get_soup(bib_url)
        styles = soup.find_all('a', class_='gs_citi')

        for link in styles:
            if link.string.lower() == "bibtex":
                return link.get('href')
        return ''

    def _get_public_attrs(self):
        res = {}
        for i in dir(self):
            if not i.startswith("_"):
                att = getattr(self, i)
                if not inspect.ismethod(att):
                    res[i] = att
        return res

    def __str__(self):
        return pprint.pformat(self._get_public_attrs())

    def __repr__(self):
        pdict = self._get_public_attrs()
        return pprint.pformat(pdict)
