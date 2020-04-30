import unittest
import scholarly

# TODO a number of these tests are out of date with the current information on
# Google Scholar. This is the obvious downside of designing static tests that
# rely on dynamic external data.
class TestScholarly(unittest.TestCase):

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
        pub = next(scholarly.search_pubs_query('frequency-domain analysis of haptic gratings cholewiak')).fill()
        cites = [c for c in pub.get_citedby()]
        self.assertEqual(len(cites), pub.citedby)

    def test_keyword(self):
        authors = [a.name for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak, PhD', authors)

    def test_multiple_authors(self):
        ''' As of 2020-04-30 there are 88 'Zucker's '''
        authors = [a.name for a in scholarly.search_author('Zucker')]
        self.assertEqual(len(authors), 88)
        self.assertIn(u'Steven W Zucker', authors)

    def test_multiple_publications(self):
        ''' As of March 14, 2019 there are 28 pubs that fit the search term'''
        pubs = [p.bib['title'] for p in scholarly.search_pubs_query('"naive physics" stability "3d shape"')]
        self.assertEqual(len(pubs), 28)
        self.assertIn(u'Visual perception of the physical stability of asymmetric three-dimensional objects', pubs)

    def test_publication_contents(self):
        pub = next(scholarly.search_pubs_query('Creating correct blur and its effect on accommodation')).fill()
        self.assertTrue(pub.bib['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S')
        self.assertTrue(pub.bib['journal'] == u'Journal of vision')
        self.assertTrue(pub.bib['number'] == u'9')
        self.assertTrue(pub.bib['pages'] == u'1--1')
        self.assertTrue(pub.bib['publisher'] == u'The Association for Research in Vision and Ophthalmology')
        self.assertTrue(pub.bib['title'] == u'Creating correct blur and its effect on accommodation')
        self.assertTrue(pub.bib['url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817')
        self.assertTrue(pub.bib['volume'] == u'18')
        self.assertTrue(pub.bib['year'] == u'2018')

    def test_single_author(self):
        author = next(scholarly.search_author('Steven A. Cholewiak')).fill()
        self.assertEqual(author.name, u'Steven A. Cholewiak')
        self.assertEqual(author.id, u'4bahYMkAAAAJ')

if __name__ == '__main__':
    unittest.main()

