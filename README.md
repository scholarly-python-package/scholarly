scholarly.py
===========

scholarly.py is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

Changes
-------

Note that because of the nature of web scraping, this project will be in **perpetual alpha**.

### v0.1

* Initial release.

Requirements
------------

Requires [bibtexparser](https://pypi.python.org/pypi/bibtexparser/) and [Beautiful Soup](https://pypi.python.org/pypi/beautifulsoup4/).


Installation
------------
Use `pip`:

    pip install scholarly

Or clone the package:

    git clone https://github.com/OrganicIrradiation/scholarly.git


Usage
-----
Because `scholarly` does not use an official API, no key is required. Simply:

```python
import scholarly

print scholarly.search_author('Steven A. Cholewiak').next()
```

### Methods
* `search_author` -- Search for an author by name and return a generator of Author objects.

```python
    search_query = scholarly.search_author('Manish Singh')
    print search_query.next()
```

```python
    {'_filled': False,
     'affiliation': u'Rutgers University, New Brunswick, NJ',
     'citedby': 2179,
     'email': u'@ruccs.rutgers.edu',
     'id': '9XRvM88AAAAJ',
     'interests': [u'Human perception',
                   u'Computational Vision',
                   u'Cognitive Science'],
     'name': u'Manish Singh',
     'url_citations': '/citations?user=9XRvM88AAAAJ&hl=en',
     'url_picture': '/citations/images/avatar_scholar_150.jpg'}
```

* `search_keyword` -- Search by keyword and return a generator of Author objects.

```python
    search_query = scholarly.search_keyword('Haptics')
    print search_query.next()
```

```python
    {'_filled': False,
     'affiliation': u'Stanford University',
     'citedby': 17867,
     'email': u'@cs.stanford.edu',
     'id': '4arkOLcAAAAJ',
     'interests': [u'Robotics', u'Haptics', u'Human Motion'],
     'name': u'Oussama Khatib',
     'url_citations': '/citations?user=4arkOLcAAAAJ&hl=en',
     'url_picture': '/citations/images/avatar_scholar_150.jpg'}
```

* `search_pubs_query` -- Search for articles/publications and return generator of Publication objects.

```python
    search_query = scholarly.search_pubs_query('The perception of physical stability of 3d objects The role of parts')
    print search_query.next()
```

```python
    {'_filled': False,
     'bib': {'abstract': u'Research on 3D shape has focused largely on the perception of local geometric properties, such as surface depth, orientation, or curvature. Relatively little is known about how the visual system organizes local measurements into global shape representations.  ...',
             'author': u'SA Cholewiak and M Singh and R Fleming\u2026',
             'title': u'The perception of physical stability of 3d objects: The role of parts',
             'url': 'http://www.journalofvision.org/content/10/7/77.short'},
     'id_scholarcitedby': '8373403526432059892',
     'source': 'scholar',
     'url_scholarbib': '/scholar.bib?q=info:9HH8oSRONHQJ:scholar.google.com/&output=citation&hl=en&ct=citation&cd=0'}
```


### Example
Here's a quick example deomonstrating how to retrieve an author's profile then retreive the titles of the papers that cite his most popular (cited) paper.

```python
    # Retrieve the author's data, fill-in, and print
    search_query = scholarly.search_author('Steven A Cholewiak')
    author = search_query.next().fill()
    print author

    # Print the titles of the author's publications
    print [pub.bib['title'] for pub in author.publications]

    # Take a closer look at the first publication
    pub = author.publications[0].fill()
    print pub

    # Which papers cited that publication?
    print [citation.bib['title'] for citation in pub.citedby()]
```


License
-------

The original code that this project was forked from was released by [Bello Chalmers](https://github.com/lbello/chalmers-web) under a [WTFPL](http://www.wtfpl.net/) license. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).