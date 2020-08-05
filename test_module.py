import unittest
import argparse
import os
import sys
from scholarly import scholarly, proxy_generator
import random
from fp.fp import FreeProxy

# def set_new_proxy():
#     while True:
#         proxy = FreeProxy(rand=True, timeout=1).get()
#         proxy_works = scholarly.use_proxy(http=proxy, https=proxy)
#         if proxy_works:
#             break
#     return proxy    

class TestScholarly(unittest.TestCase):

    def setUp(self):
        if "CONNECTION_METHOD" in scholarly.env:
            self.connection_method = os.getenv("CONNECTION_METHOD")
        else:
            self.connection_method = "none"
        if self.connection_method == "tor":
            tor_sock_port = None
            tor_control_port = None
            tor_password = "scholarly_password"
            # Tor uses the 9050 port as the default socks port 
            # on windows 9150 for socks and 9151 for control 
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                tor_sock_port = 9050
                tor_control_port = 9051
            elif sys.platform.startswith("win"):
                tor_sock_port = 9150
                tor_control_port = 9151
            proxy_generator.Tor_External(tor_sock_port,tor_control_port,tor_password)
            scholarly.use_proxy(proxy_generator)

        elif self.connection_method == "tor_internal":
            if sys.platform.startswith("linux"):
                tor_cmd = 'tor'
            elif sys.platform.startswith("win"):
                tor_cmd = 'tor.exe'
            proxy_generator.Tor_Internal(tor_cmd = tor_cmd)
            scholarly.use_proxy(proxy_generator)
        elif self.connection_method == "luminaty":
            proxy_generator.Luminati()
            scholarly.use_proxy(proxy_generator)
        elif self.connection_method == "freeproxy":
            proxy_generator.FreeProxies()
            scholarly.use_proxy(proxy_generator)
        else:
            scholarly.use_proxy(None)

    def test_tor_launch_own_process(self):
        """
        Test that we can launch a Tor process
        """
        if self.connection_method != "tor":
            return

        if sys.platform.startswith("linux"):
            tor_cmd = 'tor'
        elif sys.platform.startswith("win"):
            tor_cmd = 'tor.exe'

        tor_sock_port = random.randrange(9000, 9500)
        tor_control_port = random.randrange(9500, 9999)

        result = proxy_generator.Tor_Internal(tor_cmd, tor_sock_port, tor_control_port)
        self.assertTrue(result["proxy_works"])
        self.assertTrue(result["refresh_works"])
        self.assertEqual(result["tor_control_port"], tor_control_port)
        self.assertEqual(result["tor_sock_port"], tor_sock_port)
        # Check that we can issue a query as well
        query = 'Ipeirotis'
        scholarly.use_proxy(proxy_generator)
        authors = [a for a in scholarly.search_author(query)]
        self.assertGreaterEqual(len(authors), 1)


    def test_search_author_empty_author(self):
        """
        Test that sholarly.search_author('') returns no authors
        """
        authors = [a for a in scholarly.search_author('')]
        self.assertIs(len(authors), 0)

    def test_search_keyword_empty_keyword(self):
        """
        As of 2020-04-30, there are  6 individuals that match the name 'label'
        """
        # TODO this seems like undesirable functionality for
        # scholarly.search_keyword() with empty string. Surely, no authors
        # should be returned. Consider modifying the method itself.
        authors = [a for a in scholarly.search_keyword('')]
        self.assertGreaterEqual(len(authors), 6)

    def test_search_pubs_empty_publication(self):
        """
        Test that searching for an empty publication returns zero results
        """
        pubs = [p for p in scholarly.search_pubs('')]
        self.assertIs(len(pubs), 0)

    
    def test_search_author_filling_author_publications(self):
         """
         Download a few publications for author and check that abstracts are
         populated with lengths within the expected limits. This process
         checks the process of filling a publication that is derived
         from the author profile page.
         """
         query = 'Ipeirotis'
         authors = [a for a in scholarly.search_author(query)]
         self.assertGreaterEqual(len(authors), 1)
         author = authors[0].fill()
         # Check that we can fill without problem the first two publications
         publications = author.publications[:2]
         for i in publications:
             i.fill()
         self.assertEqual(len(publications), 2)
         abstracts_populated = ['abstract' in p.bib.keys() for p in publications]
         # Check that all publications have the abstract field populated
         self.assertTrue(all(abstracts_populated))
         # Check that the abstracts have reasonable lengths
         abstracts_length = [len(p.bib['abstract']) for p in publications]
         abstracts_check = [1000 > n > 500 for n in abstracts_length]
         self.assertTrue(all(abstracts_check))

    def test_search_pubs_citedby(self):
        """
        Testing that when we retrieve the list of publications that cite
        a publication, the number of citing publication is the same as
        the number of papers that are returned. We use a publication
        with a small number of citations, so that the test runs quickly.
        The 'Machine-learned epidemiology' paper had 11 citations as of
        June 1, 2020.
        """
        query = 'Machine-learned epidemiology: real-time detection of foodborne illness at scale'
        pubs = [p for p in scholarly.search_pubs(query)]
        self.assertGreaterEqual(len(pubs), 1)
        filled = pubs[0].fill()
        cites = [c for c in filled.citedby]
        self.assertEqual(str(len(cites)), filled.bib['cites'])

    def test_search_keyword(self):
        """
        When we search for the keyword "3d_shape" the author
        Steven A. Cholewiak should be among those listed
        """
        authors = [a.name for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak, PhD', authors)

    def test_search_author_single_author(self):
        query = 'Steven A. Cholewiak'
        authors = [a for a in scholarly.search_author(query)]
        self.assertGreaterEqual(len(authors), 1)
        author = authors[0].fill()
        self.assertEqual(author.name, u'Steven A. Cholewiak, PhD')
        self.assertEqual(author.id, u'4bahYMkAAAAJ')        
        pub = author.publications[2].fill()
        self.assertEqual(pub.id_citations,u'4bahYMkAAAAJ:ufrVoPGSRksC')

    def test_search_author_multiple_authors(self):
        """
        As of May 12, 2020 there are at least 24 'Cattanis's listed as authors
        and Giordano Cattani is one of them
        """
        authors = [a.name for a in scholarly.search_author('cattani')]
        self.assertGreaterEqual(len(authors), 24)
        self.assertIn(u'Giordano Cattani', authors)

    def test_search_author_id(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permenant
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ')
        self.assertEqual(author.name, u'Marie Skłodowska-Curie')
        self.assertEqual(author.affiliation,
                         u'Institut du radium, University of Paris')

    def test_search_author_id_filled(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permenant.
        As of July 2020, Marie Skłodowska-Curie has 1963 citations
        on Google Scholar and 179 publications
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ', filled=True)
        self.assertEqual(author.name, u'Marie Skłodowska-Curie')
        self.assertEqual(author.affiliation,
                         u'Institut du radium, University of Paris')
        self.assertGreaterEqual(author.citedby, 1963)
        self.assertGreaterEqual(len(author.publications), 179)

    def test_search_pubs(self):
        """
        As of May 12, 2020 there are at least 29 pubs that fit the search term:
        ["naive physics" stability "3d shape"].

        Check that the paper "Visual perception of the physical stability of asymmetric three-dimensional objects"
        is among them
        """
        pubs = [p.bib['title'] for p in scholarly.search_pubs(
            '"naive physics" stability "3d shape"')]
        self.assertGreaterEqual(len(pubs), 27)

        self.assertIn('Visual perception of the physical stability of asymmetric three-dimensional objects', pubs)

    def test_search_pubs_filling_publication_contents(self):
        '''
        This process  checks the process of filling a publication that is derived
         from the search publication snippets.
        '''
        query = 'Creating correct blur and its effect on accommodation'
        results = scholarly.search_pubs(query)
        pubs = [p for p in results]
        self.assertGreaterEqual(len(pubs), 1)
        f = pubs[0].fill()
        self.assertTrue(f.bib['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S')
        self.assertTrue(f.bib['journal'] == u'Journal of vision')
        self.assertTrue(f.bib['number'] == u'9')
        self.assertTrue(f.bib['pages'] == u'1--1')
        self.assertTrue(f.bib['publisher'] == u'The Association for Research in Vision and Ophthalmology')
        self.assertTrue(f.bib['title'] == u'Creating correct blur and its effect on accommodation')
        self.assertTrue(f.bib['url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817')
        self.assertTrue(f.bib['volume'] == u'18')
        self.assertTrue(f.bib['year'] == u'2018')




if __name__ == '__main__':
    unittest.main()
