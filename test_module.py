import pytest
import os
import sys
from collections import Counter
from scholarly import scholarly, ProxyGenerator
from scholarly.data_types import Mandate
from scholarly.publication_parser import PublicationParser
import random
import json
import csv
import requests
from bs4 import BeautifulSoup
from contextlib import contextmanager
try:
    import pandas as pd
except ImportError:
    pd = None


class TestLuminati:
    skipUnless = os.getenv("USERNAME") and os.getenv("PASSWORD") and os.getenv("PORT")

    @pytest.mark.skipif(not skipUnless, reason="No Luminati credentials found.")
    def test_luminati(self):
        """
        Test that we can set up Luminati (Bright Data) successfully
        """
        proxy_generator = ProxyGenerator()
        success = proxy_generator.Luminati(usr=os.getenv("USERNAME"),
                                           passwd=os.getenv("PASSWORD"),
                                           proxy_port=os.getenv("PORT"))
        assert success
        assert proxy_generator.proxy_mode == "LUMINATI"


class TestScraperAPI:
    skipUnless = os.getenv('SCRAPER_API_KEY')

    @pytest.mark.skipif(not skipUnless, reason="No ScraperAPI key found")
    def test_scraperapi(self):
        """
        Test that we can set up ScraperAPI successfully
        """
        proxy_generator = ProxyGenerator()
        success = proxy_generator.ScraperAPI(os.getenv('SCRAPER_API_KEY'))
        assert success
        assert proxy_generator.proxy_mode == "SCRAPERAPI"


class TestTorInternal:
    skipUnless = [_bin for path in sys.path if os.path.isdir(path) for _bin in os.listdir(path)
                  if _bin in ('tor', 'tor.exe')]

    @pytest.mark.skipif(not skipUnless, reason='Tor executable not found')
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
        assert result["proxy_works"]
        assert result["refresh_works"]
        assert result["tor_control_port"] == tor_control_port
        assert result["tor_sock_port"] == tor_sock_port
        # Check that we can issue a query as well
        query = 'Ipeirotis'
        scholarly.use_proxy(proxy_generator)
        authors = [a for a in scholarly.search_author(query)]
        assert 1 <= len(authors)

class TestFreeProxy:
    luminati = os.getenv("USERNAME") and os.getenv("PASSWORD") and os.getenv("PORT")
    scraperAPI = os.getenv('SCRAPER_API_KEY')
    skipIf = (luminati is not None) or (scraperAPI is not None)

    @pytest.mark.skipif(skipIf, reason="Other proxy is being used")
    def test_freeproxy(self):
        """
        Test that we can set up FreeProxy successfully
        """
        proxy_generator = ProxyGenerator()
        success = proxy_generator.FreeProxies()
        assert success
        assert proxy_generator.proxy_mode == "FREE_PROXIES"

