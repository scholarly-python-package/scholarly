"""scholarly.py"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bs4 import BeautifulSoup

import arrow
import bibtexparser
import codecs
import hashlib
import logging
import pprint
import random
import re
import requests
import time
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' +
                  '(KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 ' +
                  'Chrome/41.0.2272.76 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml'
}
_HOST = 'https://scholar.google.com'
_AUTHSEARCH = '/citations?hl=en&view_op=search_authors&mauthors={0}'
_CITATIONAUTH = '/citations?hl=en&user={0}'
_CITATIONPUB = '/citations?hl=en&view_op=view_citation&citation_for_view={0}'
_KEYWORDSEARCH = '/citations?hl=en&view_op=search_authors&mauthors=label:{0}'
_PUBSEARCH = '/scholar?hl=en&q={0}'
_SCHOLARPUB = '/scholar?hl=en&oi=bibs&cites={0}'

_CITATIONAUTHRE = r'user=([\w-]*)'
_CITATIONPUBRE = r'citation_for_view=([\w-]*:[\w-]*)'
_SCHOLARCITERE = r'gs_ocit\(event,\'([\w-]*)\''
_SCHOLARPUBRE = r'cites=([\w-]*)'
_EMAILAUTHORRE = r'Verified email at '

_PAGESIZE = 100
_TIMEOUT = 2

_PROXIES = {
    "http": None,
    "https": None,
}

_HTTP_PROXY = None
_HTTPS_PROXY = None

logging.basicConfig(filename='scholar.log', level=logging.INFO)
logger = logging.getLogger('scholarly')
_TOR_SOCK = "socks5://127.0.0.1:9050"

def _tor_works() -> bool:
    """ Checks if Tor is working"""
    with requests.Session() as session:
        session.proxies = {
            'http': _TOR_SOCK,
            'https': _TOR_SOCK
        }
        try:
            resp = session.get("https://www.google.com")
            return resp.status_code == 200
        except Exception as e:
            return False


_TOR_WORKS = _tor_works()


def _refresh_tor_id():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="scholarly_password")
        controller.signal(Signal.NEWNYM)


def _can_refresh_tor():
    time.sleep(1+random.uniform(0, 1))
    try:
        _refresh_tor_id()
        return True
    except Exception as e:
        return False


_CAN_REFRESH_TOR = _can_refresh_tor()


def use_proxy(http=_TOR_SOCK, https=_TOR_SOCK):
    """ Routes scholarly through a proxy (e.g. tor).
        Requires pysocks
        Proxy must be running."""
    logger.info("Enabling proxies: http=%r https=%r", http, https)
    global _PROXIES
    _PROXIES = {
        "http": http,
        "https": https,
    }


def use_tor():
    logger.info("Setting tor as the proxy")
    use_proxy(http=_TOR_SOCK,
              https=_TOR_SOCK)


def _has_captcha(text):
    flags = ["Please show you're not a robot",
             "network may be sending automated queries",
             "have detected unusual traffic from your computer",
             "scholarly_captcha"]
    return any([i in text for i in flags])


def _get_page(pagerequest):
    """Return the data for a page on scholar.google.com"""
    logger.info("Getting %s", pagerequest)
    # Delay for avoiding overloading scholar
    time.sleep(1+random.uniform(0, 1))
    resp = None
    while True:
        # If Tor is running we use the proxy
        with requests.Session() as session:
            if _TOR_WORKS:
                # Tor uses the 9050 port as the default socks port
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
                    if _has_captcha(resp.text):
                        logger.info("Got a CAPTCHA. Retrying...")
                    else:
                        break
                else:
                    logger.info(f"""Got a response code {resp.status_code}. 
                                    Retrying...""")

            except Exception as e:
                logger.info(f"Exception {e} while fetching page. Retrying...")
                # Check if Tor is running and refresh it
                if _TOR_WORKS and _CAN_REFRESH_TOR:
                    logger.info("Refreshing Tor ID...")
                    _refresh_tor_id()

    return resp.text


def _get_soup(pagerequest):
    """Return the BeautifulSoup for a page on scholar.google.com"""
    html = _get_page(pagerequest)
    html = html.replace(u'\xa0', u' ')
    return BeautifulSoup(html, 'html.parser')


class _SearchScholarIterator(object):
    """Iterator that returns Publication objects from the search page"""

    def __init__(self, url):
        logger.info("Reading search page")

        self._load_url(url)

    def _load_url(self, url):
        self._soup = _get_soup(_HOST + url)
        self.url = url
        self._pos = 0
        self._rows = self._soup.find_all('div', class_='gs_r gs_or gs_scl')
        logger.info("Found %d publications", len(self._rows))

    # Iterator protocol

    def __iter__(self):
        return self

    def __next__(self):
        if self._pos < len(self._rows):
            row = self._rows[self._pos]
            self._pos += 1
            return Publication(row, 'scholar')
        elif self._soup.find(class_='gs_ico gs_ico_nav_next'):
            logger.info("Loading next search page")
            url = self._soup.find(
                class_='gs_ico gs_ico_nav_next').parent['href']
            self._load_url(url)
            return self.__next__()
        else:
            logger.info("No more search pages")
            raise StopIteration

    # Pickle protocol

    def __getstate__(self):
        return {'url': self.url, 'pos': self._pos}

    def __setstate__(self, state):
        self._load_url(state['url'])
        self._pos = state['pos']


def _search_citation_soup(soup):
    """Generator that returns Author objects from the author search page"""
    while True:
        rows = soup.find_all('div', 'gsc_1usr')
        logger.info("Found %d authors", len(rows))
        for row in rows:
            yield Author(row)
        next_button = soup.find(
            class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
        if next_button and 'disabled' not in next_button.attrs:
            logger.info("Loading next page of authors")
            url = next_button['onclick'][17:-1]
            url = codecs.getdecoder("unicode_escape")(url)[0]
            soup = _get_soup(_HOST+url)
        else:
            logger.info("No more pages of authors")
            break


def _find_tag_class_name(__data, tag, text):
    elements = __data.find_all(tag)
    for element in elements:
        if 'class' in element.attrs and text in element.attrs['class'][0]:
            return element.attrs['class'][0]


class Publication(object):
    """Returns an object for a single publication"""

    def __init__(self, __data, pubtype=None):
        self.bib = dict()
        self.source = pubtype
        if self.source == 'citations':
            self.bib['title'] = __data.find('a', class_='gsc_a_at').text
            self.id_citations = re.findall(_CITATIONPUBRE, __data.find(
                'a', class_='gsc_a_at')['data-href'])[0]
            citedby = __data.find(class_='gsc_a_ac')
            if citedby and not (citedby.text.isspace() or citedby.text == ''):
                self.citedby = int(citedby.text)
            year = __data.find(class_='gsc_a_h')
            if year and year.text and not year.text.isspace() and len(year.text) > 0:
                self.bib['year'] = int(year.text)
        elif self.source == 'scholar':
            databox = __data.find('div', class_='gs_ri')
            title = databox.find('h3', class_='gs_rt')
            if title.find('span', class_='gs_ctu'):  # A citation
                title.span.extract()
            elif title.find('span', class_='gs_ctc'):  # A book or PDF
                title.span.extract()
            self.bib['title'] = title.text.strip()
            if title.find('a'):
                self.bib['url'] = title.find('a')['href']
            authorinfo = databox.find('div', class_='gs_a')
            self.bib['author'] = ' and '.join(
                [i.strip() for i in authorinfo.text.split(' - ')[0].split(',')])
            try:
                self.bib['venue'], self.bib['year'] = authorinfo.text.split(
                    ' - ')[1].split(',')
            except Exception as e:
                self.bib['venue'], self.bib['year'] = 'NA', 'NA'
            if databox.find('div', class_='gs_rs'):
                self.bib['abstract'] = databox.find('div', class_='gs_rs').text
                if self.bib['abstract'][0:8].lower() == 'abstract':
                    self.bib['abstract'] = self.bib['abstract'][9:].strip()
            lowerlinks = databox.find('div', class_='gs_fl').find_all('a')
            for link in lowerlinks:
                if 'Import into BibTeX' in link.text:
                    self.url_scholarbib = link['href']
                if 'Cited by' in link.text:
                    self.citedby = int(re.findall(r'\d+', link.text)[0])
                    self.id_scholarcitedby = re.findall(
                        _SCHOLARPUBRE, link['href'])[0]
            if __data.find('div', class_='gs_ggs gs_fl'):
                self.bib['eprint'] = __data.find(
                    'div', class_='gs_ggs gs_fl').a['href']
        self._filled = False

    def fill(self):
        """Populate the Publication with information from its profile"""
        if self.source == 'citations':
            url = _CITATIONPUB.format(self.id_citations)
            soup = _get_soup(_HOST+url)
            self.bib['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                self.bib['url'] = soup.find(
                    'a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text
                val = item.find(class_='gsc_vcd_value')
                if key == 'Authors':
                    self.bib['author'] = ' and '.join(
                        [i.strip() for i in val.text.split(',')])
                elif key == 'Journal':
                    self.bib['journal'] = val.text
                elif key == 'Volume':
                    self.bib['volume'] = val.text
                elif key == 'Issue':
                    self.bib['number'] = val.text
                elif key == 'Pages':
                    self.bib['pages'] = val.text
                elif key == 'Publisher':
                    self.bib['publisher'] = val.text
                elif key == 'Publication date':
                    self.bib['year'] = arrow.get(val.text).year
                elif key == 'Description':
                    if val.text[0:8].lower() == 'abstract':
                        val = val.text[9:].strip()
                    self.bib['abstract'] = val
                elif key == 'Total citations':
                    self.id_scholarcitedby = re.findall(
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
            bibtex = _get_page(self.url_scholarbib)
            self.bib.update(bibtexparser.loads(bibtex).entries[0])
            self._filled = True
        return self

    def get_citedby(self):
        """Searches GScholar for other articles that cite this Publication and
        returns a Publication generator.
        """
        if not hasattr(self, 'id_scholarcitedby'):
            self.fill()
        if hasattr(self, 'id_scholarcitedby'):
            url = _SCHOLARPUB.format(
                requests.utils.quote(self.id_scholarcitedby))
            return _SearchScholarIterator(url)
        else:
            return []

    def __str__(self):
        return pprint.pformat(self.__dict__)


class Author(object):
    """Returns an object for a single author"""

    def __init__(self, __data):
        if isinstance(__data, str):
            self.id = __data
        else:
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
            self.url_picture = _HOST + \
                '/citations?view_op=medium_photo&user={}'.format(self.id)
            self.name = __data.find(
                'h3', class_=_find_tag_class_name(__data, 'h3', 'name')).text
            affiliation = __data.find(
                'div', class_=_find_tag_class_name(__data, 'div', 'aff'))
            if affiliation:
                self.affiliation = affiliation.text
            email = __data.find(
                'div', class_=_find_tag_class_name(__data, 'div', 'eml'))
            if email:
                self.email = re.sub(_EMAILAUTHORRE, r'@', email.text)
            self.interests = [i.text.strip() for i in
                              __data.find_all('a', class_=_find_tag_class_name(__data, 'a', 'one_int'))]
            citedby = __data.find(
                'div', class_=_find_tag_class_name(__data, 'div', 'cby'))
            if citedby and citedby.text != '':
                self.citedby = int(citedby.text[9:])
        self._filled = False

    # all Author object sections for fill() method
    sections = ['basic',
                'citation_indices',
                'citation_num',
                'co-authors',
                'publications']
    sections = {section: section for section in sections}

    def fill(self, sections=['all']):
        """Populate the Author with information from their profile

        The `sections` argument allows for finer granularity of the profile
        information to be pulled.

        Parameters
        ----------
        sections : list of str
            The sections of author information that should be filled. They
            are broken down as follows:
            'basic' = name, affiliation, and interests;
            'citation_indices' = h-index, i10-index, and 5-year analogues;
            'citation_num' = number of citations per year;
            'co-authors' = co-authors;
            'publications' = publications;
            'all' = all of the above (this is the default)
        """
        sections = [section.lower() for section in sections]
        url_citations = _CITATIONAUTH.format(self.id)
        url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
        soup = _get_soup(_HOST+url)

        # basic data
        if self.sections['basic'] in sections or 'all' in sections:
            self.name = soup.find('div', id='gsc_prf_in').text
            self.affiliation = soup.find('div', class_='gsc_prf_il').text
            self.interests = [i.text.strip() for i in
                              soup.find_all('a', class_='gsc_prf_inta')]

        # h-index, i10-index and h-index, i10-index in the last 5 years
        if self.sections['citation_indices'] in sections or 'all' in sections:
            index = soup.find_all('td', class_='gsc_rsb_std')
            if index:
                self.citedby = int(index[0].text)
                self.citedby5y = int(index[1].text)
                self.hindex = int(index[2].text)
                self.hindex5y = int(index[3].text)
                self.i10index = int(index[4].text)
                self.i10index5y = int(index[5].text)
            else:
                self.hindex = self.hindex5y = self.i10index = self.i10index5y = 0

        # number of citations per year
        if self.sections['citation_num'] in sections or 'all' in sections:
            years = [int(y.text)
                     for y in soup.find_all('span', class_='gsc_g_t')]
            cites = [int(c.text)
                     for c in soup.find_all('span', class_='gsc_g_al')]
            self.cites_per_year = dict(zip(years, cites))

        # co-authors
        if self.sections['co-authors'] in sections or 'all' in sections:
            self.coauthors = []
            for row in soup.find_all('span', class_='gsc_rsb_a_desc'):
                new_coauthor = Author(re.findall(
                    _CITATIONAUTHRE, row('a')[0]['href'])[0])
                new_coauthor.name = row.find(tabindex="-1").text
                new_coauthor.affiliation = row.find(
                    class_="gsc_rsb_a_ext").text
                self.coauthors.append(new_coauthor)

        # publications
        if self.sections['publications'] in sections or 'all' in sections:
            self.publications = list()
            pubstart = 0
            while True:
                for row in soup.find_all('tr', class_='gsc_a_tr'):
                    new_pub = Publication(row, 'citations')
                    self.publications.append(new_pub)
                if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs:
                    pubstart += _PAGESIZE
                    url = '{0}&cstart={1}&pagesize={2}'.format(
                        url_citations, pubstart, _PAGESIZE)
                    soup = _get_soup(_HOST+url)
                else:
                    break

        if 'all' in sections or set(sections) == set(self.sections.values()):
            self._filled = True

        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)


def search_pubs_query(query):
    """Search by scholar query and return a generator of Publication objects"""
    url = _PUBSEARCH.format(requests.utils.quote(query))
    return _SearchScholarIterator(url)


def search_author(name):
    """Search by author name and return a generator of Author objects"""
    url = _AUTHSEARCH.format(requests.utils.quote(name))
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)


def search_keyword(keyword):
    """Search by keyword and return a generator of Author objects"""
    url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)


def search_pubs_custom_url(url):
    """Search by custom URL and return a generator of Publication objects
    URL should be of the form '/scholar?q=...'"""
    return _SearchScholarIterator(url)


def search_author_custom_url(url):
    """Search by custom URL and return a generator of Publication objects
    URL should be of the form '/citation?q=...'"""
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)
