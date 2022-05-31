import sys

from enum import Enum
from typing import List, Dict

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class PublicationSource(str, Enum):
    '''
    Defines the source of the publication. In general, a publication
    on Google Scholar has two forms:
    * Appearing as a PUBLICATION SNIPPET and
    * Appearing as a paper in an AUTHOR PAGE

    ------------

    "PUBLICATION SEARCH SNIPPET".
    This form captures the publication  when it appears as a "snippet" in
    the context of the resuls of a publication search. For example:

    Publication search: https://scholar.google.com/scholar?hl=en&q=adaptive+fraud+detection&btnG=&as_sdt=0%2C33

    The entries appear under the <div class = "gs_r gs_or gs_scl"> tags
    Each entry has a data-cid attribute (e.g., data-cid="pthm1bWT96oJ")

    The same type of results will also appear when someome searches
    using the "cited by", "related articles", and "all XX versions" links
    that appear under the publication snippet.

    "Cited By" link: https://scholar.google.com/scholar?cites=12319477714873931942&as_sdt=5,33&sciodt=0,33&hl=en

    "Related Articles" link: https://scholar.google.com/scholar?q=related:pthm1bWT96oJ:scholar.google.com/&scioq=adaptive+fraud+detection&hl=en&as_sdt=0,33

    "All versions" link: https://scholar.google.com/scholar?cluster=12319477714873931942&hl=en&as_sdt=0,33

    The snippet version of these publications contain the information that appears in the results.
    Often, the snippet version will miss authors, will have an abbreviated name for the venue, and so on.

    We can fill these snippets by clicking on the "Cite" button" and get back the MLA/APA/Chicago/...
    citations forms, PLUS links for BibTeX, EndNote, RefMan, and RefWorks.

    ------------
    "AUTHOR PUBLICATION ENTRY"

    We also have publications that appear in the "author pages" of Google Scholar.
    These publications are often a set of publications "merged" together.

    The snippet version of these publications conains the title of the publication,
    a subset of the authors, the (sometimes truncated) venue, and the year of the publication
    and the number of papers that cite the publication.

    The snippet entries appear under the <tr class="gsc_a_tr"> entries in the main page of the author.

    To fill in the publication, we open the "detailed view" of the paper

    Detailed view page: https://scholar.google.com/citations?view_op=view_citation&hl=en&citation_for_view=-Km63D4AAAAJ:d1gkVwhDpl0C
    '''
    PUBLICATION_SEARCH_SNIPPET = "PUBLICATION_SEARCH_SNIPPET"
    AUTHOR_PUBLICATION_ENTRY = "AUTHOR_PUBLICATION_ENTRY"
    JOURNAL_CITATION_LIST = "JOURNAL_CITATION_LIST"


class AuthorSource(str, Enum):
    '''
    Defines the source of the HTML that will be parsed.

    Author page: https://scholar.google.com/citations?hl=en&user=yxUduqMAAAAJ

    Search authors: https://scholar.google.com/citations?view_op=search_authors&hl=en&mauthors=jordan&btnG=

    Coauthors: From the list of co-authors from an Author page
    '''
    AUTHOR_PROFILE_PAGE = "AUTHOR_PROFILE_PAGE"
    SEARCH_AUTHOR_SNIPPETS = "SEARCH_AUTHOR_SNIPPETS"
    CO_AUTHORS_LIST = "CO_AUTHORS_LIST"


class ProxyMode(str, Enum):
    """
    Defines the different types supported.
    """
    FREE_PROXIES = "FREE_PROXIES"
    SCRAPERAPI = "SCRAPERAPI"
    LUMINATI = "LUMINATI"
    SINGLEPROXY = "SINGLEPROXY"
    # Deprecated:
    TOR_EXTERNAL = "TOR_EXTERNAL"
    TOR_INTERNAL = "TOR_INTERNAL"


''' Lightweight Data Structure to keep distribution of citations of the years '''
CitesPerYear = Dict[int, int]


''' Lightweight Data Structure to hold the numbers articles available or
    not available publicly according to funding mandates
'''
PublicAccess = TypedDict('PublicAccess', {"available": int, "not_available": int})


