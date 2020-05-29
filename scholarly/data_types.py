import sys

from enum import Enum
from typing import List

if sys.version_info >= (3, 8):
    from typing import TypedDict 
else:
    from typing_extensions import TypedDict


class PublicationSource(Enum):
    '''
    Defines the source of the publication
    
    Publication search: https://scholar.google.com/scholar?hl=en&as_sdt=0%2C33&q=adaptive+fraud+detection&btnG=
    
    Author page: https://scholar.google.com/citations?view_op=view_citation&hl=en&citation_for_view=-Km63D4AAAAJ:d1gkVwhDpl0C
    '''
    PUB_SEARCH = 1
    AUTHOR_PAGE = 2
    
class AuthorSource(Enum):
    '''
    Defines the source of the HTML that will be parsed.
    
    Author page: https://scholar.google.com/citations?hl=en&user=yxUduqMAAAAJ
    
    Search authors: https://scholar.google.com/citations?view_op=search_authors&hl=en&mauthors=jordan&btnG=
    
    Coauthors: From the list of co-authors from an Author page
    '''
    AUTHOR_PAGE = 1
    SEARCH_AUTHOR = 2
    COAUTHORS = 3
    

class BibEntry(TypedDict):
    '''
    The bibliographic entry for a publication
    '''
    title: str
    authors: str
    abstract: str
    pub_year: int
    pub_month: int
    venue: str
    pub_type: str # journal, conference, chapter, book, thesis, patent, course case, other ...
    volume: str
    issue: str
    number: str
    pages: str
    publisher: str  

''' Lightweight Data Structure to keep distribution of citations of the years '''
CitesPerYear = TypedDict("CitesPerYear", year=int, citations=int)        
        
class Publication(TypedDict):
    """
    :class:`Publication <Publication>` object used to represent a publication entry on Google Scholar.
    
    :param author_pub_id: The id of the paper on Google Scholar from an author page. Comes from the 
                          parameter "citation_for_view=PA9La6oAAAAJ:YsMSGLbcyi4C". It combines the 
                          author id, together with a publication id. It may corresponds to a merging
                          of multiple publications, and therefore may have multiple "citedby_id" 
                          values.
    :param citedby_id: This corresponds to a "single" publication on Google Scholar. Used in the web search
                       request to return all the papers that cite the publication. 
                       https://scholar.google.com/scholar?cites=16766804411681372720hl=en
                       If the publication comes from a "merged" list of papers from an authors page, 
                       the "citedby_id" will be a comma-separated list of values. 
                       It is also used to return the "cluster" of all the different versions of the paper.
                       https://scholar.google.com/scholar?cluster=16766804411681372720&hl=en
    :param related_id: Used to return the related papers for the given publication                       
    :param source: The source of the publication entry
    :param bib: The bibliographic entry for the page
    :param total_citations: The total number of publication that cite this publication
    :param cites_per_year: The number of citations broken down by year
    """
    author_pub_id: str
    cited_by_id: str
    related_id: str
    source: PublicationSource
    bib: BibEntry
    total_citations: int
    cites_per_year: CitesPerYear
    

    
class Author(TypedDict):
    """
    :class:`Author <Author>` object used to represent an author entry on Google Scholar.
    
    :param scholar_id: The id of the author on Google Schoar
    :param name: The name of the author
    :param affiliation: The affiliation of the author
    :param email_domain: The email domain of the author
    :param url_picture: The URL for the picture of the author
    :param citedby: The number of citations to all publications.
    :param citedby5y: The number of new citations in the last 5 years to all publications.
    :param hindex: The h-index is the largest number h such that h publications have at least h citations
    :param hindex5y: The largest number h such that h publications have at least h new citations in the last 5 years
    :param i10index: This is the number of publications with at least 10 citations.
    :param i10index5y: The number of publications that have received at least 10 new citations in the last 5 years. 
    :param cites_per_year: Breakdown of the number of citations to all publications over the years
    :param publications: A list of publications objects
    :param coauthors: A list of coauthors (list of Author objects)
    """
    scholar_id: str
    name: str
    affiliation: str
    email_domain: str
    url_picture: str
    citedby: int
    citedby5y: int
    hindex: int
    hindex5y: int
    i10index: int
    i10index5y: int
    cites_per_year: CitesPerYear
    publications: List[Publication]
    coauthors: List
