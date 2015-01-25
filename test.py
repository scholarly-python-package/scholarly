import unittest
import scholarly

class TestScholarly(unittest.TestCase):

    def test_empty_author(self):
        authors = [a for a in scholarly.search_author('')]
        self.assertIs(len(authors), 0)

    def test_single_author(self):
        author = scholarly.search_author('Steven A. Cholewiak').next().fill()
        self.assertEqual(author.name, u'Steven A. Cholewiak')
        self.assertEqual(author.id, u'4bahYMkAAAAJ')

    def test_multiple_authors(self):
    	''' As of January 25, there are 22 'Zucker's, 3 pages worth '''
        authors = [a.name for a in scholarly.search_author('Zucker')]
        self.assertEqual(len(authors), 22)
        self.assertIn(u'Steven W Zucker', authors)

    def test_empty_keyword(self):
    	''' Returns 5 individuals with the name 'label' '''
        authors = [a for a in scholarly.search_keyword('')]
        self.assertEqual(len(authors), 5)

    def test_keyword(self):
        authors = [a.name for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak', authors)

    def test_empty_publication(self):
        pubs = [p for p in scholarly.search_pubs_query('')]
        self.assertIs(len(pubs), 0)

    def test_publication_contents(self):
    	pub = scholarly.search_pubs_query('A frequency-domain analysis of haptic gratings').next().fill()
        self.assertDictContainsSubset({
			'author': u'Cholewiak, Steven A and Kim, Kwangtaek and Tan, Hong Z and Adelstein, Bernard D',
			'journal': u'Haptics, IEEE Transactions on',
			'number': u'1',
			'pages': u'3--14',
			'publisher': u'IEEE',
			'title': u'A frequency-domain analysis of haptic gratings',
			'type': u'article',
			'volume': u'3',
			u'year': u'2010',
        }, pub.bib)

    def test_multiple_publications(self):
    	''' As of January 12, there are 31 pubs, 4 pages worth'''
        pubs = [p.bib['title'] for p in scholarly.search_pubs_query('frequency-domain analysis of haptic gratings cholewiak')]
        self.assertEqual(len(pubs), 31)
        self.assertIn(u'A frequency-domain analysis of haptic gratings', pubs)

if __name__ == '__main__':
    unittest.main()
    