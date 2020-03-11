"""scholarly.py"""

from __future__ import absolute_import, division, print_function, unicode_literals

from bs4 import BeautifulSoup

import arrow
import bibtexparser
import codecs
import hashlib
import pprint
import random
import re
import requests
import sys
import time
from abc import ABCMeta, abstractmethod
from stem import Signal
from stem.control import Controller
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36"
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': _USER_AGENT,
    'accept': 'text/html,application/xhtml+xml,application/xml'
    }
_HOST = "https://scholar.google.com"
_AUTHSEARCH = "/citations?view_op=search_authors&hl=en&mauthors={0}"
_CITATIONAUTH = "/citations?user={0}&hl=en"
_CITATIONPUB = "/citations?view_op=view_citation&citation_for_view={0}"
_KEYWORDSEARCH = "/citations?view_op=search_authors&hl=en&mauthors=label:{0}"
_PUBSEARCH = "/scholar?hl=en&q={0}"
_SCHOLARPUB = "/scholar?oi=bibs&hl=en&cites={0}"

_CAPTCHA = "iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']"

_CITATIONAUTHRE = r"user=([\w-]*)"
_CITATIONPUBRE = r"citation_for_view=([\w-]*:[\w-]*)"
_SCHOLARCITERE = r"gs_ocit\(event,\'([\w-]*)\'"
_SCHOLARPUBRE = r"cites=([\w-]*)"
_EMAILAUTHORRE = r"Verified email at "

_pAGESIZE = 100
_PROXY = "127.0.0.1:9050"

class Publication(object):
    """Returns an object for a single publication"""
    def __init__(self, __data, scholarly, pubtype=None):
        self.bib = dict()
        self._scholarly = scholarly
        self.source = pubtype
        if self.source == 'citations':
            self.bib['title'] = __data.find('a', class_='gsc_a_at').text
            self.id_citations = re.findall(_CITATIONPUBRE, __data.find('a', class_='gsc_a_at')['data-href'])[0]
            citedby = __data.find(class_='gsc_a_ac')
            if citedby and not (citedby.text.isspace() or citedby.text == ''):
                self.citedby = int(citedby.text)
            year = __data.find(class_='gsc_a_h')
            if year and year.text and not year.text.isspace() and len(year.text)>0:
                self.bib['year'] = int(year.text)
        elif self.source == 'scholar':
            databox = __data.find('div', class_='gs_ri')
            title = databox.find('h3', class_='gs_rt')
            if title.find('span', class_='gs_ctu'): # A citation
                title.span.extract()
            elif title.find('span', class_='gs_ctc'): # A book or PDF
                title.span.extract()
            self.bib['title'] = title.text.strip()
            if title.find('a'):
                self.bib['url'] = title.find('a')['href']
            authorinfo = databox.find('div', class_='gs_a')
            self.bib['author'] = ' and '.join(self.get_authorlist(authorinfo))
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
                    self.id_scholarcitedby = re.findall(_SCHOLARPUBRE, link['href'])[0]
            if __data.find('div', class_='gs_ggs gs_fl'):
                self.bib['eprint'] = __data.find('div', class_='gs_ggs gs_fl').a['href']
        self._filled = False

    def get_authorlist(self, authorinfo):
        authorlist = list()
        text = authorinfo.text.replace(u'\xa0', u' ')
        text = text.split(' - ')[0]
        for i in text.split(','):
            i = i.strip()
            if bool(re.search(r'\d', i)):
                continue
            if ("Proceedings" in i or "Conference" in i or "Journal" in i
                    or "(" in i or ")" in i or "[" in i or "]" in i
                    or "Transactions" in i):
                continue
            i = i.replace("…", "")
            authorlist.append(i)
        return authorlist


    def fill(self):
        """Populate the Publication with information from its profile"""
        if self.source == 'citations':
            url = _CITATIONPUB.format(self.id_citations)
            soup = self._scholarly._get_soup(_HOST+url)
            self.bib['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                self.bib['url'] = soup.find('a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text
                val = item.find(class_='gsc_vcd_value')
                if key == 'Authors':
                    self.bib['author'] = ' and '.join(self.get_authorlist(val))
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
                    self.id_scholarcitedby = re.findall(_SCHOLARPUBRE, val.a['href'])[0]

            # number of citation per year
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            self.cites_per_year = dict(zip(years, cites))

            if soup.find('div', class_='gsc_vcd_title_ggi'):
                self.bib['eprint'] = soup.find('div', class_='gsc_vcd_title_ggi').a['href']
            self._filled = True
        elif self.source == 'scholar':
            bibtex = self._scholarly._get_page(self.url_scholarbib)
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
            url = _SCHOLARPUB.format(requests.utils.quote(self.id_scholarcitedby))
            soup = self._scholarly._get_soup(_HOST+url)
            return self._scholarly._search_scholar_soup(soup)
        else:
            return []

    def __str__(self):
        return pprint.pformat(self.__dict__)

class Author(object):
    """Returns an object for a single author"""
    def __init__(self, __data, scholarly):
        self._scholarly = scholarly
        if isinstance(__data, str):
            self.id = __data
        else:
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
            self.url_picture = _HOST+'/citations?view_op=medium_photo&user={}'.format(self.id)
            self.name = __data.find('h3', class_=_find_tag_class_name(__data, 'h3', 'name')).text
            affiliation = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'aff'))
            if affiliation:
                self.affiliation = affiliation.text
            email = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'eml'))
            if email:
                self.email = re.sub(_EMAILAUTHORRE, r'@', email.text)
            self.interests = [i.text.strip() for i in
                           __data.find_all('a', class_=_find_tag_class_name(__data, 'a', 'one_int'))]
            citedby = __data.find('div', class_=_find_tag_class_name(__data, 'div', 'cby'))
            if citedby and citedby.text != '':
                self.citedby = int(citedby.text[9:])
        self._filled = False

    def fill(self):
        """Populate the Author with information from their profile"""
        url_citations = _CITATIONAUTH.format(self.id)
        url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
        soup = self._get_soup(_HOST+url)
        self.name = soup.find('div', id='gsc_prf_in').text
        self.affiliation = soup.find('div', class_='gsc_prf_il').text
        self.interests = [i.text.strip() for i in soup.find_all('a', class_='gsc_prf_inta')]
        
        # h-index, i10-index and h-index, i10-index in the last 5 years
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
        years = [int(y.text) for y in soup.find_all('span', class_='gsc_g_t')]
        cites = [int(c.text) for c in soup.find_all('span', class_='gsc_g_al')]
        self.cites_per_year = dict(zip(years, cites))

        # co-authors
        self.coauthors = []
        for row in soup.find_all('span', class_='gsc_rsb_a_desc'):
            new_coauthor = Author(
                    re.findall(_CITATIONAUTHRE, row('a')[0]['href'])[0], self._scholarly)
            new_coauthor.name = row.find(tabindex="-1").text
            new_coauthor.affiliation = row.find(class_="gsc_rsb_a_ext").text
            self.coauthors.append(new_coauthor)


        self.publications = list()
        pubstart = 0
        while True:
            for row in soup.find_all('tr', class_='gsc_a_tr'):
                new_pub = Publication(row, self._scholarly, 'citations')
                self.publications.append(new_pub)
            if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs:
                pubstart += _PAGESIZE
                url = '{0}&cstart={1}&pagesize={2}'.format(url_citations, pubstart, _PAGESIZE)
                soup = _get_soup(_HOST+url)
            else:
                break

        self._filled = True
        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)

