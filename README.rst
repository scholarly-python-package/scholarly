scholarly
=========

scholarly is a module that allows you to retrieve author and publication
information from `Google Scholar <https://scholar.google.com>`__ in a
friendly, Pythonic way.

Usage
-----

Because ``scholarly`` does not use an official API, no key is required.
Simply:

.. code:: python

    import scholarly

    print(next(scholarly.search_author('Steven A. Cholewiak')))

Methods
~~~~~~~

-  ``search_author`` -- Search for an author by name and return a
   generator of Author objects.

.. code:: python

        >>> search_query = scholarly.search_author('Manish Singh, Rutgers')
        >>> print(next(search_query))
        {'_filled': False,
         'affiliation': u'Rutgers University, New Brunswick, NJ',
         'citedby': 2379,
         'email': u'@ruccs.rutgers.edu',
         'id': u'9XRvM88AAAAJ',
         'interests': [u'Human perception',
                       u'Computational Vision',
                       u'Cognitive Science'],
         'name': u'Manish Singh',
         'url_citations': '/citations?user=9XRvM88AAAAJ&hl=en',
         'url_picture': u'/citations/images/avatar_scholar_150.jpg'}

-  ``search_keyword`` -- Search by keyword and return a generator of
   Author objects.

.. code:: python

        >>> search_query = scholarly.search_keyword('Haptics')
        >>> print(next(search_query))
        {'_filled': False,
         'affiliation': u'Lamar University',
         'citedby': 20267,
         'email': u'@lamar.edu',
         'id': u'N2ab6CAAAAAJ',
         'interests': [u'CAD/CAM',
                       u'Haptics',
                       u'Medical Simulation',
                       u'GPU computing',
                       u'evolutionary computing'],
         'name': u'Weihang Zhu',
         'url_citations': '/citations?user=N2ab6CAAAAAJ&hl=en',
         'url_picture': u'/citations/images/avatar_scholar_150.jpg'}

-  ``search_pubs_query`` -- Search for articles/publications and return
   generator of Publication objects.

.. code:: python

        >>> search_query = scholarly.search_pubs_query('Perception of physical stability and center of mass of 3D objects')
        >>> print(next(search_query))
        {'_filled': False,
         'bib': {'abstract': u'Humans can judge from vision alone whether an object is physically stable or not. Such judgments allow observers to predict the physical behavior of objects, and hence to guide their motor actions. We investigated the visual estimation of physical stability of 3-D  ...',
                 'author': u'SA Cholewiak and RW Fleming and M Singh',
                 'eprint': u'http://www.journalofvision.org/content/15/2/13.full',
                 'title': u'Perception of physical stability and center of mass of 3-D objects',
                 'url': u'http://www.journalofvision.org/content/15/2/13.short'},
         'source': 'scholar',
         'url_scholarbib': u'/scholar.bib?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=citation&hl=en&ct=citation&cd=0'}

Example
~~~~~~~

Here's a quick example demonstrating how to retrieve an author's profile
then retrieve the titles of the papers that cite his most popular
(cited) paper.

.. code:: python

        >>> # Retrieve the author's data, fill-in, and print
        >>> search_query = scholarly.search_author('Steven A Cholewiak')
        >>> author = next(search_query).fill()
        >>> print author

        >>> # Print the titles of the author's publications
        >>> print [pub.bib['title'] for pub in author.publications]

        >>> # Take a closer look at the first publication
        >>> pub = author.publications[0].fill()
        >>> print pub

        >>> # Which papers cited that publication?
        >>> print [citation.bib['title'] for citation in pub.citedby()]

Installation
------------

Use ``pip`` to install from pypi:

::

    pip install scholarly

or ``pip`` to install from github:

::

    pip install git+https://github.com/OrganicIrradiation/scholarly.git

or clone the package using git:

::

    git clone https://github.com/OrganicIrradiation/scholarly.git

Requirements
------------

Requires `arrow <http://crsmithdev.com/arrow/>`__, `Beautiful
Soup <https://pypi.python.org/pypi/beautifulsoup4/>`__,
`bibtexparser <https://pypi.python.org/pypi/bibtexparser/>`__, and
`requests[security] <https://pypi.python.org/pypi/requests/>`__.

Changes
-------

Note that because of the nature of web scraping, this project will be in
**perpetual alpha**.

v0.2
~~~~

-  Python 2/3 compatibility. No longer using datetime-util and moved the
   datetime operations to arrow. Now using wheel format.

v0.1.5
~~~~~~

-  Exactly the same as v0.1.5, but had to bump the version because of a
   version mistakenly pushed to pypi that had a bad tarball url.

v0.1.4
~~~~~~

-  Moved over to requests. When Google requests a CAPTCHA, print a URL
   to the image (rehosted on `postimage.org <http://postimage.org>`__),
   and have the user confirm that this is being run interactively. Also
   explicitly request the 'html.parser' for BeautifulSoup. Includes a
   few small updates to test.py tests to account for updated citation
   contents and updates to the README. And finally, the pypi install
   should also now include requests[security].

v0.1.3
~~~~~~

-  Raise an exception when we receive a Bot Check. Reorganized test.py
   alphabetically and updated its test cases. Reorganized README. Added
   python-dateutil as installation requirement, for some reason it was
   accidentally omitted.

v0.1.2
~~~~~~

-  Now request HTTPS connection rather than HTTP and update test.py to
   account for a new "Zucker". Also added information for the v0.1.1
   revision.

v0.1.1
~~~~~~

-  Fixed an issue with multi-page Author results, author entries with no
   citations (which are rare, but do occur), and added some tests using
   unittest.

v0.1
~~~~

-  Initial release.

License
-------

The original code that this project was forked from was released by
`Bello Chalmers <https://github.com/lbello/chalmers-web>`__ under a
`WTFPL <http://www.wtfpl.net/>`__ license. In keeping with this
mentality, all code is released under the
`Unlicense <http://unlicense.org/>`__.