class BibEntry(TypedDict, total=False):
    """
    :class:`BibEntry <BibEntry>` The bibliographic entry for a publication
            (When source is not specified, the field is present in all sources)

    :param pub_type: the type of entry for this bib (for example 'article') (source: PUBLICATION_SEARCH_SNIPPET)
    :param bib_id: bib entry id (source: PUBLICATION_SEARCH_SNIPPET)
    :param abstract: description of the publication
    :param title: title of the publication
    :param author: list of author the author names that contributed to this publication
    :param pub_year: the year the publication was first published
    :param venue: the venue of the publication (source: PUBLICATION_SEARCH_SNIPPET)
    :param journal: Journal Name
    :param volume: number of years a publication has been circulated
    :param number: NA number of a publication
    :param pages: range of pages
    :param publisher: The publisher's name
    :param citation: Formatted citation string, usually containing journal name, volume and page numbers (source: AUTHOR_PUBLICATION_ENTRY)
    :param pub_url: url of the website providing the publication
    """
    pub_type: str
    bib_id: str
    abstract: str
    title: str
    author: str
    pub_year: str
    venue: str
    journal: str
    volume: str
    number: str
    pages: str
    publisher: str
    citation: str


class Mandate(TypedDict, total=False):
    """
    :class:`Mandate <Mandate>` A funding mandate for a given year

    :param agency: name of the funding agency
    :param url_policy: url of the policy for this mandate
    :param url_policy_cached: url of the policy cached by Google Scholar
    :param effective_date: date from which the policy is effective
    :param embargo: period within which the article must be publicly available
    :param acknowledgement: text in the paper acknowledging the funding
    :param grant: grant ID that supported this work
    """
    agency: str
    url_policy: str
    url_policy_cached: str
    effective_date: str
    embargo: str
    acknowledgement: str
    grant: str


class Publication(TypedDict, total=False):
    """
    :class:`Publication <Publication>` object used to represent a publication entry on Google Scholar.
           (When source is not specified, the field is present in all sources)

    :param BibEntryCitation: contains additional information about the publication
    :param gsrank: position of the publication in the query (source: PUBLICATION_SEARCH_SNIPPET)
    :param author_id: list of the corresponding author ids of the authors that contributed to the Publication (source: PUBLICATION_SEARCH_SNIPPET)
    :param num_citations: number of citations of this Publication
    :param cites_id: This corresponds to a "single" publication on Google Scholar. Used in the web search
                       request to return all the papers that cite the publication. If cites_id =
                       16766804411681372720 then:
                       https://scholar.google.com/scholar?cites=<cites_id>&hl=en
                       If the publication comes from a "merged" list of papers from an authors page,
                       the "citedby_id" will be a comma-separated list of values.
                       It is also used to return the "cluster" of all the different versions of the paper.
                       https://scholar.google.com/scholar?cluster=16766804411681372720&hl=en
                       (source: AUTHOR_PUBLICATION_ENTRY)
    :param citedby_url: This corresponds to a "single" publication on Google Scholar. Used in the web search
                       request to return all the papers that cite the publication.
                       https://scholar.google.com/scholar?cites=16766804411681372720hl=en
                       If the publication comes from a "merged" list of papers from an authors page,
                       the "citedby_url" will be a comma-separated list of values.
                       It is also used to return the "cluster" of all the different versions of the paper.
                       https://scholar.google.com/scholar?cluster=16766804411681372720&hl=en
    :param cites_per_year: a dictionay containing the number of citations per year for this Publication
                           (source: AUTHOR_PUBLICATION_ENTRY)
    :param eprint_url: digital version of the Publication. Usually it is a pdf.
    :param pub_url: url of the website providing the publication
    :param author_pub_id: The id of the paper on Google Scholar from an author page. Comes from the
                          parameter "citation_for_view=PA9La6oAAAAJ:YsMSGLbcyi4C". It combines the
                          author id, together with a publication id. It may corresponds to a merging
                          of multiple publications, and therefore may have multiple "citedby_id"
                          values.
                          (source: AUTHOR_PUBLICATION_ENTRY)
    :param public_access: Boolean corresponding to whether the article is available or not in accordance with public access mandates.
    :param mandates: List of mandates with funding information and public access requirements.
    :param url_related_articles: the url containing link for related articles of a publication (needs fill() for AUTHOR_PUBLICATION_ENTRIES)
    :param url_add_sclib: (source: PUBLICATION_SEARCH_SNIPPET)
    :param url_scholarbib: the url containing links for
                           the BibTeX entry, EndNote, RefMan and RefWorks (source: PUBLICATION_SEARCH_SNIPPET)
    :param filled: whether the publication is fully filled or not
    :param source: The source of the publication entry
    :param container_type: Used from the source code to identify if this container object
                           is an Author or a Publication object.
    """

    bib: BibEntry
    gsrank: int
    author_id: List[str]
    num_citations: int
    cites_id: List[str]
    citedby_url: str
    cites_per_year: CitesPerYear
    author_pub_id: str
    public_access: bool
    mandates: List[Mandate]
    eprint_url: str
    pub_url: str
    url_add_sclib: str
    url_related_articles: str
    url_scholarbib: str
    filled: bool
    source: PublicationSource
    container_type: str