class TestScholarly:

    @classmethod
    def setUpClass(cls):
        scholarly.set_timeout(5)
        scholarly.set_retries(5)

        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg, ProxyGenerator())

        # Try storing the file temporarily as `scholarly.csv` and delete it.
        # If there exists already a file with that name, generate a random name
        # that does not exist yet, so we can safely delete it.
        cls.mandates_filename = "scholarly.csv"
        while os.path.exists(cls.mandates_filename):
            cls.mandates_filename = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)) + ".csv"

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the mandates csv fiile downloaded.
        """
        if os.path.exists(cls.mandates_filename):
            os.remove(cls.mandates_filename)

    @staticmethod
    @contextmanager
    def suppress_stdout():
        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout

    def test_search_author_empty_author(self):
        """
        Test that sholarly.search_author('') returns no authors
        """
        authors = [a for a in scholarly.search_author('')]
        assert len(authors) == 0

    def test_search_keywords(self):
        query = scholarly.search_keywords(['crowdsourcing', 'privacy'])
        author = next(query)
        assert author['scholar_id'] == '_cMw1IUAAAAJ'
        assert author['name'] == 'Arpita Ghosh'
        assert author['affiliation'] == 'Cornell University'

    def test_search_keyword_empty_keyword(self):
        """
        As of 2020-04-30, there are  6 individuals that match the name 'label'
        """
        # TODO this seems like undesirable functionality for
        # scholarly.search_keyword() with empty string. Surely, no authors
        # should be returned. Consider modifying the method itself.
        authors = [a for a in scholarly.search_keyword('')]
        assert 6 <= len(authors)

    def test_search_keyword(self):
        """
        Test that we can search based on specific keywords

        When we search for the keyword "3d shape" the author
        Steven A. Cholewiak should be among those listed.
        When we search for the keyword "Haptics", Oussama Khatib
        should be listed first.
        """
        # Example 1
        authors = [a['name'] for a in scholarly.search_keyword('3d shape')]
        assert len(authors) != 0
        assert u'Steven A. Cholewiak, PhD' in authors

        # Example 2
        expected_author = {'affiliation': 'Stanford University',
                           'citedby': 43856,
                           'email_domain': '@cs.stanford.edu',
                           'filled': [],
                           'interests': ['Robotics',
                                         'Haptics',
                                         'Human Motion Understanding'],
                           'name': 'Oussama Khatib',
                           'scholar_id': '4arkOLcAAAAJ',
                           'source': 'SEARCH_AUTHOR_SNIPPETS',
                           'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=4arkOLcAAAAJ'
                           }
        search_query = scholarly.search_keyword('Haptics')
        author = next(search_query)
        for key in author:
            if (key not in {"citedby", "container_type", "interests"}) and (key in expected_author):
                assert author[key] == expected_author[key]
        assert set(author["interests"]) == set(expected_author["interests"])

        # Example 3
        expected_author = {'affiliation': "CEA, Département d'Astrophysique",
                           'citedby': 98936,
                           'email_domain': '@cea.fr',
                           'filled': [],
                           'interests': ['Cosmology (CMB',
                                         'weak-lensing',
                                         'large scale structure)',
                                         'Statistics',
                                         'Image Processing'],
                           'name': 'Jean-Luc Starck',
                           'scholar_id': 'IAaAiXgAAAAJ',
                           'source': 'SEARCH_AUTHOR_SNIPPETS',
                           'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=IAaAiXgAAAAJ'
                           }
        search_query = scholarly.search_keyword('large-scale structure')
        author = next(search_query)
        for key in author:
            if (key not in {"citedby", "container_type", "interests"}) and (key in expected_author):
                assert author[key] == expected_author[key]
        scholarly.pprint(author)
        assert set(author["interests"]) == set(expected_author["interests"])

    def test_search_author_single_author(self):
        query = 'Steven A. Cholewiak'
        authors = [a for a in scholarly.search_author(query)]
        assert 1 <= len(authors)
        author = scholarly.fill(authors[0])
        assert author['name'] == u'Steven A. Cholewiak, PhD'
        assert author['scholar_id'] == u'4bahYMkAAAAJ'

        assert author['homepage'] == "http://steven.cholewiak.com/"
        assert author['organization'] == 6518679690484165796
        assert 10 <= author['public_access']['available']
        assert author['public_access']['available'] == \
                         sum(pub.get('public_access', None) is True for pub in author['publications'])
        assert author['public_access']['not_available'] == \
                         sum(pub.get('public_access', None) is False for pub in author['publications'])
        pub = author['publications'][1]
        assert pub['author_pub_id'] == u'4bahYMkAAAAJ:LI9QrySNdTsC'
        assert '5738786554683183717' in pub['cites_id']
        scholarly.fill(pub)
        assert pub['pub_url'] == "https://dl.acm.org/doi/abs/10.1145/3130800.3130815"
        mandate = Mandate(agency="US National Science Foundation", effective_date="2016/1", embargo="12 months",
                          url_policy="https://www.nsf.gov/pubs/2015/nsf15052/nsf15052.pdf",
                          url_policy_cached="/mandates/nsf-2021-02-13.pdf",
                          grant="BCS-1354029")
        assert mandate['agency'] in [_mandate['agency'] for _mandate in pub['mandates']]
        # Trigger the pprint method, but suppress the output
        with self.suppress_stdout():
            scholarly.pprint(author)
            scholarly.pprint(pub)
        # Check for the complete list of coauthors
        assert 20 <= len(author['coauthors'])
        if len(author['coauthors']) > 20:
            assert 35 <= len(author['coauthors'])
            assert 'I23YUh8AAAAJ' in [_coauth['scholar_id'] for _coauth in author['coauthors']]

    def test_search_author_multiple_authors(self):
        """
        As of May 12, 2020 there are at least 24 'Cattanis's listed as authors
        and Giordano Cattani is one of them
        """
        authors = [a['name'] for a in scholarly.search_author('cattani')]
        assert 24 <= len(authors)
        assert u'Giordano Cattani' in authors

    def test_search_author_id(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permanent
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ')
        assert author['name'] == u'Marie Skłodowska-Curie'
        assert author['affiliation'] == \
                         u'Institut du radium, University of Paris'

    def test_search_author_id_filled(self):
        """
        Test the search by author ID. Marie Skłodowska-Curie's ID is
        EmD_lTEAAAAJ and these IDs are permanent.
        As of July 2020, Marie Skłodowska-Curie has 1963 citations
        on Google Scholar and 179 publications
        """
        author = scholarly.search_author_id('EmD_lTEAAAAJ', filled=True)
        assert author['name'] == u'Marie Skłodowska-Curie'
        assert author['affiliation'] == \
                         u'Institut du radium, University of Paris'
        assert author['interests'] == []
        assert author['public_access']['available'] == 0
        assert author['public_access']['not_available'] == 0
        assert 2090 <= author['citedby']
        assert 218 <= len(author['publications'])
        cpy = {1986:4, 2011: 137, 2018: 100}
        for year, count in cpy.items():
            assert author["cites_per_year"][year] == count
        pub = author['publications'][1]
        assert pub["citedby_url"] == \
                         "https://scholar.google.com/scholar?oi=bibs&hl=en&cites=9976400141451962702"


    def test_extract_author_id_list(self):
        '''
        This unit test tests the extraction of the author id field from the html to populate the `author_id` field
        in the Publication object.
        '''
        author_html_full = '<a href="/citations?user=4bahYMkAAAAJ&amp;hl=en&amp;oi=sra">SA Cholewiak</a>, <a href="/citations?user=3xJXtlwAAAAJ&amp;hl=en&amp;oi=sra">GD Love</a>, <a href="/citations?user=Smr99uEAAAAJ&amp;hl=en&amp;oi=sra">MS Banks</a> - Journal of vision, 2018 - jov.arvojournals.org'
        pub_parser = PublicationParser(None)
        author_id_list = pub_parser._get_author_id_list(author_html_full)
        assert author_id_list[0] == '4bahYMkAAAAJ'
        assert author_id_list[1] == '3xJXtlwAAAAJ'
        assert author_id_list[2] == 'Smr99uEAAAAJ'

        author_html_partial = "A Bateman, J O'Connell, N Lorenzini, <a href=\"/citations?user=TEndP-sAAAAJ&amp;hl=en&amp;oi=sra\">T Gardner</a>…&nbsp;- BMC psychiatry, 2016 - Springer"
        pub_parser = PublicationParser(None)
        author_id_list = pub_parser._get_author_id_list(author_html_partial)
        assert author_id_list[3] == 'TEndP-sAAAAJ'

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
        assert author == author_loaded
        # Test that a loaded publication is still fillable and serializable.
        pub = author_loaded['publications'][0]
        scholarly.fill(pub)
        serialized = json.dumps(pub)
        pub_loaded = json.loads(serialized, object_hook=cpy_decoder)
        assert pub == pub_loaded

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
        # Skip this part of the test since u_35RYKgDlwC has vanished from Google Scholar
        if False:
            for i in range(len(author['publications'])):
                if author['publications'][i]['author_pub_id'] == 'Xxjj6IsAAAAJ:u_35RYKgDlwC':
                    pub_index = i
            assert 0 <= i
            # elided title
            assert author['publications'][pub_index]['bib']['title'] == \
                             u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary …'
            # full text
            pub = scholarly.fill(author['publications'][pub_index])
            assert pub['bib']['title'] == \
                             u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary investigation'

            assert pub['bib']['citation'] == ""

        for i in range(len(author['publications'])):
            if author['publications'][i]['author_pub_id'] == 'Xxjj6IsAAAAJ:ldfaerwXgEUC':
                pub_index = i
        assert 0 <= i
        # elided title
        assert author['publications'][pub_index]['bib']['title'] == \
                         u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary …'
        # full text
        pub = scholarly.fill(author['publications'][pub_index])
        assert pub['bib']['title'] == \
                         u'Evaluation of toxicity of Dichlorvos (Nuvan) to fresh water fish Anabas testudineus and possible modulation by crude aqueous extract of Andrographis paniculata: A preliminary …'

        assert pub['bib']['citation'] == "Journal of Fisheries and Life Sciences 5 (2), 74-84, 2020"

    def test_author_organization(self):
        """
        """
        organization_id = 4836318610601440500  # Princeton University
        organizations = scholarly.search_org("Princeton University")
        assert len(organizations) == 1
        organization = organizations[0]
        assert organization['Organization'] == "Princeton University"
        assert organization['id'] == str(organization_id)

        search_query = scholarly.search_author_by_organization(organization_id)
        author = next(search_query)
        assert author['scholar_id'] == "ImhakoAAAAAJ"
        assert author['name'] == "Daniel Kahneman"
        assert author['email_domain'] == "@princeton.edu"
        assert author['affiliation'] == "Princeton University (Emeritus)"
        assert 438891 <= author['citedby']

    def test_coauthors(self):
        """
        Test that we can fetch long (20+) and short list of coauthors
        """
        author = scholarly.search_author_id('7Jl3PIoAAAAJ')
        scholarly.fill(author, sections=['basics', 'coauthors'])
        assert author['name'] == "Victor Silva"
        assert len(author['coauthors']) <= 20
        # If the above assertion fails, pick a different author profile
        assert 6 <= len(author['coauthors'])
        assert 'Eleni Stroulia' in [_coauth['name'] for _coauth in author['coauthors']]
        assert 'TyM1dLwAAAAJ' in [_coauth['scholar_id'] for _coauth in author['coauthors']]
        # Fill co-authors
        for _coauth in author['coauthors']:
            scholarly.fill(_coauth, sections=['basics'])
        assert 16627554827500071773 in [_coauth.get('organization', None) for _coauth in author['coauthors']]

        author = scholarly.search_author_id('PA9La6oAAAAJ')
        scholarly.fill(author, sections=['basics', 'coauthors'])
        assert author['name'] == "Panos Ipeirotis"
        assert 66 <= len(author['coauthors'])
        # Break the build if the long list cannot be fetched.
        assert 'Eduardo Ruiz' in [_coauth['name'] for _coauth in author['coauthors']]
        assert 'hWq7jFQAAAAJ' in [_coauth['scholar_id'] for _coauth in author['coauthors']]

    def test_public_access(self):
        """
        Test that we obtain public access information

        We check two cases: 1) when number of public access mandates exceeds
        100, thus requiring fetching information from a second page and 2) fill
        public access counts without fetching publications.
        """
        author = scholarly.search_author_id("f4KlrXIAAAAJ")
        scholarly.fill(author, sections=['basics', 'public_access', 'publications'])
        assert 1150 <= author["public_access"]["available"]
        assert author["public_access"]["available"] == \
                         sum(pub.get("public_access", None) is True for pub in author["publications"])
        assert author["public_access"]["not_available"] == \
                         sum(pub.get("public_access", None) is False for pub in author["publications"])

        author = next(scholarly.search_author("Daniel Kahneman"))
        assert author["scholar_id"] == "ImhakoAAAAAJ"
        assert author["interests"] == []
        scholarly.fill(author, sections=["public_access"])
        assert 5 <= author["public_access"]["available"]

    def test_mandates(self):
        """
        Test that we can fetch the funding information of a paper from an author
        """
        author = scholarly.search_author_id("kUDCLXAAAAAJ")
        scholarly.fill(author, sections=['public_access', 'publications'])
        for pub in author['publications']:
            if pub['author_pub_id'] == "kUDCLXAAAAAJ:tzM49s52ZIMC":
                scholarly.fill(pub)
                break
        # The hard-coded reference mandate may need regular updates.
        mandate = Mandate(agency="European Commission", effective_date="2013/12", embargo="6 months", grant="647112",
                          url_policy="https://erc.europa.eu/sites/default/files/document/file/ERC%20Open%20Access%20guidelines-Version%201.1._10.04.2017.pdf",
                          url_policy_cached="/mandates/horizon2020_eu-2021-02-13-en.pdf",
        )
        assert mandate in pub['mandates']

    def test_author_custom_url(self):
        """
        Test that we can use custom URLs for retrieving author data
        """
        query_url = "/citations?hl=en&view_op=search_authors&mauthors=label%3A3d_shape"
        authors = scholarly.search_author_custom_url(query_url)
        assert u'Steven A. Cholewiak, PhD' in [author['name'] for author in authors]

    @pytest.mark.skipif(sys.platform.startswith("win"), reason="File read is empty in Windows")
    def test_download_mandates_csv(self):
        """
        Test that we can download the mandates CSV and read it.
        """
        if not os.path.exists(self.mandates_filename):
            text = scholarly.download_mandates_csv(self.mandates_filename)
            assert 0 < len(text)
        funder, policy, percentage2020, percentageOverall = [], [], [], []
        with open(self.mandates_filename, "r") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                funder.append(row['\ufeffFunder'])
                policy.append(row['Policy'])
                percentage2020.append(row['2020'])
                percentageOverall.append(row['Overall'])

        agency_policy = {
            "US National Science Foundation": "https://www.nsf.gov/pubs/2015/nsf15052/nsf15052.pdf",
            "Department of Science & Technology, India": "http://www.dst.gov.in/sites/default/files/APPROVED%20OPEN%20ACCESS%20POLICY-DBT%26DST%2812.12.2014%29_1.pdf",
            "Swedish Research Council": "https://www.vr.se/english/applying-for-funding/requirements-terms-and-conditions/publishing-open-access.html",
            "Swedish Research Council for Environment, Agricultural Sciences and Spatial Planning": ""
        }
        agency_2020 = {
            "US National Science Foundation": "87%",
            "Department of Science & Technology, India": "49%",
            "Swedish Research Council": "89%",
            "Swedish Research Council for Environment, Agricultural Sciences and Spatial Planning": "88%"
        }

        response = requests.get("https://scholar.google.com/citations?view_op=mandates_leaderboard&hl=en")
        soup = BeautifulSoup(response.text, "html.parser")
        agency_overall = soup.find_all("td", class_="gsc_mlt_n gsc_mlt_bd")

        # These hardcoded numbers need some regular updates.
        for agency, index in zip(agency_policy, [5-1,9-1, 21-1, 63-1]):
            agency_index = funder.index(agency)
            assert policy[agency_index] == agency_policy[agency]
            # Check that the percentage values from CSV and on the page agree.
            assert percentageOverall[agency_index] == agency_overall[index].text
            # The percentage fluctuates, so we can't check the exact value.
            assert int(percentage2020[agency_index][:-1]) == pytest.approx(int(agency_2020[agency][:-1]), abs=2)

    @pytest.mark.skipif(sys.platform.startswith("win"), reason="File read is empty in Windows")
    @pytest.mark.skipif(pd is None, reason="pandas is not installed")
    def test_download_mandates_csv_with_pandas(self):
        """
        Test that we can use pandas to read the CSV file
        """
        if not os.path.exists(self.mandates_filename):
            text = scholarly.download_mandates_csv(self.mandates_filename)
            assert 0 < len(text)
        df = pd.read_csv(self.mandates_filename, usecols=["Funder", "Policy", "2020", "Overall"]).fillna("")
        assert 0 < len(df)

        funders = ["US National Science Foundation",
                   "Department of Science & Technology, India",
                   "Swedish Research Council",
                   "Swedish Research Council for Environment, Agricultural Sciences and Spatial Planning"
                   ]

        policies = ["https://www.nsf.gov/pubs/2015/nsf15052/nsf15052.pdf",
                    "http://www.dst.gov.in/sites/default/files/APPROVED%20OPEN%20ACCESS%20POLICY-DBT%26DST%2812.12.2014%29_1.pdf",
                    "https://www.vr.se/english/applying-for-funding/requirements-terms-and-conditions/publishing-open-access.html",
                    ""
                    ]
        percentage_overall = [84, 54, 83, 83]
        percentage_2020 = [87, 49, 89, 88]

        rows = df["Funder"].isin(funders)
        assert rows.sum() == 4
        assert df["Policy"][rows].tolist() == policies
        df_overall = df["Overall"][rows].tolist()
        df_2020 = df["2020"][rows].tolist()
        for idx in range(4):
            assert int(df_overall[idx][:-1]) == pytest.approx(percentage_overall[idx], abs=2)
            assert int(df_2020[idx][:-1]) == pytest.approx(percentage_2020[idx], abs=2)

    def test_save_journal_leaderboard(self):
        """
        Test that we can save the journal leaderboard to a file
        """
        filename = "journals.csv"
        while os.path.exists(filename):
            filename = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)) + ".csv"

        try:
            scholarly.save_journals_csv(category="Physics & Mathematics", subcategory="Astronomy & Astrophysics",
                                        filename=filename, include_comments=True)
            with open(filename, "r") as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    # These hard-coded values need regular updates.
                    assert row['Publication'] == 'The Astrophysical Journal'
                    assert row['h5-index'] == '167'
                    assert row['h5-median'] == '234'
                    assert row['Comment'] == '#1 Astronomy & Astrophysics; #2 Physics & Mathematics; '
                    break
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_bin_citations_by_year(self):
        """Test an internal optimization function to bin cites_per_year
           while keeping the citation counts less than 1000 per bin.
        """
        cpy = {2022: 490, 2021: 340, 2020:327, 2019:298, 2018: 115, 2017: 49, 2016: 20, 2015: 8, 2014: 3, 2013: 1, 2012: 1}
        years = scholarly._bin_citations_by_year(cpy, 2022)
        for y_hi, y_lo in years:
            assert y_lo <= y_hi
            assert sum(cpy[y] for y in range(y_lo, y_hi+1)) <= 1000

    def test_cites_per_year(self):
        """Test that the cites_per_year is correctly filled in,
           including any gap years.
        """
        author = scholarly.search_author_id('DW_bVcEAAAAJ')
        scholarly.fill(author, sections=['counts'])
        cpy = {2014: 1, 2015: 2, 2016: 2, 2017: 0, 2018: 2, 2019: 0, 2020: 11, 2021: 21, 2022: 37}
        for year, count in cpy.items():
            assert author['cites_per_year'][year] == count

    def test_redirect(self):
        """Test that we can handle redirects when the scholar_id is approximate.
        """
        author = scholarly.search_author_id("oMaIg8sAAAAJ")
        assert author["scholar_id"] == "PEJ42J0AAAAJ"
        scholarly.fill(author, sections=["basics"])
        assert author["name"] == "Kiran Bhatia"
        assert 135 <= author["citedby"]

class TestScholarlyWithProxy:
    @classmethod
    def setUpClass(cls):
        """
        Setup the proxy methods for unit tests
        """
        scholarly.set_timeout(5)
        scholarly.set_retries(5)

        if "CONNECTION_METHOD" in scholarly.env:
            cls.connection_method = os.getenv("CONNECTION_METHOD")
        else:
            cls.connection_method = "none"
            scholarly.use_proxy(None)
            return

        # Use dual proxies for unit testing
        secondary_proxy_generator = ProxyGenerator()
        secondary_proxy_generator.FreeProxies()

        proxy_generator = ProxyGenerator()
        if cls.connection_method == "tor":
            tor_password = "scholarly_password"
            # Tor uses the 9050 port as the default socks port
            # on windows 9150 for socks and 9151 for control
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                tor_sock_port = 9050
                tor_control_port = 9051
            elif sys.platform.startswith("win"):
                tor_sock_port = 9150
                tor_control_port = 9151
            else:
                tor_sock_port = None
                tor_control_port = None
            proxy_generator.Tor_External(tor_sock_port, tor_control_port,
                                         tor_password)

        elif cls.connection_method == "tor_internal":
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                tor_cmd = 'tor'
            elif sys.platform.startswith("win"):
                tor_cmd = 'tor.exe'
            else:
                tor_cmd = None
            proxy_generator.Tor_Internal(tor_cmd = tor_cmd)

        elif cls.connection_method == "luminati":
            scholarly.set_retries(10)
            proxy_generator.Luminati(usr=os.getenv("USERNAME"),
                                     passwd=os.getenv("PASSWORD"),
                                     proxy_port=os.getenv("PORT"))

        elif cls.connection_method == "freeproxy":
            # Use different instances for primary and secondary
            proxy_generator = ProxyGenerator()
            proxy_generator.FreeProxies()

        elif cls.connection_method == "scraperapi":
            proxy_generator.ScraperAPI(os.getenv('SCRAPER_API_KEY'))

        else:
            scholarly.use_proxy(None)

        scholarly.use_proxy(proxy_generator, secondary_proxy_generator)

    def test_search_pubs_empty_publication(self):
        """
        Test that searching for an empty publication returns zero results
        """
        pubs = [p for p in scholarly.search_pubs('')]
        assert len(pubs) == 0

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
        assert 1 <= len(pubs)
        filled = scholarly.fill(pubs[0])
        cites = [c for c in scholarly.citedby(filled)]
        assert len(cites) == filled['num_citations']

    def test_search_pubs_citedby_id(self):
        """
        Test querying for citations by paper ID.

        The 'Machine-learned epidemiology' paper had 11 citations as of
        June 1, 2020.
        """
        # Machine-learned epidemiology: real-time detection of foodborne illness at scale
        publication_id = 2244396665447968936

        pubs = [p for p in scholarly.search_citedby(publication_id)]
        assert 11 <= len(pubs)

    def test_bibtex(self):
        """
        Test that we get the BiBTeX entry correctly
        """

        with open("testdata/test_bibtex_result.txt", "r") as f:
            expected_result = "".join(f.readlines())

        pub = scholarly.search_single_pub("A distribution-based clustering algorithm for mining in large "
                                          "spatial databases", filled=True)
        result = scholarly.bibtex(pub)
        assert result == expected_result

    def test_search_pubs(self):
        """
        As of May 12, 2020 there are at least 29 pubs that fit the search term:
        ["naive physics" stability "3d shape"].

        Check that the paper "Visual perception of the physical stability of asymmetric three-dimensional objects"
        is among them
        """
        pub = scholarly.search_single_pub("naive physics stability 3d shape")
        pubs = list(scholarly.search_pubs('"naive physics" stability "3d shape"'))
        # Check that the first entry in pubs is the same as pub.
        # Checking for quality holds for non-dict entries only.
        for key in {'author_id', 'pub_url', 'eprint_url', 'num_citations'}:
            assert pub[key] == pubs[0][key]
        for key in {'title', 'pub_year', 'venue'}:
            assert pub['bib'][key] == pubs[0]['bib'][key]
        assert 27 <= len(pubs)
        titles = [p['bib']['title'] for p in pubs]
        assert 'Visual perception of the physical stability of asymmetric three-dimensional objects' in titles

    def test_search_pubs_single_pub(self):
        """
        As of Jun 24, 2024 there are is only one pub that fits the search term:
        [Perception of physical stability and center of mass of 3D objects].

        Check that it returns a proper result and the total results for that search term is equal to 1.
        """
        pub = scholarly.search_single_pub("Perception of physical stability and center of mass of 3D objects")
        pubs = list(scholarly.search_pubs("Perception of physical stability and center of mass of 3D objects"))
        # Check that the first entry in pubs is the same as pub.
        # Checking for quality holds for non-dict entries only.
        for key in {'author_id', 'pub_url', 'num_citations'}:
            assert pub[key] == pubs[0][key]
        for key in {'title', 'pub_year', 'venue'}:
            assert pub['bib'][key] == pubs[0]['bib'][key]
        assert len(pubs) == 1

    def test_search_pubs_total_results(self):
        """
        As of September 16, 2021 there are 32 pubs that fit the search term:
        ["naive physics" stability "3d shape"], and 17'000 results that fit
        the search term ["WIEN2k Blaha"] and none for ["sdfsdf+24r+asdfasdf"].

        Check that the total results for that search term equals 32.
        """
        pubs = scholarly.search_pubs('"naive physics" stability "3d shape"')
        assert 32 <= pubs.total_results

        pubs = scholarly.search_pubs('WIEN2k Blaha')
        assert 10000 <= pubs.total_results

        pubs = scholarly.search_pubs('sdfsdf+24r+asdfasdf')
        assert pubs.total_results == 0

    def test_search_pubs_filling_publication_contents(self):
        '''
        This process  checks the process of filling a publication that is derived
         from the search publication snippets.
        '''
        query = 'Creating correct blur and its effect on accommodation'
        results = scholarly.search_pubs(query)
        pubs = [p for p in results]
        assert 1 <= len(pubs)
        f = scholarly.fill(pubs[0])
        assert f['bib']['author'] == u'Cholewiak, Steven A and Love, Gordon D and Banks, Martin S'
        assert f['author_id'] == ['4bahYMkAAAAJ', '3xJXtlwAAAAJ', 'Smr99uEAAAAJ']
        assert f['bib']['journal'] == u'Journal of Vision'
        assert f['bib']['number'] == '9'
        assert f['bib']['pages'] == u'1--1'
        assert f['bib']['publisher'] == u'The Association for Research in Vision and Ophthalmology'
        assert f['bib']['title'] == u'Creating correct blur and its effect on accommodation'
        assert f['pub_url'] == u'https://jov.arvojournals.org/article.aspx?articleid=2701817'
        assert f['eprint_url'] == u'https://jov.arvojournals.org/arvo/content_public/journal/jov/937491/i1534-7362-18-9-1.pdf'
        assert f['bib']['volume'] == '18'
        assert f['bib']['pub_year'] == u'2018'

    def test_related_articles_from_author(self):
        """
        Test that we obtain related articles to an article from an author
        """
        author = scholarly.search_author_id("ImhakoAAAAAJ")
        scholarly.fill(author, sections=['basics', 'publications'])
        pub = author['publications'][0]
        assert pub['bib']['title'] == 'Prospect theory: An analysis of decision under risk'
        assert pub['bib']['citation'] == 'Handbook of the fundamentals of financial decision making: Part I, 99-127, 2013'
        related_articles = scholarly.get_related_articles(pub)
        # Typically, the same publication is returned as the most related article
        same_article = next(related_articles)
        assert pub["pub_url"] == same_article["pub_url"]
        assert pub["eprint_url"] == same_article["eprint_url"]
        for key in {'title', 'pub_year'}:
            assert str(pub['bib'][key]) == (same_article['bib'][key])

        # These may change with time
        related_article = next(related_articles)
        assert related_article['bib']['title'] == 'Advances in prospect theory: Cumulative representation of uncertainty'
        assert related_article['bib']['pub_year'] == '1992'
        assert 18673 <= related_article['num_citations']
        assert "A Tversky" in related_article['bib']['author']

    def test_related_articles_from_publication(self):
        """
        Test that we obtain related articles to an article from a search
        """
        pub = scholarly.search_single_pub("Planck 2018 results-VI. Cosmological parameters")
        related_articles = scholarly.get_related_articles(pub)
        # Typically, the same publication is returned as the most related article
        same_article = next(related_articles)
        for key in {'author_id', 'pub_url', 'eprint_url', 'num_citations'}:
            assert pub[key] == same_article[key]
        for key in {'title', 'pub_year'}:
            assert pub['bib'][key] == same_article['bib'][key]

        # These may change with time
        related_article = next(related_articles)
        assert related_article['bib']['title'] == 'Large Magellanic Cloud Cepheid standards provide ' \
                         'a 1% foundation for the determination of the Hubble constant and stronger evidence ' \
                         'for physics beyond ΛCDM'
        assert related_article['bib']['pub_year'] == '2019'
        assert 1388 <= related_article['num_citations']
        assert "AG Riess" in related_article['bib']['author']

    def test_pubs_custom_url(self):
        """
        Test that we can use custom URLs for retrieving publication data
        """
        query_url = ('/scholar?as_q=&as_epq=&as_oq=SFDI+"modulated+imaging"&as_eq=&as_occt=any&as_sauthors=&'
                     'as_publication=&as_ylo=2005&as_yhi=2020&hl=en&as_sdt=0%2C31')
        pubs = scholarly.search_pubs_custom_url(query_url)
        pub = next(pubs)
        assert pub['bib']['title'] == 'Quantitation and mapping of tissue optical properties using modulated imaging'
        assert set(pub['author_id']) == {'V-ab9U4AAAAJ', '4k-k6SEAAAAJ', 'GLm-SaQAAAAJ'}
        assert pub['bib']['pub_year'] == '2009'
        assert 581 <= pub['num_citations']

    def check_citedby_1k(self, pub):
        """A common checking method to check
        """
        original_citation_count = pub["num_citations"]
        # Trigger a different code path
        if original_citation_count <= 1000:
            pub["num_citations"] = 1001
        citations = scholarly.citedby(pub)
        citation_list = list(citations)
        assert len(citation_list) == original_citation_count
        return citation_list

    def test_citedby_1k_citations(self):
        """Test that scholarly can fetch 1000+ citations from an author
        """
        author = scholarly.search_author_id('QoX9bu8AAAAJ')
        scholarly.fill(author, sections=['publications'])
        pub = [_p for _p in  author['publications'] if _p["author_pub_id"]=="QoX9bu8AAAAJ:L8Ckcad2t8MC"][0]
        scholarly.fill(pub)
        citation_list = self.check_citedby_1k(pub)

        yearwise_counter = Counter([c["bib"]["pub_year"] for c in citation_list])
        for year, count in pub["cites_per_year"].items():
            assert yearwise_counter.get(str(year)) == 0

    def test_citedby_1k_scholar(self):
        """Test that scholarly can fetch 1000+ citations from a pub search.
        """
        title = "Persistent entanglement in a class of eigenstates of quantum Heisenberg spin glasses"
        pubs = scholarly.search_pubs(title)
        pub = next(pubs)
        self.check_citedby_1k(pub)

    def test_citedby(self):
        """Test that we can search citations of a paper from author's profile.
        """
        # Retrieve the author's data, fill-in, and print
        search_query = scholarly.search_author('Steven A Cholewiak')
        author = scholarly.fill(next(search_query))
        pub = scholarly.fill(author['publications'][0])

        # Which papers cited that publication?
        top10_citations = [citation for num, citation in enumerate(scholarly.citedby(pub)) if num<10]
        assert len(top10_citations) == 10
