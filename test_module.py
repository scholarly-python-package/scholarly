import unittest
import sys
from scholarly import scholarly
import random


class TestScholarly(unittest.TestCase):

    def setUp(self):
        tor_sock_port = None
        tor_control_port = None
        tor_password = "scholarly_password"

        # Tor uses the 9050 port as the default socks port
        # on windows 9150 for socks and 9151 for control
        if sys.platform.startswith("linux"):
            tor_sock_port = 9050
            tor_control_port = 9051
        elif sys.platform.startswith("win"):
            tor_sock_port = 9150
            tor_control_port = 9151
        scholarly.use_tor(tor_sock_port, tor_control_port, tor_password)


    def test_launch_tor(self):
        """
        Test that we can launch a Tor process
        """
        if sys.platform.startswith("linux"):
            tor_cmd = 'tor'
        elif sys.platform.startswith("win"):
            tor_cmd = 'tor.exe'

        tor_sock_port = random.randrange(9000, 9500)
        tor_control_port = random.randrange(9500, 9999)

        result = scholarly.launch_tor(tor_cmd, tor_sock_port, tor_control_port)
        self.assertTrue(result["proxy_works"])
        self.assertTrue(result["refresh_works"])
        self.assertEqual(result["tor_control_port"], tor_control_port)
        self.assertEqual(result["tor_sock_port"], tor_sock_port)
        # Check that we can issue a query as well
        query = 'Ipeirotis'
        authors = [a for a in scholarly.search_author(query)]
        self.assertGreaterEqual(len(authors), 1)


    def test_empty_author(self):
        """
        Test that sholarly.search_author('') returns no authors
        """
        authors = [a for a in scholarly.search_author('')]
        self.assertIs(len(authors), 0)

    def test_empty_keyword(self):
        """
        As of 2020-04-30, there are  6 individuals that match the name 'label'
        """
        # TODO this seems like undesirable functionality for
        # scholarly.search_keyword() with empty string. Surely, no authors
        # should be returned. Consider modifying the method itself.
        authors = [a for a in scholarly.search_keyword('')]
        self.assertEqual(len(authors), 6)

    def test_empty_publication(self):
        """
        Test that searching for an empty publication returns zero results
        """
        pubs = [p for p in scholarly.search_pubs('')]
        self.assertIs(len(pubs), 0)

    
    def test_filling_multiple_publications(self):
         """
         Download a few publications for author and check that abstracts are
         populated with lengths within the expected limits
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

    def test_get_cited_by(self):
        """
        Testing that when we retrieve the list of publications that cite
        a publication, the number of citing publication is the same as
        the number of papers that are returned
        """
        query = 'frequency-domain analysis of haptic gratings cholewiak'
        pubs = [p for p in scholarly.search_pubs(query)]
        self.assertGreaterEqual(len(pubs), 1)
        filled = pubs[0].fill()
        cites = [c for c in filled.citedby]
        self.assertEqual(str(len(cites)), filled.bib['cites'])

    def test_keyword(self):
        """
        When we search for the keyword "3d_shape" the author
        Steven A. Cholewiak should be among those listed
        """
        authors = [a.name for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak, PhD', authors)

    def test_multiple_authors(self):
        """
        As of May 12, 2020 there are at least 24 'Cattanis's listed as authors
        and Giordano Cattani is one of them
        """
        authors = [a.name for a in scholarly.search_author('cattani')]
        self.assertGreaterEqual(len(authors), 24)
        self.assertIn(u'Giordano Cattani', authors)

    def test_multiple_publications(self):
        """
        As of May 12, 2020 there are at least 29 pubs that fit the search term:
        ["naive physics" stability "3d shape"].

        Check that the paper "Visual perception of the physical stability of asymmetric three-dimensional objects"
        is among them
        """
        pubs = [p.bib['title'] for p in scholarly.search_pubs(
            '"naive physics" stability "3d shape"')]
        self.assertGreaterEqual(len(pubs), 29)

        self.assertIn(
            u'Visual perception of the physical stability of asymmetric three-dimensional objects', pubs)

    def test_publication_contents(self):
        query = 'Creating correct blur and its effect on accommodation'
        pubs = [p for p in scholarly.search_pubs(query)]
        self.assertGreaterEqual(len(pubs), 1)
        filled = pubs[0].fill()
        self.assertTrue(
            filled.bib['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S')
        self.assertTrue(filled.bib['journal'] == u'Journal of vision')
        self.assertTrue(filled.bib['number'] == u'9')
        self.assertTrue(filled.bib['pages'] == u'1--1')
        self.assertTrue(
            filled.bib['publisher'] == u'The Association for Research in Vision and Ophthalmology')
        self.assertTrue(
            filled.bib['title'] == u'Creating correct blur and its effect on accommodation')
        self.assertTrue(
            filled.bib['url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817')
        self.assertTrue(filled.bib['volume'] == u'18')
        self.assertTrue(filled.bib['year'] == u'2018')

    def test_single_author(self):
        query = 'Steven A. Cholewiak'
        authors = [a for a in scholarly.search_author(query)]
        self.assertGreaterEqual(len(authors), 1)
        author = authors[0].fill()
        self.assertEqual(author.name, u'Steven A. Cholewiak, PhD')
        self.assertEqual(author.id, u'4bahYMkAAAAJ')


if __name__ == '__main__':
    unittest.main()
