"""scholarly.py"""
import requests
import random
import os
import copy
import pprint
from typing import Callable
from ._navigator import Navigator
from ._proxy_generator import ProxyGenerator
from dotenv import find_dotenv, load_dotenv
from .author_parser import AuthorParser
from .publication_parser import PublicationParser, _SearchScholarIterator
from .data_types import Author, AuthorSource, Publication, PublicationSource

_AUTHSEARCH = '/citations?hl=en&view_op=search_authors&mauthors={0}'
_KEYWORDSEARCH = '/citations?hl=en&view_op=search_authors&mauthors=label:{0}'
_PUBSEARCH = '/scholar?hl=en&q={0}'


class _Scholarly:
    """Class that manages the API for scholarly"""

    def __init__(self):
        load_dotenv(find_dotenv())
        self.env = os.environ.copy()
        self.__nav = Navigator()

    def set_retries(self, num_retries: int)->None:
        """Sets the number of retries in case of errors

        :param num_retries: the number of retries
        :type num_retries: int
        """

        return self.__nav._set_retries(num_retries)


    def use_proxy(self, proxy_generator: ProxyGenerator)->None:
        """Select which proxy method to use.
        See the available ProxyGenerator methods.

        :param proxy_generator: proxy generator objects
        :type proxy_generator: ProxyGenerator
        """
        self.__nav.use_proxy(proxy_generator)


    def set_logger(self, enable: bool):
        """Enable or disable the logger for google scholar. 
        Enabled by default
        """
        self.__nav.set_logger(enable)

    def set_timeout(self, timeout: int):
        """Set timeout period in seconds for scholarly"""
        self.__nav.set_timeout(timeout)


    def search_pubs(self,
                    query: str, patents: bool = True,
                    citations: bool = True, year_low: int = None,
                    year_high: int = None, sort_by: str = "relevance",
                    include_last_year: str = "abstracts")->_SearchScholarIterator:
        """Searches by query and returns a generator of Publication objects

        :param query: terms to be searched
        :type query: str
        :param patents: Whether or not to include patents, defaults to True
        :type patents: bool, optional
        :param citations: Whether or not to include citations, defaults to True
        :type citations: bool, optional
        :param year_low: minimum year of publication, defaults to None
        :type year_low: int, optional
        :param year_high: maximum year of publication, defaults to None
        :type year_high: int, optional
        :param sort_by: 'relevance' or 'date', defaults to 'relevance'
        :type sort_by: string, optional
        :param include_last_year: 'abstracts' or 'everything', defaults to 'abstracts' and only applies if 'sort_by' is 'date'
        :type include_last_year: string, optional
        :returns: Generator of Publication objects
        :rtype: Iterator[:class:`Publication`]

        :Example::

        .. testcode::

            search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
            scholarly.pprint(next(search_query)) # in order to pretty print the result

        :Output::

        .. testoutput::

            {'author_id': ['4bahYMkAAAAJ', 'ruUKktgAAAAJ', ''],
             'bib': {'abstract': 'Humans can judge from vision alone whether an object is '
                                 'physically stable or not. Such judgments allow observers '
                                 'to predict the physical behavior of objects, and hence '
                                 'to guide their motor actions. We investigated the visual '
                                 'estimation of physical stability of 3-D objects (shown '
                                 'in stereoscopically viewed rendered scenes) and how it '
                                 'relates to visual estimates of their center of mass '
                                 '(COM). In Experiment 1, observers viewed an object near '
                                 'the edge of a table and adjusted its tilt to the '
                                 'perceived critical angle, ie, the tilt angle at which '
                                 'the object',
                     'author': ['SA Cholewiak', 'RW Fleming', 'M Singh'],
                     'pub_year': '2015',
                     'title': 'Perception of physical stability and center of mass of 3-D '
                              'objects',
                     'venue': 'Journal of vision'},
             'citedby_url': '/scholar?cites=15736880631888070187&as_sdt=5,33&sciodt=0,33&hl=en',
             'eprint_url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
             'filled': False,
             'gsrank': 1,
             'num_citations': 23,
             'pub_url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
             'source': 'PUBLICATION_SEARCH_SNIPPET',
             'url_add_sclib': '/citations?hl=en&xsrf=&continue=/scholar%3Fq%3DPerception%2Bof%2Bphysical%2Bstability%2Band%2Bcenter%2Bof%2Bmass%2Bof%2B3D%2Bobjects%26hl%3Den%26as_sdt%3D0,33&citilm=1&json=&update_op=library_add&info=K8ZpoI6hZNoJ&ei=QhqhX66wKoyNy9YPociEuA0',
             'url_scholarbib': '/scholar?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=cite&scirp=0&hl=en'}

        """
        url = _PUBSEARCH.format(requests.utils.quote(query))

        yr_lo = '&as_ylo={0}'.format(year_low) if year_low is not None else ''
        yr_hi = '&as_yhi={0}'.format(year_high) if year_high is not None else ''
        citations = '&as_vis={0}'.format(1 - int(citations))
        patents = '&as_sdt={0},33'.format(1 - int(patents))
        sortby = ''

        if sort_by == "date":
            if include_last_year == "abstracts":
                sortby = '&scisbd=1'
            elif include_last_year == "everything":
                sortby = '&scisbd=2'
            else:
                print("Invalid option for 'include_last_year', available options: 'everything', 'abstracts'")
                return
        elif sort_by != "relevance":
            print("Invalid option for 'sort_by', available options: 'relevance', 'date'")
            return
            
        # improve str below
        url = url + yr_lo + yr_hi + citations + patents + sortby
        return self.__nav.search_publications(url)

    def search_single_pub(self, pub_title: str, filled: bool = False)->PublicationParser:
        """Search by scholar query and return a single Publication container object
        
        :param pub_title: Title of the publication to search
        :type pub_title: string
        :param filled: Whether the application should be filled with additional information
        :type filled: bool
        """
        url = _PUBSEARCH.format(requests.utils.quote(pub_title))
        return self.__nav.search_publication(url, filled)

    def search_author(self, name: str):
        """Search by author name and return a generator of Author objects

        :Example::

            .. testcode::

                search_query = scholarly.search_author('Marty Banks, Berkeley')
                scholarly.pprint(next(search_query))

        :Output::

        .. testoutput::

            {'affiliation': 'Professor of Vision Science, UC Berkeley',
             'citedby': 21074,
             'email_domain': '@berkeley.edu',
             'filled': False,
             'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
             'name': 'Martin Banks',
             'scholar_id': 'Smr99uEAAAAJ',
             'source': 'SEARCH_AUTHOR_SNIPPETS',
             'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=Smr99uEAAAAJ'}
        """
        url = _AUTHSEARCH.format(requests.utils.quote(name))
        return self.__nav.search_authors(url)
    
    def fill(self, object: dict, sections=[]) -> Author or Publication:
        """Fills the object according to its type.
        If the container type is Author it will fill the additional author fields
        If it is Publication it will fill it accordingly.
        
        :param object: the Author or Publication object that needs to get filled
        :type object: Author or Publication
        :param sections: the sections that the user wants filled for an Author object. This can be: ['basics', 'indices', 'counts', 'coauthors', 'publications']
        :type sections: list
        """

        if object['container_type'] == "Author":
            author_parser = AuthorParser(self.__nav)
            object = author_parser.fill(object, sections)
            if object is False:
                raise ValueError("Incorrect input")
        elif object['container_type'] == "Publication":
            publication_parser = PublicationParser(self.__nav)
            object = publication_parser.fill(object)
        return object

    def bibtex(self, object: Publication)->str:
        """Returns a bibtex entry for a publication that has either Scholar source
        or citation source
        
        :param object: The Publication object for the bibtex exportation
        :type object: Publication
        """
        if object['container_type'] == "Publication":
           publication_parser = PublicationParser(self.__nav) 
           return publication_parser.bibtex(object)
        else:
            print("Object not supported for bibtex exportation")
            return

    def citedby(self, object: Publication)->_SearchScholarIterator:
        """Searches Google Scholar for other articles that cite this Publication
        and returns a Publication generator.

        :param object: The Publication object for the bibtex exportation
        :type object: Publication
        """
        if object['container_type'] == "Publication":
           publication_parser = PublicationParser(self.__nav) 
           return publication_parser.citedby(object)
        else:
            print("Object not supported for bibtex exportation")
            return


    def search_author_id(self, id: str, filled: bool = False)->Author:
        """Search by author id and return a single Author object

        :Example::

            .. testcode::

                search_query = scholarly.search_author_id('EmD_lTEAAAAJ')
                scholarly.pprint(search_query)

        :Output::

            .. testoutput::

                {'affiliation': 'Institut du radium, University of Paris',
                 'filled': False,
                 'interests': [],
                 'name': 'Marie Skłodowska-Curie',
                 'scholar_id': 'EmD_lTEAAAAJ',
                 'source': 'AUTHOR_PROFILE_PAGE'}
        """
        return self.__nav.search_author_id(id, filled)

    def search_keyword(self, keyword: str):
        """Search by keyword and return a generator of Author objects
        
        :param keyword: keyword to be searched
        :type keyword: str

        :Example::

        .. testcode::

            search_query = scholarly.search_keyword('Haptics')
            scholarly.pprint(next(search_query))

        :Output::

        .. testoutput::

            {'affiliation': 'Postdoctoral research assistant, University of Bremen',
             'citedby': 56666,
             'email_domain': '@collision-detection.com',
             'filled': False,
             'interests': ['Computer Graphics',
                           'Collision Detection',
                           'Haptics',
                           'Geometric Data Structures'],
             'name': 'Rene Weller',
             'scholar_id': 'lHrs3Y4AAAAJ',
             'source': 'SEARCH_AUTHOR_SNIPPETS',
             'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=lHrs3Y4AAAAJ'}
        """
        url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
        return self.__nav.search_authors(url)

    def search_pubs_custom_url(self, url: str)->_SearchScholarIterator:
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'

        :param url: custom url to seach for the publication
        :type url: string
        """
        return self.__nav.search_publications(url)

    def search_author_custom_url(self, url: str)->Author:
        """Search by custom URL and return a generator of Author objects
        URL should be of the form '/citation?q=...'

        :param url: url for the custom author url
        :type url: string
        """
        return self.__nav.search_authors(url)

    def pprint(self, object: Author or Publication)->None:
        """Pretty print an Author or Publication container object
        
        :param object: Publication or Author container object
        :type object: Author or Publication
        """
        if 'container_type' not in object:
            print("Not a scholarly container object")
            return

        to_print = copy.deepcopy(object)
        if to_print['container_type'] == 'Publication':
            to_print['source'] = PublicationSource(to_print['source']).name
        elif to_print['container_type'] == 'Author':
            parser = AuthorParser(self.__nav)
            to_print['source'] = AuthorSource(to_print['source']).name
            if parser._sections == to_print['filled']:
                to_print['filled'] = True
            else:
                to_print['filled'] = False
            
            if 'coauthors' in to_print:
                for coauthor in to_print['coauthors']:
                    coauthor['filled'] = False
                    del coauthor['container_type']
                    coauthor['source'] = AuthorSource(coauthor['source']).name

            if 'publications' in to_print:
                for publication in to_print['publications']:
                    publication['source'] = PublicationSource(publication['source']).name
                    del publication['container_type']

        del to_print['container_type']
        print(pprint.pformat(to_print))

    def search_org(self, name: str, fromauthor: bool = False) -> list:
        """Search by organization name and return a list of possible disambiguations
        :Example::
            .. testcode::
                search_query = scholarly.search_org('ucla')
                print(search_query)
        :Output::
            .. testoutput::
                [{'Organization': 'University of California, Los Angeles',
                  'id': '14108176128635076915'},
                 {'Organization': 'Universidad Centroccidental Lisandro Alvarado',
                  'id': '9670678584336165373'}
                ]
        """

        url = _AUTHSEARCH.format(requests.utils.quote(name))
        return self.__nav.search_organization(url, fromauthor)
