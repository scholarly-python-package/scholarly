import unittest
import argparse
import os
import sys
from scholarly import scholarly, ProxyGenerator
from scholarly.publication_parser import PublicationParser
import random
from fp.fp import FreeProxy
import json


class TestScholarly(unittest.TestCase):

    def setUp(self):
        proxy_generator = ProxyGenerator()
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
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                tor_cmd = 'tor'
            elif sys.platform.startswith("win"):
                tor_cmd = 'tor.exe'
            else:
                tor_cmd = None
            proxy_generator.Tor_Internal(tor_cmd = tor_cmd)
            scholarly.use_proxy(proxy_generator)
        elif self.connection_method == "luminati":
            scholarly.set_retries(10)
            proxy_generator.Luminati(usr=os.getenv("USERNAME"),
                                     passwd=os.getenv("PASSWORD"),
                                     proxy_port = os.getenv("PORT"),
                                     skip_checking_proxy=True)
            scholarly.use_proxy(proxy_generator)
        elif self.connection_method == "freeproxy":
            proxy_generator.FreeProxies()
            scholarly.use_proxy(proxy_generator)
        elif self.connection_method == "scraperapi":
            proxy_generator.ScraperAPI(os.getenv('SCRAPER_API_KEY'), skip_checking_proxy=True)
            scholarly.use_proxy(proxy_generator)
        else:
            scholarly.use_proxy(None)

    def tearDown(self):
        return
        if self.connection_method == "freeproxy":
            scholarly._Scholarly__nav.pm1._fp_gen.close()
        scholarly._Scholarly__nav.pm2._fp_gen.close()

    @unittest.skipUnless([_bin for path in sys.path if os.path.isdir(path) for _bin in os.listdir(path)
                          if _bin=='tor' or _bin=='tor.exe'], reason='Tor executable not found')
    def test_tor_launch_own_process(self):
        """
        Test that we can launch a Tor process
        """
        proxy_generator = ProxyGenerator()
        if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            tor_cmd = 'tor'
        elif sys.platform.startswith("win"):
            tor_cmd = 'tor.exe'
        else:
            tor_cmd = None

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
        filled = scholarly.fill(pubs[0])
        cites = [c for c in scholarly.citedby(filled)]
        self.assertEqual(len(cites), filled['num_citations'])

    def test_search_pubs_citedby_id(self):
        """
        Test querying for citations by paper ID.

        The 'Machine-learned epidemiology' paper had 11 citations as of
        June 1, 2020.
        """
        # Machine-learned epidemiology: real-time detection of foodborne illness at scale
        publication_id = 2244396665447968936

        pubs = [p for p in scholarly.search_citedby(publication_id)]
        self.assertGreaterEqual(len(pubs), 11)

    def test_search_keyword(self):
        """
        When we search for the keyword "3d_shape" the author
        Steven A. Cholewiak should be among those listed
        """
        authors = [a['name'] for a in scholarly.search_keyword('3d_shape')]
        self.assertIsNot(len(authors), 0)
        self.assertIn(u'Steven A. Cholewiak, PhD', authors)

    def test_search_author_single_author(self):
        query = 'Steven A. Cholewiak'
        authors = [a for a in scholarly.search_author(query)]
        self.assertGreaterEqual(len(authors), 1)
        author = scholarly.fill(authors[0])
        self.assertEqual(author['name'], u'Steven A. Cholewiak, PhD')
        self.assertEqual(author['scholar_id'], u'4bahYMkAAAAJ')
        # Currently, fetching more than 20 coauthors works only if not using a proxy.
        if self.connection_method=="none":
            self.assertGreaterEqual(len(author['coauthors']), 33, "Full coauthor list not fetched")
            self.assertTrue('I23YUh8AAAAJ' in [_coauth['scholar_id'] for _coauth in author['coauthors']])
        else:
            self.assertEqual(len(author['coauthors']), 20)
        self.assertEqual(author['homepage'], "http://steven.cholewiak.com/")
        self.assertEqual(author['organization'], 6518679690484165796)
        self.assertGreaterEqual(author['public_access']['available'], 10)
        self.assertEqual(author['public_access']['available'],
                         sum(pub.get('public_access', None) is True for pub in author['publications']))
        self.assertEqual(author['public_access']['not_available'],
                         sum(pub.get('public_access', None) is False for pub in author['publications']))
        pub = author['publications'][2]
        self.assertEqual(pub['author_pub_id'], u'4bahYMkAAAAJ:LI9QrySNdTsC')
        self.assertTrue('5738786554683183717' in pub['cites_id'])

    def test_search_author_multiple_authors(self):
        """
        As of May 12, 2020 there are at least 24 'Cattanis's listed as authors
        and Giordano Cattani is one of them
        """
        authors = [a['name'] for a in scholarly.search_author('cattani')]
        self.assertGreaterEqual(len(authors), 24)
        self.assertIn(u'Giordano Cattani', authors)

    def test_search_author_id(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permenant
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ')
        self.assertEqual(author['name'], u'Marie Skłodowska-Curie')
        self.assertEqual(author['affiliation'],
                         u'Institut du radium, University of Paris')

    def test_search_author_id_filled(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permenant.
        As of July 2020, Marie Skłodowska-Curie has 1963 citations
        on Google Scholar and 179 publications
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ', filled=True)
        self.assertEqual(author['name'], u'Marie Skłodowska-Curie')
        self.assertEqual(author['affiliation'],
                         u'Institut du radium, University of Paris')
        self.assertEqual(author['public_access']['available'], 0)
        self.assertEqual(author['public_access']['not_available'], 0)
        self.assertGreaterEqual(author['citedby'], 1963) # TODO: maybe change
        self.assertGreaterEqual(len(author['publications']), 179)
        pub = author['publications'][1]
        self.assertEqual(pub["citedby_url"],
                         "https://scholar.google.com/scholar?oi=bibs&hl=en&cites=9976400141451962702")

    def test_search_pubs(self):
        """
        As of May 12, 2020 there are at least 29 pubs that fit the search term:
        ["naive physics" stability "3d shape"].

        Check that the paper "Visual perception of the physical stability of asymmetric three-dimensional objects"
        is among them
        """
        pubs = [p['bib']['title'] for p in scholarly.search_pubs(
            '"naive physics" stability "3d shape"')]
        self.assertGreaterEqual(len(pubs), 27)

        self.assertIn('Visual perception of the physical stability of asymmetric three-dimensional objects', pubs)

    def test_search_pubs_total_results(self):
        """
        As of September 16, 2021 there are 32 pubs that fit the search term:
        ["naive physics" stability "3d shape"], and 17'000 results that fit
        the search term ["WIEN2k Blaha"] and none for ["sdfsdf+24r+asdfasdf"].

        Check that the total results for that search term equals 32.
        """
        pubs = scholarly.search_pubs('"naive physics" stability "3d shape"')
        self.assertGreaterEqual(pubs.total_results, 32)

        pubs = scholarly.search_pubs('WIEN2k Blaha')
        self.assertGreaterEqual(pubs.total_results, 10000)

        pubs = scholarly.search_pubs('sdfsdf+24r+asdfasdf')
        self.assertEqual(pubs.total_results, 0)

    def test_search_pubs_filling_publication_contents(self):
        '''
        This process  checks the process of filling a publication that is derived
         from the search publication snippets.
        '''
        query = 'Creating correct blur and its effect on accommodation'
        results = scholarly.search_pubs(query)
        pubs = [p for p in results]
        self.assertGreaterEqual(len(pubs), 1)
        f = scholarly.fill(pubs[0])
        self.assertTrue(f['bib']['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S')
        self.assertTrue(f['author_id'] == ['4bahYMkAAAAJ', '3xJXtlwAAAAJ', 'Smr99uEAAAAJ'])
        self.assertTrue(f['bib']['journal'] == u'Journal of Vision')
        self.assertTrue(f['bib']['number'] == '9')
        self.assertTrue(f['bib']['pages'] == u'1--1')
        self.assertTrue(f['bib']['publisher'] == u'The Association for Research in Vision and Ophthalmology')
        self.assertTrue(f['bib']['title'] == u'Creating correct blur and its effect on accommodation')
        self.assertTrue(f['pub_url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817')
        self.assertTrue(f['bib']['volume'] == '18')
        self.assertTrue(f['bib']['pub_year'] == u'2018')

    def test_extract_author_id_list(self):
        '''
        This unit test tests the extraction of the author id field from the html to populate the `author_id` field
        in the Publication object.
        '''
        author_html_full = '<a href="/citations?user=4bahYMkAAAAJ&amp;hl=en&amp;oi=sra">SA Cholewiak</a>, <a href="/citations?user=3xJXtlwAAAAJ&amp;hl=en&amp;oi=sra">GD Love</a>, <a href="/citations?user=Smr99uEAAAAJ&amp;hl=en&amp;oi=sra">MS Banks</a> - Journal of vision, 2018 - jov.arvojournals.org'
        pub_parser = PublicationParser(None)
        author_id_list = pub_parser._get_author_id_list(author_html_full)
        self.assertTrue(author_id_list[0] == '4bahYMkAAAAJ')
        self.assertTrue(author_id_list[1] == '3xJXtlwAAAAJ')
        self.assertTrue(author_id_list[2] == 'Smr99uEAAAAJ')

        author_html_partial = "A Bateman, J O'Connell, N Lorenzini, <a href=\"/citations?user=TEndP-sAAAAJ&amp;hl=en&amp;oi=sra\">T Gardner</a>…&nbsp;- BMC psychiatry, 2016 - Springer"
        pub_parser = PublicationParser(None)
        author_id_list = pub_parser._get_author_id_list(author_html_partial)
        self.assertTrue(author_id_list[3] == 'TEndP-sAAAAJ')

    def test_serialiazation(self):
        """
        Test that we can serialize the Author and Publication types

        Note: JSON converts integer keys to strings, resulting in the years
        in `cites_per_year` dictionary as `str` type instead of `int`.
        To ensure consistency with the typing, use `object_hook` option
        when loading to convert the keys to integers.
        """
        # Test that a filled Author with unfilled Publication
        # is serializable.
        def cpy_decoder(di):
            """A utility function to convert the keys in `cites_per_year` to `int` type.

              This ensures consistency with `CitesPerYear` typing.
            """
            if "cites_per_year" in di:
                di["cites_per_year"] = {int(k): v for k,v in di["cites_per_year"].items()}
            return di

        author = scholarly.search_author_id('EmD_lTEAAAAJ', filled=True)
        serialized = json.dumps(author)
        author_loaded = json.loads(serialized, object_hook=cpy_decoder)
        self.assertEqual(author, author_loaded)
        # Test that a loaded publication is still fillable and serializable.
        pub = author_loaded['publications'][0]
        scholarly.fill(pub)
        serialized = json.dumps(pub)
        pub_loaded = json.loads(serialized, object_hook=cpy_decoder)
        self.assertEqual(pub, pub_loaded)

    def test_full_title(self):
        """
        Test if the full title of a long title-publication gets retrieved.
        The code under test gets executed if:
        publication['source'] == PublicationSource.AUTHOR_PUBLICATION_ENTRY
        so the long title-publication is taken from an author object.
        """
        author = scholarly.search_author_id('Xxjj6IsAAAAJ')
        author = scholarly.fill(author, sections=['publications'])
        pub_index = -1
        for i in range(len(author['publications'])):
            if author['publications'][i]['author_pub_id'] == 'Xxjj6IsAAAAJ:u_35RYKgDlwC':
                pub_index = i
        self.assertGreaterEqual(i, 0)
        # elided title
        self.assertEqual(author['publications'][pub_index]['bib']['title'],
                         u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary …')
        # full text
        pub = scholarly.fill(author['publications'][pub_index])
        self.assertEqual(pub['bib']['title'],
                         u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary investigation')

    def test_author_organization(self):
        """
        """
        organization = 4836318610601440500  # Princeton University
        search_query = scholarly.search_author_by_organization(organization)
        author = next(search_query)
        self.assertEqual(author['scholar_id'], "ImhakoAAAAAJ")
        self.assertEqual(author['name'], "Daniel Kahneman")
        self.assertEqual(author['email_domain'], "@princeton.edu")
        self.assertEqual(author['affiliation'], "Princeton University (Emeritus)")
        self.assertGreaterEqual(author['citedby'], 438891)

    def test_public_access(self):
        """
        Test that we obtain public access information

        We check two cases: 1) when number of public access mandates exceeds
        100, thus requiring fetching information from a second page and 2) fill
        public access counts without fetching publications.
        """
        author = scholarly.search_author_id("7x48vOkAAAAJ")
        scholarly.fill(author, sections=['basics', 'public_access', 'publications'])
        self.assertGreaterEqual(author["public_access"]["available"], 110)
        self.assertEqual(author["public_access"]["available"],
                         sum(pub.get("public_access", None) is True for pub in author["publications"]))
        self.assertEqual(author["public_access"]["not_available"],
                         sum(pub.get("public_access", None) is False for pub in author["publications"]))

        author = next(scholarly.search_author("Daniel Kahneman"))
        scholarly.fill(author, sections=["basics", "indices", "public_access"])
        self.assertEqual(author["scholar_id"], "ImhakoAAAAAJ")
        self.assertGreaterEqual(author["public_access"]["available"], 6)


if __name__ == '__main__':
    unittest.main()
