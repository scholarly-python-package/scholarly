"""scholarly.py"""
import requests
from typing import Callable
from ._navigator import Navigator

_AUTHSEARCH = '/citations?hl=en&view_op=search_authors&mauthors={0}'
_KEYWORDSEARCH = '/citations?hl=en&view_op=search_authors&mauthors=label:{0}'
_PUBSEARCH = '/scholar?hl=en&q={0}'


class _Scholarly:
    """Class that manages the API for scholarly"""

    def __init__(self):
        self.__nav = Navigator()

    def set_retries(self, num_retries: int):
        """Sets the number of retries in case of errors

        :param num_retries: the number of retries
        :type num_retries: int
        """

        return self.__nav._set_retries(num_retries)

    def use_proxy(self, http: str, https: str):
        """Setups a proxy without refreshing capabilities.

        :param http: the http proxy address
        :type http: str
        :param https: the https proxy address
        :type https: str
        """

        return self.__nav._use_proxy(http, https)

    def set_proxy_generator(self, gen: Callable[..., str]):
        """Setups a function that generates new proxies on demand.

        :param gen: the function to call to obtain a new proxy
        """

        return self.__nav._set_proxy_generator(gen)

    def use_tor(self, tor_sock_port: int, tor_control_port: int, tor_pw: str):
        """[summary]

        [description]
        :param tor_sock_port: Tor sock proxy port.
        :type tor_sock_port: int
        :param tor_control_port: Tor controller port.
        :type tor_control_port: int
        :param tor_pw: Tor controller password
        :type tor_pw: str

        :Example::

            scholarly.use_tor(9050, 9051, "scholarly_password")

        """
        return self.__nav._setup_tor(tor_sock_port, tor_control_port, tor_pw)

    def launch_tor(self,
                   tor_path: str, tor_sock_port: int, tor_control_port: int):
        """
        Launches a temporary Tor connector to be used by scholarly.

        This method requires the absolute path to a Tor executable file,
        or that the executable is in the PATH.

        :param tor_path: Absolute path to the local Tor binary
        :type tor_path: str
        :param tor_sock_port: Tor sock proxy port.
        :type tor_sock_port: int
        :param tor_control_port: Tor controller port.
        :type tor_control_port: int

        :Example::

            scholarly.launch_tor('/usr/bin/tor')
        """
        return self.__nav._launch_tor(tor_path, tor_sock_port, tor_control_port)

    def search_pubs(self,
                    query: str, patents: bool = True,
                    citations: bool = True, year_low: int = None,
                    year_high: int = None):
        """Searches by query and returns a generator of Publication objects

        [description]
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
        :returns: Generator of Publication objects
        :rtype: Iterator[:class:`Publication`]

        :Example::

            .. testcode::

                search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
                print(next(search_query))

        :Output::

            .. testoutput::

                {
                    'bib':{
                            'abstract':'Humans can judge from vision alone whether an object is '
                                        'physically stable or not. Such judgments allow observers '
                                        'to predict the physical behavior of objects, and hence '
                                        'to guide their motor actions. We investigated the visual '
                                        'estimation of physical stability of 3-D objects (shown '
                                        'in stereoscopically viewed rendered scenes) and how it '
                                        'relates to visual estimates of their center of mass '
                                        '(COM). In Experiment 1, observers viewed an object near '
                                        'the edge of a table and adjusted its tilt to the '
                                        'perceived critical angle, ie, the tilt angle at which '
                                        'the object …',
                            'author': 'SA Cholewiak and RW Fleming and M Singh',
                            'eprint': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
                            'title': 'Perception of physical stability and center of mass of 3-D '
                                  'objects',
                            'url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
                            'venue': 'Journal of vision',
                            'year': ' 2015'
                    },
                    'citedby': 19,
                    'filled': False,
                    'id_scholarcitedby': '15736880631888070187',
                    'source': 'scholar',
                    'url_scholarbib': 'https://scholar.googleusercontent.com/scholar.bib?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=citation&scisdr=CgXsOAkeGAA:AAGBfm0AAAAAXsLLJNxa7vzefAEwz6a3tLCEoMsli6vj&scisig=AAGBfm0AAAAAXsLLJNK0I3FleN-7_r_TxUF8m5JDa9W5&scisf=4&ct=citation&cd=0&hl=en'
                }

        """
        url = _PUBSEARCH.format(requests.utils.quote(query))

        yr_lo = '&as_ylo={0}'.format(year_low) if year_low is not None else ''
        yr_hi = '&as_yhi={0}'.format(year_high) if year_high is not None else ''
        citations = '&as_vis={0}'.format(1 - int(citations))
        patents = '&as_sdt={0},33'.format(1 - int(patents))
        # improve str below
        url = url + yr_lo + yr_hi + citations + patents
        return self.__nav.search_publications(url)

    def search_single_pub(self, pub_title: str, filled: bool = False):
        """Search by scholar query and return a single Publication object"""
        url = _PUBSEARCH.format(requests.utils.quote(pub_title))
        return self.__nav.search_publication(url, filled)

    def search_author(self, name: str):
        """Search by author name and return a generator of Author objects

        :Example::

            .. testcode::

                search_query = scholarly.search_author('Marty Banks, Berkeley')
                print(next(search_query))

        :Output::

            .. testoutput::

                {
                    'affiliation': 'Professor of Vision Science, UC Berkeley',
                    'citedby': 20160,
                    'email': '@berkeley.edu',
                    'filled': False,
                    'id': 'Smr99uEAAAAJ',
                    'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
                    'name': 'Martin Banks',
                    'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=Smr99uEAAAAJ'
                }
        """
        url = _AUTHSEARCH.format(requests.utils.quote(name))
        return self.__nav.search_authors(url)

    def search_keyword(self, keyword: str):
        """Search by keyword and return a generator of Author objects

        :Example::

            .. testcode::

                search_query = scholarly.search_keyword('Haptics')
                print(next(search_query))

        :Output::

            .. testoutput::

                {
                    'affiliation': 'Postdoctoral research assistant, University of Bremen',
                    'citedby': 55943,
                    'email': '@collision-detection.com',
                    'filled': False,
                    'id': 'lHrs3Y4AAAAJ',
                    'interests': ['Computer Graphics',
                               'Collision Detection',
                               'Haptics',
                               'Geometric Data Structures'],
                    'name': 'Rene Weller',
                    'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=lHrs3Y4AAAAJ'
                }
        """
        url = _KEYWORDSEARCH.format(requests.utils.quote(keyword))
        return self.__nav.search_authors(url)

    def search_pubs_custom_url(self, url: str):
        """Search by custom URL and return a generator of Publication objects
        URL should be of the form '/scholar?q=...'"""
        return self.__nav.search_publications(url)

    def search_author_custom_url(self, url: str):
        """Search by custom URL and return a generator of Author objects
        URL should be of the form '/citation?q=...'"""
        return self.__nav.search_authors(url)
