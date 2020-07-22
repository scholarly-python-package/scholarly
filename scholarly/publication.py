import re
import bibtexparser
import arrow
import pprint
from bibtexparser.bibdatabase import BibDatabase

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
        self._nav = nav
        self._load_url(url)

    def _load_url(self, url: str):
        # this is temporary until setup json file
        self._soup = self._nav._get_soup(url)
        self._pos = 0
        self._rows = self._soup.find_all('div', class_='gs_r gs_or gs_scl')

    # Iterator protocol

    def __iter__(self):
        return self

    def __next__(self):
        if self._pos < len(self._rows):
            row = self._rows[self._pos]
            self._pos += 1
            return Publication(self._nav, row, 'scholar')
        elif self._soup.find(class_='gs_ico gs_ico_nav_next'):
            url = self._soup.find(
                class_='gs_ico gs_ico_nav_next').parent['href']
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


class Publication(object):
    """Returns an object for a single publication"""

    def __init__(self, nav, __data, pubtype=None):
        self.nav = nav
        self.bib = dict()
        self.source = pubtype
        if self.source == 'citations':
            self._citation_pub(__data)
        elif self.source == 'scholar':
            self._scholar_pub(__data)
        self._filled = False

    def _citation_pub(self, __data):
        self.bib['title'] = __data.find('a', class_='gsc_a_at').text
        self.id_citations = re.findall(_CITATIONPUBRE, __data.find(
            'a', class_='gsc_a_at')['data-href'])[0]
        citedby = __data.find(class_='gsc_a_ac')

        self.bib["cites"] = "0"
        if citedby and not (citedby.text.isspace() or citedby.text == ''):
            self.bib["cites"] = citedby.text.strip()

        year = __data.find(class_='gsc_a_h')
        if (year and year.text
                and not year.text.isspace()
                and len(year.text) > 0):
            self.bib['year'] = year.text.strip()

    def _get_authorlist(self, authorinfo):
        authorlist = list()
        text = authorinfo.split(' - ')[0]
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

        self.bib['gsrank'] = str(int(pos) + 1)

        if title.find('span', class_='gs_ctu'):  # A citation
            title.span.extract()
        elif title.find('span', class_='gs_ctc'):  # A book or PDF
            title.span.extract()

        self.bib['title'] = title.text.strip()

        if title.find('a'):
            self.bib['url'] = title.find('a')['href']

        authorinfo = databox.find('div', class_='gs_a').text
        authorinfo = authorinfo.replace(u'\xa0', u' ')       # NBSP
        authorinfo = authorinfo.replace(u'&amp;', u'&')      # Ampersand
        self.bib["author"] = self._get_authorlist(authorinfo)

        # There are 4 (known) patterns in the author/venue/year/host line:
        #  (A) authors - host
        #  (B) authors - venue, year - host
        #  (C) authors - venue - host
        #  (D) authors - year - host
        # The authors are handled above so below is only concerned with
        # the middle venue/year part. In principle the venue is separated
        # from the year by a comma. However, there exist venues with commas
        # and as shown above there might not always be a venue AND a year...
        venueyear = authorinfo.split(' - ')
        # If there is no middle part (A) then venue and year are unknown.
        if len(venueyear) <= 2:
            self.bib['venue'], self.bib['year'] = 'NA', 'NA'
        else:
            venueyear = venueyear[1].split(',')
            venue = 'NA'
            year = venueyear[-1].strip()
            if year.isnumeric() and len(year) == 4:
                self.bib['year'] = year
                if len(venueyear) >= 2:
                    venue = ','.join(venueyear[0:-1]) # everything but last
            else:
                venue = ','.join(venueyear) # everything
                self.bib['year'] = 'NA'
            self.bib['venue'] = venue

        if databox.find('div', class_='gs_rs'):
            self.bib['abstract'] = databox.find('div', class_='gs_rs').text
            self.bib['abstract'] = self.bib['abstract'].replace(u'\u2026', u'')
            self.bib['abstract'] = self.bib['abstract'].replace(u'\n', u' ')
            self.bib['abstract'] = self.bib['abstract'].strip()

            if self.bib['abstract'][0:8].lower() == 'abstract':
                self.bib['abstract'] = self.bib['abstract'][9:].strip()

        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')

        self.bib["cites"] = "0"

        for link in lowerlinks:
            if (link is not None and
                    link.get('title') is not None and
                    'Cite' == link.get('title')):
                self.url_scholarbib = _BIBCITE.format(cid, pos)
                sclib = self.nav.publib.format(id=cid)
                self.url_add_sclib = sclib

            if 'Cited by' in link.text:
                self.bib['cites'] = re.findall(r'\d+', link.text)[0].strip()
                self.citations_link = link['href']

        if __data.find('div', class_='gs_ggs gs_fl'):
            self.bib['eprint'] = __data.find(
                'div', class_='gs_ggs gs_fl').a['href']

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
        if self.source == 'citations':
            url = _CITATIONPUB.format(self.id_citations)
            soup = self.nav._get_soup(url)
            self.bib['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                self.bib['url'] = soup.find(
                    'a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text.strip().lower()
                val = item.find(class_='gsc_vcd_value')
                if key == 'authors':
                    self.bib['author'] = ' and '.join(
                        [i.strip() for i in val.text.split(',')])
                elif key == 'journal':
                    self.bib['journal'] = val.text
                elif key == 'volume':
                    self.bib['volume'] = val.text
                elif key == 'issue':
                    self.bib['number'] = val.text
                elif key == 'pages':
                    self.bib['pages'] = val.text
                elif key == 'publisher':
                    self.bib['publisher'] = val.text
                elif key == 'Publication date':

                    patterns = ['YYYY/M',
                                'YYYY/MM/DD',
                                'YYYY',
                                'YYYY/M/DD',
                                'YYYY/M/D',
                                'YYYY/MM/D']
                    self.bib['year'] = arrow.get(val.text, patterns).year
                elif key == 'description':
                    if val.text[0:8].lower() == 'abstract':
                        val = val.text[9:].strip()
                    abstract = val.find(class_='gsh_csp')
                    if abstract is None:
                        abstract = val.find(class_='gsh_small')
                    self.bib['abstract'] = abstract.text
                elif key == 'total citations':
                    self.bib['cites'] = re.findall(
                        _SCHOLARPUBRE, val.a['href'])[0]

            # number of citation per year
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            self.cites_per_year = dict(zip(years, cites))

            if soup.find('div', class_='gsc_vcd_title_ggi'):
                self.bib['eprint'] = soup.find(
                    'div', class_='gsc_vcd_title_ggi').a['href']
            self._filled = True
        elif self.source == 'scholar':
            bibtex_url = self._get_bibtex(self.url_scholarbib)
            bibtex = self.nav._get_page(bibtex_url)
            self.bib.update(bibtexparser.loads(bibtex).entries[0])
            self._filled = True
        return self

    @property
    def citedby(self) -> _SearchScholarIterator or list:
        """Searches Google Scholar for other articles that cite this Publication and
        returns a Publication generator.

        :getter: Returns a Generator of Publications that cited the current.
        :type: Iterator[:class:`Publication`]
        """
        if not self.filled:
            self.fill()
        return _SearchScholarIterator(self.nav, self.citations_link)

    @property
    def bibtex(self) -> str:
        """Returns the publication as a Bibtex entry

        :getter: Returns a Bibtex entry in text format
        :type: str
        """
        if not self._filled:
            self.fill()
        a = BibDatabase()
        a.entries = [self.bib]
        return bibtexparser.dumps(a)

    def _get_bibtex(self, bib_url) -> str:
        soup = self.nav._get_soup(bib_url)
        styles = soup.find_all('a', class_='gs_citi')

        for link in styles:
            if link.string.lower() == "bibtex":
                return link.get('href')
        return ''

    def __str__(self):
        pdict = dict(self.__dict__)
        try:
            pdict["filled"] = self.filled
            del pdict['nav']
            del pdict['_filled']
        except Exception:
            raise

        return pprint.pformat(pdict)

    def __repr__(self):
        return self.__str__()
