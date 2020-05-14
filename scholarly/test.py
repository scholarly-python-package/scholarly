import unittest
import scholarly
import requests


# TODO a number of these tests are out of date with the current information on
# Google Scholar. This is the obvious downside of designing static tests that
# rely on dynamic external data.
class TestScholarly(unittest.TestCase):

    def _tor_works(self):
        '''
        Checks if Tor is working
        '''
        with requests.Session() as session:
            session.proxies = {
                    'http': 'socks5://127.0.0.1:9050',
                    'https': 'socks5://127.0.0.1:9050'
            }
            try:
                resp = session.get("https://www.google.com")
                if resp.status_code == 200:
                    return True
            except Exception as e:
                pass
            return False

    def setUp(self):
        if self._tor_works():
            scholarly.use_tor()
        #else:
        #    scholarly.use_random_proxy()

    def test_empty_author(self):
        '''Test that sholarly.search_author('') returns no authors'''
        authors = [a for a in scholarly.search_author('')]
        self.assertIs(len(authors), 0)

    def test_empty_keyword(self):
        ''' As of 2020-04-30, there are  6 individuals that match the name
        'label' '''
        # TODO this seems like undesirable functionality for
        # scholarly.search_keyword() with empty string. Surely, no authors
        # should be returned. Consider modifying the method itself.
        authors = [a for a in scholarly.search_keyword('')]
        self.assertEqual(len(authors), 6)

    def test_empty_publication(self):
        pubs = [p for p in scholarly.search_pubs_query('')]
        self.assertIs(len(pubs), 0)

    def test_get_cited_by(self):
        query = 'frequency-domain analysis of haptic gratings cholewiak'
        pubs = [p for p in scholarly.search_pubs_query(query)]
        self.assertGreaterEqual(len(pubs), 1)
        filled = pubs[0].fill()
        cites = [c for c in filled.get_citedby()]
        self.assertEqual(len(cites), filled.citedby)

    def test_keyword(self):
        authors = [a.name for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak, PhD', authors)

    def test_multiple_authors(self):
        ''' As of May 12, 2020 there are at least 24 'Cattanis's '''
        authors = [a.name for a in scholarly.search_author('cattani')]
        self.assertGreaterEqual(len(authors), 24)
        self.assertIn(u'Giordano Cattani', authors)

    def test_multiple_publications(self):
        ''' As of May 12, 2020 there are at least 29 pubs that fit the search term'''
        pubs = [p.bib['title'] for p in scholarly.search_pubs_query('"naive physics" stability "3d shape"')]
        self.assertGreaterEqual(len(pubs), 29)

        self.assertIn(u'Visual perception of the physical stability of asymmetric three-dimensional objects', pubs)

    def test_publication_contents(self):
        query = 'Creating correct blur and its effect on accommodation'
        pubs = [p for p in scholarly.search_pubs_query(query)]
        self.assertGreaterEqual(len(pubs), 1)
        filled = pubs[0].fill()
        self.assertTrue(filled.bib['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S')
        self.assertTrue(filled.bib['journal'] == u'Journal of vision')
        self.assertTrue(filled.bib['number'] == u'9')
        self.assertTrue(filled.bib['pages'] == u'1--1')
        self.assertTrue(filled.bib['publisher'] == u'The Association for Research in Vision and Ophthalmology')
        self.assertTrue(filled.bib['title'] == u'Creating correct blur and its effect on accommodation')
        self.assertTrue(filled.bib['url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817')
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