class Scholarly:
    __metaclass__ = ABCMeta

    def __init__(self, use_proxy):
        self._use_proxy = use_proxy
        self._session = None

    def _handle_too_many_requests(self):
        """ Google Scholar responded with status too many requests. If we are
        using TOR, renew your identity. If we are not using tor sleep until we
        are allowed to request again."""

        if self._use_proxy:
            with Controller.from_port(port = 9051) as controller:
                print("Refreshing proxy...")
                controller.authenticate(password = "")
                controller.signal(Signal.NEWNYM)
                time.sleep(5)
                self._session = webdriver.Firefox(proxy = Proxy({
                        "proxyType": ProxyType.MANUAL,
                        "httpProxy": "socks5://{0}".format(_PROXY),
                        "sslProxy": "socks5://{0}".format(_PROXY),
                        "ftpProxy": "socks5://{0}".format(_PROXY),
                        "noProxy": ""
                        }))
        else:
            print("""Too many requests from scholarly. Consider using proxy
                  and/or scholarly with selenium. Waiting till the end of the
                  day to continue.""")
            now = datetime.now()
            now_sec = now.minute * 60 + now.second + now.hour * 3600
            time.sleep(24 * 3600 - now_sec)

    @abstractmethod
    def _get_page(self, pagerequest):
        pass

    def _get_soup(self, pagerequest):
        """Return the BeautifulSoup for a page on scholar.google.com"""
        html = self._get_page(pagerequest)
        html = html.replace(u'\xa0', u' ')
        return BeautifulSoup(html, 'html.parser')


    def _search_scholar_soup(self, soup):
        """Generator that returns Publication objects from the search page"""
        while True:
            for row in soup.find_all('div', 'gs_or'):
                yield Publication(row, self, 'scholar')
            if soup.find(class_='gs_ico gs_ico_nav_next'):
                url = soup.find(class_='gs_ico gs_ico_nav_next').parent['href']
                soup = self._get_soup(_HOST+url)
            else:
                break


    def _search_citation_soup(self, soup):
        """Generator that returns Author objects from the author search page"""
        while True:
            for row in soup.find_all('div', 'gsc_1usr'):
                yield Author(row, self)
            next_button = soup.find(class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
            if next_button and 'disabled' not in next_button.attrs:
                url = next_button['onclick'][17:-1]
                url = codecs.getdecoder("unicode_escape")(url)[0]
                soup = self._get_soup(_HOST+url)
            else:
                break

    def _find_tag_class_name(self, __data, tag, text):
        elements = __data.find_all(tag)
        for element in elements:
            if 'class' in element.attrs and text in element.attrs['class'][0]:
                return element.attrs['class'][0]


    def search_pubs_query(self, query):
        """Search by scholar query and return a generator of Publication objects"""
        url = _PUBSEARCH.format(requests.utils.quote(query))
        soup = self._get_soup(_HOST+url)
        return self._search_scholar_soup(soup)


    def search_author(self, name):
        """Search by author name and return a generator of Author objects"""
        url = _AUTHSEARCH.format(requests.utils.quote(name))
        soup = self._get_soup(_HOST+url)
        return self._search_citation_soup(soup)


    def search_keyword(self, keyword):
        """Search by keyword and return a generator of Author objects"""
        url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
        soup = self._get_soup(_HOST+url)
        return self._search_citation_soup(soup)


    def search_pubs_custom_url(self, url):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        soup = self._get_soup(_HOST+url)
        return self._search_scholar_soup(soup)


    def search_author_custom_url(self, url):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/citation?q=...'"""
        soup = self._get_soup(_HOST+url)
        return self._search_citation_soup(soup)

class ScholarlyDefault(Scholarly):

    def __init__(self, use_proxy):
        Scholarly.__init__(self, use_proxy)

        self._session = requests.Session()
        if use_proxy:
            print("using proxy")
            self._session.proxies = {
                "http": "socks5://{0}".format(_PROXY),
                "https": "socks5://{0}".format(_PROXY)
            }
    
    def _get_page(self, pagerequest):
        """Return the data for a page on scholar.google.com"""
        # Note that we include a sleep to avoid being kicked out by google
        time.sleep(5 + random.uniform(0, 5))
        resp = self._session.get(pagerequest, headers=_HEADERS, cookies=_COOKIES)
        if resp.status_code == 200 and "captcha" not in resp.text:
            return resp.text
        elif resp.status_code == 503:
            raise Exception('Error: {0} {1}\nCaptcha detected, consider using scholarly with selenium'
                    .format(resp.status_code, resp.reason))
        elif resp.status_code == 429:
            self._handle_too_many_requests()
            self._get_page(pagerequest)
        elif resp.status_code == 200 and "captcha" in resp.text:
            raise NotImplementedError(
                    "Captcha detected, consider using scholarly with selenium")
        else:
            raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))

