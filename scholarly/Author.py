import re
import pprint
import hashlib
import random


class Author(object):
    """Returns an object for a single author"""

    def __init__(self, __data, scholarly):
        self._scholarly = scholarly
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
            topics = __data.find_all('a',
                                     class_=_find_tag_class_name(__data,
                                                                 'a',
                                                                 'one_int'))
            self.interests = [i.text.strip() for i in topics]
            citedby = __data.find(
                'div', class_=_find_tag_class_name(__data, 'div', 'cby'))
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
        self.interests = [i.text.strip()
                          for i in soup.find_all('a', class_='gsc_prf_inta')]

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
                re.findall(_CITATIONAUTHRE,
                           row('a')[0]['href'])[0],
                self._scholarly)
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
                url = '{0}&cstart={1}&pagesize={2}'.format(
                    url_citations, pubstart, _PAGESIZE)
                soup = _get_soup(_HOST+url)
            else:
                break

        self._filled = True
        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)
