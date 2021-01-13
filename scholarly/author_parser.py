from .publication_parser import PublicationParser
import re
from .data_types import Author, AuthorSource, PublicationSource

_CITATIONAUTHRE = r'user=([\w-]*)'
_HOST = 'https://scholar.google.com{0}'
_PAGESIZE = 100
_EMAILAUTHORRE = r'Verified email at '
_CITATIONAUTH = '/citations?hl=en&user={0}'


class AuthorParser:
    """Returns an object for a single author"""

    def __init__(self, nav):
        self.nav = nav
        self._sections = {'basics',
                          'indices',
                          'counts',
                          'coauthors',
                          'publications'}
    
    def get_author(self, __data)->Author:
        """ Fills the information for an author container
        """
        author: Author = {'container_type': 'Author'}
        author['filled'] = set()
        if isinstance(__data, str):
            author['scholar_id'] = __data
            author['source'] = AuthorSource.AUTHOR_PROFILE_PAGE
        else:
            author['source'] = AuthorSource.SEARCH_AUTHOR_SNIPPETS
            author['scholar_id'] = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]

            pic = '/citations?view_op=medium_photo&user={}'.format(author['scholar_id'])
            author['url_picture'] = _HOST.format(pic)

            name_class = self._find_tag_class_name(__data, 'h3', 'name')
            author['name'] = __data.find('h3', class_=name_class).text

            aff_class = self._find_tag_class_name(__data, 'div', 'aff')
            affiliation = __data.find('div', class_=aff_class)
            if affiliation:
                author['affiliation'] = affiliation.text

            email_class = self._find_tag_class_name(__data, 'div', 'eml')
            email = __data.find('div', class_=email_class)
            if email:
                author['email_domain'] = re.sub(_EMAILAUTHORRE, r'@', email.text)

            int_class = self._find_tag_class_name(__data, 'a', 'one_int')
            interests = __data.find_all('a', class_=int_class)
            author['interests'] = [i.text.strip() for i in interests]

            citedby_class = self._find_tag_class_name(__data, 'div', 'cby')
            citedby = __data.find('div', class_=citedby_class)
            if citedby and citedby.text != '':
                author['citedby'] = int(citedby.text[9:])

        return author


    def _find_tag_class_name(self, __data, tag, text):
        elements = __data.find_all(tag)
        for element in elements:
            if 'class' in element.attrs and text in element.attrs['class'][0]:
                return element.attrs['class'][0]

    def _fill_basics(self, soup, author):
        author['name'] = soup.find('div', id='gsc_prf_in').text
        if author['source'] == AuthorSource.AUTHOR_PROFILE_PAGE:
            res = soup.find('img', id='gsc_prf_pup-img')
            if res != None:
                if "avatar_scholar" not in res['src']:
                    author['url_picture'] = res['src']
        author['affiliation'] = soup.find('div', class_='gsc_prf_il').text
        author['interests'] = [i.text.strip() for i in
                          soup.find_all('a', class_='gsc_prf_inta')]
        if author['source'] == AuthorSource.AUTHOR_PROFILE_PAGE:
            email = soup.find('div', id="gsc_prf_ivh", class_="gsc_prf_il")
            if email.text != "No verified email":
                author['email_domain'] = '@'+email.text.split(" ")[3]
        if author['source'] == AuthorSource.CO_AUTHORS_LIST:
            picture = soup.find('img', id="gsc_prf_pup-img").get('src')
            if "avatar_scholar" in picture:
                picture = _HOST.format(picture)
            author['url_picture'] = picture
        
    def _fill_indices(self, soup, author):
        index = soup.find_all('td', class_='gsc_rsb_std')
        if index:
            author['citedby'] = int(index[0].text)
            author['citedby5y'] = int(index[1].text)
            author['hindex'] = int(index[2].text)
            author['hindex5y'] = int(index[3].text)
            author['i10index'] = int(index[4].text)
            author['i10index5y'] = int(index[5].text)
        else:
            author['hindex'] = 0
            author['hindex5y'] = 0
            author['i10index'] = 0
            author['i10index5y'] = 0

    def _fill_counts(self, soup, author):
        years = [int(y.text)
                 for y in soup.find_all('span', class_='gsc_g_t')]
        cites = [int(c.text)
                 for c in soup.find_all('span', class_='gsc_g_al')]
        author['cites_per_year'] = dict(zip(years, cites))

    def _fill_publications(self, soup, author):
        author['publications'] = list()
        pubstart = 0
        url_citations = _CITATIONAUTH.format(author['scholar_id'])

        pub_parser = PublicationParser(self.nav)
        while True:
            for row in soup.find_all('tr', class_='gsc_a_tr'):
                new_pub = pub_parser.get_publication(row, PublicationSource.AUTHOR_PUBLICATION_ENTRY)
                author['publications'].append(new_pub)
            if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs:
                pubstart += _PAGESIZE
                url = '{0}&cstart={1}&pagesize={2}'.format(
                    url_citations, pubstart, _PAGESIZE)
                soup = self.nav._get_soup(url)
            else:
                break

    def _fill_coauthors(self, soup, author):
        author['coauthors'] = []
        for row in soup.find_all('span', class_='gsc_rsb_a_desc'):
            new_coauthor = self.get_author(re.findall(
                _CITATIONAUTHRE, row('a')[0]['href'])[0])
            new_coauthor['name'] = row.find(tabindex="-1").text
            new_coauthor['affiliation'] = row.find(
                class_="gsc_rsb_a_ext").text
            new_coauthor['source'] = AuthorSource.CO_AUTHORS_LIST
            author['coauthors'].append(new_coauthor)

    def fill(self, author, sections: list = []):
        """Populate the Author with information from their profile

        The `sections` argument allows for finer granularity of the profile
        information to be pulled.

        :param sections: Sections of author profile to be filled, defaults to ``[]``.

            * ``basics``: fills name, affiliation, and interests;
            * ``citations``: fills h-index, i10-index, and 5-year analogues;
            * ``counts``: fills number of citations per year;
            * ``coauthors``: fills co-authors;
            * ``publications``: fills publications;
            * ``[]``: fills all of the above
        :type sections: ['basics','citations','counts','coauthors','publications',[]] list, optional
        :returns: The filled object if fill was successfull, False otherwise.
        :rtype: Author or bool

        :Example::

        .. testcode::

            search_query = scholarly.search_author('Steven A Cholewiak')
            author = next(search_query)
            scholarly.pprint(author.fill(sections=['basic', 'citation_indices', 'co-authors']))

        :Output::

        .. testoutput::

            {'affiliation': 'Vision Scientist',
             'citedby': 304,
             'citedby5y': 226,
             'coauthors': [{'affiliation': 'Kurt Koffka Professor of Experimental '
                                           'Psychology, University of Giessen',
                            'filled': False,
                            'name': 'Roland Fleming',
                            'scholar_id': 'ruUKktgAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Professor of Vision Science, UC Berkeley',
                            'filled': False,
                            'name': 'Martin Banks',
                            'scholar_id': 'Smr99uEAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Durham University, Computer Science & Physics',
                            'filled': False,
                            'name': 'Gordon D. Love',
                            'scholar_id': '3xJXtlwAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Professor of ECE, Purdue University',
                            'filled': False,
                            'name': 'Hong Z Tan',
                            'scholar_id': 'OiVOAHMAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Deepmind',
                            'filled': False,
                            'name': 'Ari Weinstein',
                            'scholar_id': 'MnUboHYAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': "Brigham and Women's Hospital/Harvard Medical "
                                           'School',
                            'filled': False,
                            'name': 'Chia-Chien Wu',
                            'scholar_id': 'dqokykoAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Professor of Psychology and Cognitive Science, '
                                           'Rutgers University',
                            'filled': False,
                            'name': 'Jacob Feldman',
                            'scholar_id': 'KoJrMIAAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Research Scientist at Google Research, PhD '
                                           'Student at UC Berkeley',
                            'filled': False,
                            'name': 'Pratul Srinivasan',
                            'scholar_id': 'aYyDsZ0AAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Formerly: Indiana University, Rutgers '
                                           'University, University of Pennsylvania',
                            'filled': False,
                            'name': 'Peter C. Pantelis',
                            'scholar_id': 'FoVvIK0AAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Professor in Computer Science, University of '
                                           'California, Berkeley',
                            'filled': False,
                            'name': 'Ren Ng',
                            'scholar_id': '6H0mhLUAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Yale University',
                            'filled': False,
                            'name': 'Steven W Zucker',
                            'scholar_id': 'rNTIQXYAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Brown University',
                            'filled': False,
                            'name': 'Ben Kunsberg',
                            'scholar_id': 'JPZWLKQAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Rutgers University, New Brunswick, NJ',
                            'filled': False,
                            'name': 'Manish Singh',
                            'scholar_id': '9XRvM88AAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Silicon Valley Professor of ECE, Purdue '
                                           'University',
                            'filled': False,
                            'name': 'David S. Ebert',
                            'scholar_id': 'fD3JviYAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Clinical Director, Neurolens Inc.,',
                            'filled': False,
                            'name': 'Vivek Labhishetty',
                            'scholar_id': 'tD7OGTQAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'MIT',
                            'filled': False,
                            'name': 'Joshua B. Tenenbaum',
                            'scholar_id': 'rRJ9wTJMUB8C',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Chief Scientist, isee AI',
                            'filled': False,
                            'name': 'Chris Baker',
                            'scholar_id': 'bTdT7hAAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Professor of Psychology, Ewha Womans '
                                           'University',
                            'filled': False,
                            'name': 'Sung-Ho Kim',
                            'scholar_id': 'KXQb7CAAAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Assistant Professor, Boston University',
                            'filled': False,
                            'name': 'Melissa M. Kibbe',
                            'scholar_id': 'NN4GKo8AAAAJ',
                            'source': 'CO_AUTHORS_LIST'},
                           {'affiliation': 'Nvidia Corporation',
                            'filled': False,
                            'name': 'Peter Shirley',
                            'scholar_id': 'nHx9IgYAAAAJ',
                            'source': 'CO_AUTHORS_LIST'}],
             'email_domain': '@berkeley.edu',
             'filled': False,
             'hindex': 9,
             'hindex5y': 9,
             'i10index': 8,
             'i10index5y': 7,
             'interests': ['Depth Cues',
                           '3D Shape',
                           'Shape from Texture & Shading',
                           'Naive Physics',
                           'Haptics'],
             'name': 'Steven A. Cholewiak, PhD',
             'scholar_id': '4bahYMkAAAAJ',
             'source': 'SEARCH_AUTHOR_SNIPPETS',
             'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=4bahYMkAAAAJ'}
        """
        try:
            sections = [section.lower() for section in sections]
            url_citations = _CITATIONAUTH.format(author['scholar_id'])
            url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
            soup = self.nav._get_soup(url)

            if sections == []:
                for i in self._sections:
                    if i not in author['filled']:
                        getattr(self, f'_fill_{i}')(soup, author)
                        author['filled'].add(i)
            else:
                for i in sections:
                    if i in self._sections and i not in author['filled']:
                        getattr(self, f'_fill_{i}')(soup, author)
                        author['filled'].add(i)
        except Exception as e:
            raise(e)

        return author


    def __repr__(self):
        return self.__str__()
