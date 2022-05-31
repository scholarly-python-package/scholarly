from .publication_parser import PublicationParser
import re
from .data_types import Author, AuthorSource, PublicationSource, PublicAccess
import codecs

_CITATIONAUTHRE = r'user=([\w-]*)'
_HOST = 'https://scholar.google.com{0}'
_PAGESIZE = 100
_EMAILAUTHORRE = r'Verified email at '
_CITATIONAUTH = '/citations?hl=en&user={0}'
_COAUTH = '/citations?view_op=list_colleagues&hl=en&user={0}'
_MANDATES = "/citations?hl=en&tzom=300&user={0}&view_op=list_mandates&pagesize={1}"


class AuthorParser:
    """Returns an object for a single author"""

    def __init__(self, nav):
        self.nav = nav
        self._sections = ['basics',
                          'indices',
                          'counts',
                          'coauthors',
                          'publications',
                          'public_access']

    def get_author(self, __data)->Author:
        """ Fills the information for an author container
        """
        author: Author = {'container_type': 'Author'}
        author['filled'] = []
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
            if int_class:
                interests = __data.find_all('a', class_=int_class)
                author['interests'] = [i.text.strip() for i in interests]
            else:
                author['interests'] = []

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
            if res is not None:
                if "avatar_scholar" not in res['src']:
                    author['url_picture'] = res['src']
        elif author['source'] == AuthorSource.CO_AUTHORS_LIST:
            picture = soup.find('img', id="gsc_prf_pup-img").get('src')
            if "avatar_scholar" in picture:
                picture = _HOST.format(picture)
            author['url_picture'] = picture

        affiliation = soup.find('div', class_='gsc_prf_il')
        author['affiliation'] = affiliation.text
        affiliation_link = affiliation.find('a')
        if affiliation_link:
            author['organization'] = int(affiliation_link.get('href').split("org=")[-1])
        author['interests'] = [i.text.strip() for i in
                          soup.find_all('a', class_='gsc_prf_inta')]
        email = soup.find('div', id="gsc_prf_ivh", class_="gsc_prf_il")
        if author['source'] == AuthorSource.AUTHOR_PROFILE_PAGE:
            if email.text != "No verified email":
                author['email_domain'] = '@'+email.text.split(" ")[3]
        homepage = email.find('a', class_="gsc_prf_ila")
        if homepage:
            author['homepage'] = homepage.get('href')

        index = soup.find_all('td', class_='gsc_rsb_std')
        if index:
            author['citedby'] = int(index[0].text)

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

    def _fill_public_access(self, soup, author):
        available = soup.find('div', class_='gsc_rsb_m_a')
        not_available = soup.find('div', class_='gsc_rsb_m_na')
        n_available, n_not_available = 0, 0
        if available:
            n_available = int(re.sub("[.,]", "", available.text.split(" ")[0]))
        if not_available:
            n_not_available = int(re.sub("[.,]", "", not_available.text.split(" ")[0]))

        author["public_access"] = PublicAccess(available=n_available,
                                               not_available=n_not_available)

        if 'publications' not in author['filled']:
            return

        # Make a dictionary mapping to the publications
        publications = {pub['author_pub_id']:pub for pub in author['publications']}
        soup = self.nav._get_soup(_MANDATES.format(author['scholar_id'], _PAGESIZE))
        while True:
            rows = soup.find_all('div', 'gsc_mnd_sec_na')
            if rows:
                for row in rows[0].find_all('a', 'gsc_mnd_art_rvw gs_nph gsc_mnd_link_font'):
                    author_pub_id = re.findall(r"citation_for_view=([\w:-]*)",
                                               row['data-href'])[0]
                    publications[author_pub_id]["public_access"] = False

            rows = soup.find_all('div', 'gsc_mnd_sec_avl')
            if rows:
                for row in rows[0].find_all('a', 'gsc_mnd_art_rvw gs_nph gsc_mnd_link_font'):
                    author_pub_id = re.findall(r"citation_for_view=([\w:-]*)",
                                               row['data-href'])[0]
                    publications[author_pub_id]["public_access"] = True

            next_button = soup.find(class_="gs_btnPR")
            if next_button and "disabled" not in next_button.attrs:
                url = next_button['onclick'][17:-1]
                url = codecs.getdecoder("unicode_escape")(url)[0]
                soup = self.nav._get_soup(url)
            else:
                break


    def _fill_publications(self, soup, author, publication_limit: int = 0, sortby_str: str = ''):
        author['publications'] = list()
        pubstart = 0
        url_citations = _CITATIONAUTH.format(author['scholar_id'])
        url_citations += sortby_str

        pub_parser = PublicationParser(self.nav)
        flag = False
        while True:
            for row in soup.find_all('tr', class_='gsc_a_tr'):
                new_pub = pub_parser.get_publication(row, PublicationSource.AUTHOR_PUBLICATION_ENTRY)
                author['publications'].append(new_pub)
                if (publication_limit) and (len(author['publications']) >= publication_limit):
                    flag = True
                    break
            if 'disabled' not in soup.find('button', id='gsc_bpf_more').attrs and not flag:
                pubstart += _PAGESIZE
                url = '{0}&cstart={1}&pagesize={2}'.format(
                    url_citations, pubstart, _PAGESIZE)
                soup = self.nav._get_soup(url)
            else:
                break

    def _get_coauthors_short(self, soup):
        """Get the short list of coauthors from the profile page.

        This method fetches the list of coauthors visible from an author's
        prilfe page alone. This may or may not be the complete list of
        coauthors.

        Note:
        -----
        This method is to be called by _fill_coauthors method.
        """
        coauthors = soup.find_all('span', class_='gsc_rsb_a_desc')
        coauthor_ids = [re.findall(_CITATIONAUTHRE,
                        coauth('a')[0].get('href'))[0]
                        for coauth in coauthors]

        coauthor_names = [coauth.find(tabindex="-1").text
                          for coauth in coauthors]
        coauthor_affils = [coauth.find(class_="gsc_rsb_a_ext").text
                           for coauth in coauthors]

        return coauthor_ids, coauthor_names, coauthor_affils

    def _get_coauthors_long(self, author):
        """Get the long (>20) list of coauthors.

        This method fetches the complete list of coauthors bu opening a new
        page filled with the complete coauthor list.

        Note:
        -----
        This method is to be called by _fill_coauthors method.
        """
        soup = self.nav._get_soup(_COAUTH.format(author['scholar_id']))
        coauthors = soup.find_all('div', 'gs_ai gs_scl')
        coauthor_ids = [re.findall(_CITATIONAUTHRE,
                        coauth('a')[0].get('href'))[0]
                        for coauth in coauthors]

        coauthor_names = [coauth.find(class_="gs_ai_name").text for coauth in coauthors]
        coauthor_affils = [coauth.find(class_="gs_ai_aff").text
                           for coauth in coauthors]

        return coauthor_ids, coauthor_names, coauthor_affils

    def _fill_coauthors(self, soup, author):
        # If "View All" is not found, scrape the page for coauthors
        if not soup.find_all('button', id='gsc_coauth_opn'):
            coauthor_info = self._get_coauthors_short(soup)
        else:
        # If "View All" is found, try opening the dialog box.
        # If geckodriver is not installed, resort to a short list and warn.
            try:
                coauthor_info = self._get_coauthors_long(author)
            except Exception as err:
                coauthor_info = self._get_coauthors_short(soup)
                self.nav.logger.warning(err)
                self.nav.logger.warning("Fetching only the top 20 coauthors")

        author['coauthors'] = []
        for coauth_id, coauth_name, coauth_affil in zip(*coauthor_info):
            new_coauthor = self.get_author(coauth_id)
            new_coauthor['name'] = coauth_name
            new_coauthor['affiliation'] = coauth_affil
            new_coauthor['source'] = AuthorSource.CO_AUTHORS_LIST
            author['coauthors'].append(new_coauthor)

    def fill(self, author, sections: list = [], sortby="citedby", publication_limit: int = 0):
        """Populate the Author with information from their profile

        The `sections` argument allows for finer granularity of the profile
        information to be pulled.

        :param sections: Sections of author profile to be filled, defaults to ``[]``.

            * ``basics``: fills name, affiliation, and interests;
            * ``citations``: fills h-index, i10-index, and 5-year analogues;
            * ``counts``: fills number of citations per year;
            * ``public_access``: fills number of articles with public access mandates;
            * ``coauthors``: fills co-authors;
            * ``publications``: fills publications;
            * ``[]``: fills all of the above
        :type sections: ['basics','citations','counts','public_access','coauthors','publications',[]] list, optional
        :param sortby: Select the order of the citations in the author page. Either by 'citedby' or 'year'. Defaults to 'citedby'.
        :type sortby: string
        :param publication_limit: Select the max number of publications you want you want to fill for the author. Defaults to no limit.
        :type publication_limit: int
        :returns: The filled object if fill was successfull, False otherwise.
        :rtype: Author or bool

        :Example::

        .. testcode::

            search_query = scholarly.search_author('Steven A Cholewiak')
            author = next(search_query)
            author = scholarly.fill(author, sections=['basics', 'citations', 'coauthors'])
            scholarly.pprint(author)

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
             'homepage': 'http://steven.cholewiak.com/',
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
            sections.sort(reverse=True)  # Ensure 'publications' comes before 'public_access'
            sortby_str = ''
            if sortby == "year":
                sortby_str = '&view_op=list_works&sortby=pubdate'
            elif sortby != "citedby":
                raise Exception("Please enter a valid sortby parameter. Options: 'year', 'citedby'")
            url_citations = _CITATIONAUTH.format(author['scholar_id'])
            url_citations += sortby_str
            url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
            soup = self.nav._get_soup(url)

            if sections == []:
                for i in self._sections:
                    if i not in author['filled']:
                        (getattr(self, f'_fill_{i}')(soup, author) if i != 'publications' else getattr(self, f'_fill_{i}')(soup, author, publication_limit, sortby_str))
                        author['filled'].append(i)
            else:
                for i in sections:
                    if i in self._sections and i not in author['filled']:
                        (getattr(self, f'_fill_{i}')(soup, author) if i != 'publications' else getattr(self, f'_fill_{i}')(soup, author, publication_limit, sortby_str))
                        author['filled'].append(i)
        except Exception as e:
            raise(e)

        return author


    def __repr__(self):
        return self.__str__()