class ScholarlySelenium(Scholarly):

    def __init__(self, use_proxy):
        Scholarly.__init__(self, use_proxy)

        if use_proxy:
            self._session = webdriver.Firefox(proxy = Proxy({
                    "proxyType": ProxyType.MANUAL,
                    "httpProxy": "socks5://{0}".format(_PROXY),
                    "httpsProxy": "socks5://{0}".format(_PROXY),
                    "socksProxy": "socks5://{0}".format(_PROXY),
                    "sslProxy": "socks5://{0}".format(_PROXY),
                    "ftpProxy": "socks5://{0}".format(_PROXY),
                    "noProxy": ""
                    }))
        else:
            self._session = webdriver.Firefox()

    def _get_page(self, pagerequest):
        """Return the data for a page on scholar.google.com.
        Note that we include a sleep to avoid overloading the scholar server"""
        self._session.get(pagerequest)
        wait_time = 5 + random.uniform(0, 5)

        # Wait for captcha to show up
        while True:
            wait = WebDriverWait(self._session, wait_time)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, _CAPTCHA)))
            except TimeoutException:
                break

            # Wait for captcha to disapear, if no captcha has shown this does not block
            wait = WebDriverWait(self._session, 1000000000)
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, _CAPTCHA)))

        # Obtain html body
        text = self._session.page_source

        # Check if google figured out, that we are sending automated queries
        if "but your computer or network may be sending automated queries" in text and self._use_proxy:
            self._session.close()
            self._handle_too_many_requests()
            return self._get_page(pagerequest)

        return text

def get_scholarly_instance(use_proxy = False, use_selenium = False):
    if use_selenium:
        return ScholarlySelenium(use_proxy)
    else:
        return ScholarlyDefault(use_proxy)