class Author(TypedDict, total=False):
    """
    :class:`Author <Author>` object used to represent an author entry on Google Scholar.
           (When source is not specified, the field is present in all sources)

    :param scholar_id: The id of the author on Google Scholar
    :param name: The name of the author
    :param affiliation: The affiliation of the author
    :param organization: A unique ID of the organization (source: AUTHOR_PROFILE_PAGE)
    :param email_domain: The email domain of the author (source: SEARCH_AUTHOR_SNIPPETS, AUTHOR_PROFILE_PAGE)
    :param url_picture: The URL for the picture of the author
    :param homepage: URL of the homepage of the author
    :param citedby: The number of citations to all publications. (source: SEARCH_AUTHOR_SNIPPETS)
    :param filled: The list of sections filled out of the total set of sections that can be filled
    :param interests: Fields of interest of this Author (sources: SEARCH_AUTHOR_SNIPPETS, AUTHOR_PROFILE_PAGE)
    :param citedby5y: The number of new citations in the last 5 years to all publications. (source: SEARCH_AUTHOR_SNIPPETS)
    :param hindex: The h-index is the largest number h such that h publications have at least h citations. (source: SEARCH_AUTHOR_SNIPPETS)
    :param hindex5y: The largest number h such that h publications have at least h new citations in the last 5 years. (source: SEARCH_AUTHOR_SNIPPETS)
    :param i10index: This is the number of publications with at least 10 citations.  (source: SEARCH_AUTHOR_SNIPPETS)
    :param i10index5y: The number of publications that have received at least 10 new citations in the last 5 years. (source: SEARCH_AUTHOR_SNIPPETS)
    :param cites_per_year: Breakdown of the number of citations to all publications over the years (source: SEARCH_AUTHOR_SNIPPETS)
    :param public_access: Number of articles that are available and not available in accordance with public access mandates. (source: SEARCH_AUTHOR_SNIPPETS, AUTHOR_PROFILE_PAGE)
    :param publications: A list of publications objects. (source: SEARCH_AUTHOR_SNIPPETS)
    :param coauthors: A list of coauthors (list of Author objects) (source: SEARCH_AUTHOR_SNIPPETS)
    :param container_type: Used from the source code to identify if this container object
                           is an Author or a Publication object.
    :param source: The place where the author information are derived
    """

    scholar_id: str
    name: str
    affiliation: str
    organization: int
    email_domain: str
    url_picture: str
    homepage: str
    citedby: int
    filled: List[str]
    interests: List[str]
    citedby5y: int
    hindex: int
    hindex5y: int
    i10index: int
    i10index5y: int
    cites_per_year: CitesPerYear
    public_access: PublicAccess
    publications: List[Publication]
    coauthors: List # List of authors. No self dict functionality available
    container_type: str
    source: AuthorSource

class Journal(TypedDict, total=False):
    """
    :class:`Journal <Journal>` object used to represent a journal entry on Google Scholar.
           (When source is not specified, the field is present in all sources)


    :param name: The name of the journal
    :param h5-index: h5-index is the h-index for articles published in the journal during the last 5 complete years.
    :param h5-median: h5-median for a publication is the median number of citations for the articles that make up its h5-index.
    :param url_citations: The URL for the cached citations page of the journal
    :param comment: String representing the ranking for the journal in various categories

    """

    name: str
    h5_index: int
    h5_median: int
    url_citations: str
    comment: str
