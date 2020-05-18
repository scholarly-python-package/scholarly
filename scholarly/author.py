from .publication import Publication
import re 
import pprint


_CITATIONAUTHRE = r'user=([\w-]*)'
_HOST = 'https://scholar.google.com{0}'
_PAGESIZE = 100
_EMAILAUTHORRE = r'Verified email at '
_CITATIONAUTH = '/citations?hl=en&user={0}'


class Author(object):
    """Returns an object for a single author"""

    def _find_tag_class_name(self, __data, tag, text):
        elements = __data.find_all(tag)
        for element in elements:
            if 'class' in element.attrs and text in element.attrs['class'][0]:
                return element.attrs['class'][0]

    def __init__(self, nav, __data):
        self.nav = nav
        if isinstance(__data, str):
            self.id = __data
        else:
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
            self.url_picture = _HOST + \
                '/citations?view_op=medium_photo&user={}'.format(self.id)
            self.name = __data.find(
                'h3', class_=self._find_tag_class_name(__data, 'h3', 'name')).text
            affiliation = __data.find(
                'div', class_=self._find_tag_class_name(__data, 'div', 'aff'))
            if affiliation:
                self.affiliation = affiliation.text
            email = __data.find(
                'div', class_=self._find_tag_class_name(__data, 'div', 'eml'))
            if email:
                self.email = re.sub(_EMAILAUTHORRE, r'@', email.text)
            self.interests = [i.text.strip() for i in
                              __data.find_all('a', class_=self._find_tag_class_name(__data, 'a', 'one_int'))]
            citedby = __data.find(
                'div', class_=self._find_tag_class_name(__data, 'div', 'cby'))
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

    def fill(self, sections:list=['all']):
        """Populate the Author with information from their profile

        The `sections` argument allows for finer granularity of the profile
        information to be pulled.

        :param sections: The sections of author information that will be filled.
        They are broken down as follows:
            'basic' = name, affiliation, and interests;
            'citation_indices' = h-index, i10-index, and 5-year analogues;
            'citation_num' = number of citations per year;
            'co-authors' = co-authors;
            'publications' = publications;
            'all' = all of the above, defaults to ['all']
        :type sections: list, optional
        :returns: [description]
        :rtype: {Author}
        """

        sections = [section.lower() for section in sections]
        url_citations = _CITATIONAUTH.format(self.id)
        url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
        soup = self.nav._get_soup(url)

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
                new_coauthor = Author(self.nav, re.findall(
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
                    new_pub = Publication(self.nav, row, 'citations')
                    self.publications.append(new_pub)
                if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs:
                    pubstart += _PAGESIZE
                    url = '{0}&cstart={1}&pagesize={2}'.format(
                        url_citations, pubstart, _PAGESIZE)
                    soup = self.nav._get_soup(url)
                else:
                    break

        if 'all' in sections or set(sections) == set(self.sections.values()):
            self._filled = True

        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)

    def __repr__(self):
        return pprint.pformat(self.__dict__)
