import re
import pprint
import hashlib
import random
import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
import copy
from datetime import date


class Publication(object):
    """Returns an object for a single publication"""

    def __init__(self, __data, scholarly, pubtype=None):
        self.bib = dict()
        self._scholarly = scholarly
        self.source = pubtype

        if self.source == 'citations':
            self.__citation_pub(__data)
        elif self.source == 'scholar':
            self.__scholar_pub(__data)

        self._filled = False

    def __citation_pub(self, __data):
        self.bib['title'] = __data.find('a', class_='gsc_a_at').text
        self.id_citations = re.findall(self._scholarly.URLS(
            'CITATIONPUBRE'),
            __data.find('a', class_='gsc_a_at')['data-href'])[0]
        citedby = __data.find(class_='gsc_a_ac')

        if citedby and not (citedby.text.isspace() or citedby.text == ''):
            self.citedby = int(citedby.text)
        year = __data.find(class_='gsc_a_h')

        if (year and year.text and
                not year.text.isspace() and len(year.text) > 0):
            self.bib['year'] = int(year.text)

    def __scholar_pub(self, __data):
        # getting title, google publication id and position on search
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

        authorinfo = databox.find('div', class_='gs_a')
        self.bib['author'] = self.__get_authorlist(authorinfo)

        if databox.find('div', class_='gs_rs'):
            self.bib['abstract'] = databox.find('div', class_='gs_rs').text
            self.bib['abstract'] = self.bib['abstract'].replace(u'\u2026', u'')
            self.bib['abstract'] = self.bib['abstract'].replace(u'\n', u' ')
            self.bib['abstract'] = self.bib['abstract'].strip()

            if self.bib['abstract'][0:8].lower() == 'abstract':
                self.bib['abstract'] = self.bib['abstract'][9:]

        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')

        for link in lowerlinks:
            if (link is not None and
                    link.get('title') is not None and
                    'Cite' == link.get('title')):
                self.url_scholarbib = self.__get_bibtex(cid, pos)
                sclib = self._scholarly.URLS('PUBLIB').format(id=cid)
                sclib = self._scholarly.URLS('HOST').format(sclib)
                self.url_add_sclib = sclib

            if 'Cited by' in link.text:
                self.bib['cites'] = re.findall(r'\d+', link.text)[0]
                self.bib['citesurl'] = self._scholarly.URLS(
                    'HOST').format(link['href'])

        if __data.find('div', class_='gs_ggs gs_fl'):
            self.bib['eprint'] = __data.find(
                'div', class_='gs_ggs gs_fl').a['href']

    @property
    def bibtex(self) -> str:
        """Contains the publication as a bibtex entry
        
        Returns:
            str -- a bibtex entry
        """
        a = BibDatabase()
        a.entries = [self.bib]
        return bibtexparser.dumps(a)

    def __get_bibtex(self, cid: str, pos: str) -> str:
        bib_url = self._scholarly.URLS('BIBCITE').format(cid, pos)
        url = self._scholarly.URLS('HOST').format(bib_url)
        soup = self._scholarly._get_soup(url)
        styles = soup.find_all('a', class_='gs_citi')

        for link in styles:
            if link.string.lower() == "bibtex":
                return link.get('href')
        return ''

    def __get_authorlist(self, authorinfo):
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

    def fill(self):
        """Populate the Publication with information from Google Scholar

        Please notice that this information is not truly reliable because
        Google Scholar might not have all authors and contains different
        versions of the same publication
        """
        if self.source == 'citations':
            url = self._scholarly.URLS("CITATIONPUB").format(self.id_citations)
            soup = self._scholarly._get_soup(
                self._scholarly.URLS('HOST').format(url))
            self.bib['title'] = soup.find('div', id='gsc_vcd_title').text

            if soup.find('a', class_='gsc_vcd_title_link'):
                self.bib['url'] = soup.find(
                    'a', class_='gsc_vcd_title_link')['href']

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
                    self.id_scholarcitedby = re.findall(
                        self._scholarly.URLS('SCHOLARPUBRE'), val.a['href'])[0]

            # number of citation per year
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            self.cites_per_year = dict(zip(years, cites))

            if soup.find('div', class_='gsc_vcd_title_ggi'):
                self.bib['eprint'] = soup.find(
                    'div', class_='gsc_vcd_title_ggi').a['href']
            self._filled = True

        elif self.source == 'scholar':
            self.bib['add_to_lib'] = self.url_add_sclib

            try:
                bibtex = self._scholarly._get_soup(self.url_scholarbib)
                bibtex = bibtex.find('pre').string
                self.bib.update(bibtexparser.loads(bibtex).entries[0])
                self.bib['author_count'] = str(
                    len(self.bib['author'].split('and')))
                self.bib['age'] = str(
                    int(date.today().year) - int(self.bib['year']))
            except:
                # did not find year
                pass

            self._filled = True
        return self

    def __get_citedby(self):
        """Searches GScholar for other articles that cite this Publication and
        returns a Publication generator.
        """
        if not hasattr(self, 'id_scholarcitedby'):
            self.fill()
        if hasattr(self, 'id_scholarcitedby'):
            url = self._scholarly.URLS('SCHOLARPUB').format(
                requests.utils.quote(self.id_scholarcitedby))
            soup = self._scholarly._get_soup(
                self._scholarly.URLS('HOST').format(url))
            return self._scholarly._search_scholar_soup(soup)
        else:
            return []

    def __str__(self):
        x = self.__dict__.copy()
        del x['_scholarly']
        return pprint.pformat(x)

    def __repr__(self):
        return self.__str__()
