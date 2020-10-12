import re
import bibtexparser
import arrow
import pprint
from bibtexparser.bibdatabase import BibDatabase
from .data_types import PublicationCitation, PublicationScholar


_HOST = 'https://scholar.google.com{0}'
_SCHOLARPUBRE = r'cites=([\w-]*)'
_CITATIONPUB = '/citations?hl=en&view_op=view_citation&citation_for_view={0}'
_SCHOLARPUB = '/scholar?hl=en&oi=bibs&cites={0}'
_CITATIONPUBRE = r'citation_for_view=([\w-]*:[\w-]*)'
_BIBCITE = '/scholar?q=info:{0}:scholar.google.com/\
&output=cite&scirp={1}&hl=en'
_CITEDBYLINK = '/scholar?cites={0}'


class _SearchScholarIterator(object):
    """Iterator that returns Publication objects from the search page
    I have removed all logging from here for simplicity. -V
    """

    def __init__(self, nav, url: str):
        self._url = url
        self._nav = nav
        self._load_url(url)
        self.pub_parser = PublicationParser(self._nav)

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
            res = self.pub_parser.get_publication(row, 'scholar')
            return res
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


class PublicationParser(object):
    """Returns an object for a single publication"""

    def __init__(self, nav):
        self.nav = nav

    def _citation_pub(self, __data, publication: PublicationCitation):
        # create the bib entry in the dictionary
        publication['bib']['title'] = __data.find('a', class_='gsc_a_at').text
        publication['author_pub_id'] = re.findall(_CITATIONPUBRE, __data.find(
            'a', class_='gsc_a_at')['data-href'])[0]
        citedby = __data.find(class_='gsc_a_ac')

        publication['bib']["cites"] = 0
        if citedby and not (citedby.text.isspace() or citedby.text == ''):
            publication['bib']["cites"] = int(citedby.text.strip())

        year = __data.find(class_='gsc_a_h')
        if (year and year.text
                and not year.text.isspace()
                and len(year.text) > 0):
            publication['bib']['pub_year'] = year.text.strip()
        
        return publication

    def get_publication(self, __data, pubtype=None):

        publication = {}
        if pubtype == 'citations':
            publication: PublicationCitation = {'container_type': 'Publication'}
        elif pubtype == 'scholar':
            publication: PublicationScholar = {'container_type': 'Publication'}
        publication['source'] = pubtype
        publication['bib'] = {}
        publication['filled'] = False

        if publication['source'] == 'citations':
            return self._citation_pub(__data, publication)
        elif publication['source'] == 'scholar':
            return self._scholar_pub(__data, publication)
        else:
            return publication

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


    def _get_author_id_list(self, authorinfo_inner_html):
        author_id_list = list()
        html = authorinfo_inner_html.split(' - ')[0]
        for author_html in html.split(','):
            author_html = author_html.strip()
            match = re.search('\\?user=(.*?)&amp;', author_html)
            if match:
                author_id_list.append(match.groups()[0])
            # else: #TODO: might need to remove
            #     author_id_list.append(None)
        return author_id_list

    def _scholar_pub(self, __data, publication: PublicationScholar):
        databox = __data.find('div', class_='gs_ri')
        title = databox.find('h3', class_='gs_rt')

        cid = __data.get('data-cid')
        pos = __data.get('data-rp')

        publication['bib']['gsrank'] = int(pos) + 1

        if title.find('span', class_='gs_ctu'):  # A citation
            title.span.extract()
        elif title.find('span', class_='gs_ctc'):  # A book or PDF
            title.span.extract()

        publication['bib']['title'] = title.text.strip()

        if title.find('a'):
            publication['bib']['url'] = title.find('a')['href']

        author_div_element = databox.find('div', class_='gs_a')
        authorinfo = author_div_element.text
        authorinfo = authorinfo.replace(u'\xa0', u' ')       # NBSP
        authorinfo = authorinfo.replace(u'&amp;', u'&')      # Ampersand
        publication['bib']["author"] = self._get_authorlist(authorinfo)
        authorinfo_html = author_div_element.decode_contents()
        publication['bib']["author_id"] = self._get_author_id_list(authorinfo_html)

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
            publication['bib']['venue'], publication['bib']['year'] = 'NA', 'NA'
        else:
            venueyear = venueyear[1].split(',')
            venue = 'NA'
            year = venueyear[-1].strip()
            if year.isnumeric() and len(year) == 4:
                publication['bib']['year'] = year
                if len(venueyear) >= 2:
                    venue = ','.join(venueyear[0:-1]) # everything but last
            else:
                venue = ','.join(venueyear) # everything
                publication['bib']['year'] = 'NA'
            publication['bib']['venue'] = venue

        if databox.find('div', class_='gs_rs'):
            publication['bib']['abstract'] = databox.find('div', class_='gs_rs').text
            publication['bib']['abstract'] = publication['bib']['abstract'].replace(u'\u2026', u'')
            publication['bib']['abstract'] = publication['bib']['abstract'].replace(u'\n', u' ')
            publication['bib']['abstract'] = publication['bib']['abstract'].strip()

            if publication['bib']['abstract'][0:8].lower() == 'abstract':
                publication['bib']['abstract'] = publication['bib']['abstract'][9:].strip()

        lowerlinks = databox.find('div', class_='gs_fl').find_all('a')

        publication['bib']["cites"] = 0

        for link in lowerlinks:
            if (link is not None and
                    link.get('title') is not None and
                    'Cite' == link.get('title')):
                publication['url_scholarbib'] = _BIBCITE.format(cid, pos)
                sclib = self.nav.publib.format(id=cid)
                publication['url_add_sclib'] = sclib

            if 'Cited by' in link.text:
                publication['bib']['cites'] = int(re.findall(r'\d+', link.text)[0].strip())
                publication['citedby_id'] = link['href']

        if __data.find('div', class_='gs_ggs gs_fl'):
            publication['bib']['eprint'] = __data.find(
                'div', class_='gs_ggs gs_fl').a['href']
        return publication


    def fill(self, publication):
        """Populate the Publication with information from its profile"""
        if publication['source'] == 'citations':
            url = _CITATIONPUB.format(publication['author_pub_id'])
            soup = self.nav._get_soup(url)
            publication['bib']['title'] = soup.find('div', id='gsc_vcd_title').text
            if soup.find('a', class_='gsc_vcd_title_link'):
                publication['bib']['url'] = soup.find(
                    'a', class_='gsc_vcd_title_link')['href']
            for item in soup.find_all('div', class_='gs_scl'):
                key = item.find(class_='gsc_vcd_field').text.strip().lower()
                val = item.find(class_='gsc_vcd_value')
                if key == 'authors':
                    publication['bib']['authors'] = ' and '.join(
                        [i.strip() for i in val.text.split(',')])
                elif key == 'journal':
                    publication['bib']['journal'] = val.text
                elif key == 'volume':
                    publication['bib']['volume'] = int(val.text)
                elif key == 'issue':
                    publication['bib']['number'] = int(val.text)
                elif key == 'pages':
                    publication['bib']['pages'] = val.text
                elif key == 'publisher':
                    publication['bib']['publisher'] = val.text
                elif key == 'Publication date':

                    patterns = ['YYYY/M',
                                'YYYY/MM/DD',
                                'YYYY',
                                'YYYY/M/DD',
                                'YYYY/M/D',
                                'YYYY/MM/D']
                    publication['bib']['pub_year'] = arrow.get(val.text, patterns).year
                elif key == 'description':
                    # try to find all the gsh_csp if they exist
                    abstract = val.find_all(class_='gsh_csp')
                    result = ""
                    
                    # append all gsh_csp together as there can be multiple in certain scenarios
                    for item in abstract:
                        if item.text[0:8].lower() == 'abstract':
                            result += item.text[9:].strip()
                        else:
                            result += item.text

                    if len(abstract) == 0: # if no gsh_csp were found 
                        abstract = val.find(class_='gsh_small')
                        if abstract:
                            if abstract.text[0:8].lower() == 'abstract':
                                result = abstract.text[9:].strip()
                            else:
                                result = abstract.text
                        else:
                            result = ' '.join([description_part for description_part in val])

                    publication['bib']['abstract'] = result
                elif key == 'total citations':
                    publication['bib']['cites_id'] = re.findall(
                        _SCHOLARPUBRE, val.a['href'])[0]
                    publication['citedby_id'] = _CITEDBYLINK.format(publication['bib']['cites_id'])
            # number of citation per year
            years = [int(y.text) for y in soup.find_all(class_='gsc_vcd_g_t')]
            cites = [int(c.text) for c in soup.find_all(class_='gsc_vcd_g_al')]
            publication['cites_per_year'] = dict(zip(years, cites))

            if soup.find('div', class_='gsc_vcd_title_ggi'):
                publication['bib']['eprint'] = soup.find(
                    'div', class_='gsc_vcd_title_ggi').a['href']
            publication['filled'] = True
        elif publication['source'] == 'scholar':
            bibtex_url = self._get_bibtex(publication['url_scholarbib'])
            bibtex = self.nav._get_page(bibtex_url)
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            publication['bib'].update(bibtexparser.loads(bibtex,parser).entries[-1])
            publication['filled'] = True
        return publication


    def citedby(self, publication) -> _SearchScholarIterator or list:
        """Searches Google Scholar for other articles that cite this Publication and
        returns a Publication generator.

        :getter: Returns a Generator of Publications that cited the current.
        :type: Iterator[:class:`Publication`]
        """
        if not publication['filled']:
            publication = self.fill(publication)
        return _SearchScholarIterator(self.nav, publication['citedby_id'])

    def bibtex(self, publication) -> str:
        """Returns the publication as a Bibtex entry

        :getter: Returns a Bibtex entry in text format
        :type: str
        """
        if not publication['filled']:
            publication = self.fill(publication)
        a = BibDatabase()
        converted_dict = publication['bib']
        if publication['source'] == "scholar":
            converted_dict['author_id'] = ', '.join([item for item in converted_dict['author_id'] if item is not None])
        str_dict = {key: str(value) for key, value in converted_dict.items()}
        # convert every key of the dictionary to string to be Bibtex compatible
        a.entries = [str_dict]
        return bibtexparser.dumps(a)

    def _get_bibtex(self, bib_url) -> str:
        soup = self.nav._get_soup(bib_url)
        styles = soup.find_all('a', class_='gs_citi')

        for link in styles:
            if link.string.lower() == "bibtex":
                return link.get('href')
        return ''
