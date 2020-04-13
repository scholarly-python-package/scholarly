import re
import pprint
if __name__ == '__main__':
    from confs import *
else:
    from .confs import *
import hashlib
import random

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}

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
            self.bib['author'] = self.get_authorlist(authorinfo)
            if databox.find('div', class_='gs_rs'):
                self.bib['abstract'] = databox.find('div', class_='gs_rs').text
                if self.bib['abstract'][0:8].lower() == 'abstract':
                    self.bib['abstract'] = self.bib['abstract'][9:].strip()
            lowerlinks = databox.find('div', class_='gs_fl').find_all('a')
            for link in lowerlinks:
                # if (link is not None and 
                #     link.get('title') is not None and
                #     'Cite' in link.get('title')):
                    
                #     self.url_scholarbib = link.get('href')
                if 'Cited by' in link.text:
                    self.bib['cites'] = int(re.findall(r'\d+', link.text)[0])
                    self.bib['citesurl'] = re.findall(_SCHOLARPUBRE, link['href'])[0]
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
            #bibtex = self._scholarly._get_page(self.url_scholarbib)
            #self.bib.update(bibtexparser.loads(bibtex).entries[0])
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