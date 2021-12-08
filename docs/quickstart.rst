Quickstart
==========

Installation
------------

Use ``pip`` to install from pypi:

.. code:: bash

    pip3 install scholarly

or use ``pip`` to install from github:

.. code:: bash

    pip install git+https://github.com/scholarly-python-package/scholarly.git

or clone the package using git:

.. code:: bash

    git clone https://github.com/scholarly-python-package/scholarly.git


Usage
-----

Because ``scholarly`` does not use an official API, no key is required.
Simply:

.. code:: python

    from scholarly import scholarly

    print(next(scholarly.search_author('Steven A. Cholewiak')))

Example
-------

Here's a quick example demonstrating how to retrieve an author's profile
then retrieve the titles of the papers that cite his most popular
(cited) paper.

.. code:: python

    from scholarly import scholarly

    # Retrieve the author's data, fill-in, and print
    search_query = scholarly.search_author('Steven A Cholewiak')
    author = scholarly.fill(next(search_query))
    print(author)

    # Print the titles of the author's publications
    print([pub['bib']['title'] for pub in author['publications']])

    # Take a closer look at the first publication
    pub = scholarly.fill(author['publications'][0])
    print(pub)

    # Which papers cited that publication?
    print([citation['bib']['title'] for citation in scholarly.citedby(pub)])

Methods for ``scholar``
-----------------------

``search_author``
^^^^^^^^^^^^^^^^^

Search for an author by name and return a generator of Author objects.
######################################################################
.. code:: python

    >>> search_query = scholarly.search_author('Marty Banks, Berkeley')
    >>> scholarly.pprint(next(search_query))
    {'affiliation': 'Professor of Vision Science, UC Berkeley',
     'citedby': 21074,
     'email_domain': '@berkeley.edu',
     'filled': False,
     'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
     'name': 'Martin Banks',
     'scholar_id': 'Smr99uEAAAAJ',
     'source': 'SEARCH_AUTHOR_SNIPPETS',
     'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=Smr99uEAAAAJ'}

``search_author_id``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Search for an author by the id visible in the url of an Authors profile.
########################################################################

.. code:: python

    >>> author = scholarly.search_author_id('Smr99uEAAAAJ')
    >>> scholarly.pprint(author)
    {'affiliation': 'Professor of Vision Science, UC Berkeley',
     'email_domain': '@berkeley.edu',
     'filled': False,
     'homepage': 'http://bankslab.berkeley.edu/',
     'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
     'name': 'Martin Banks',
     'organization': 11816294095661060495,
     'scholar_id': 'Smr99uEAAAAJ',
     'source': 'AUTHOR_PROFILE_PAGE'}

``search_author_by_organization``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Search for authors by organization ID.
########################################################################

.. code:: python

    >>> scholarly.search_org('Princeton University')
    [{'Organization': 'Princeton University', 'id': '4836318610601440500'}]

    >>> search_query = scholarly.search_author_by_organization(4836318610601440500)
    >>> author = next(search_query)
    >>> scholarly.pprint(author)
        {'affiliation': 'Princeton University (Emeritus)',
         'citedby': 438891,
         'email_domain': '@princeton.edu',
         'filled': False,
         'interests': ['Daniel Kahneman'],
         'name': 'Daniel Kahneman',
         'scholar_id': 'ImhakoAAAAAJ',
         'source': 'SEARCH_AUTHOR_SNIPPETS',
         'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=ImhakoAAAAAJ'}

``search_keyword``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Search by keyword and return a generator of Author objects.
###########################################################

.. code:: python

    >>> search_query = scholarly.search_keyword('Haptics')
    >>> scholarly.pprint(next(search_query))
    {'affiliation': 'Postdoctoral research assistant, University of Bremen',
     'citedby': 56666,
     'email_domain': '@collision-detection.com',
     'filled': False,
     'interests': ['Computer Graphics',
                   'Collision Detection',
                   'Haptics',
                   'Geometric Data Structures'],
     'name': 'Rene Weller',
     'scholar_id': 'lHrs3Y4AAAAJ',
     'source': 'SEARCH_AUTHOR_SNIPPETS',
     'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=lHrs3Y4AAAAJ'}

``search_pubs``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Search for articles/publications and return generator of Publication objects.
#############################################################################

.. code:: python

    >>> search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
    >>> scholarly.pprint(next(search_query))
    {'author_id': ['4bahYMkAAAAJ', 'ruUKktgAAAAJ', ''],
     'bib': {'abstract': 'Humans can judge from vision alone whether an object is '
                         'physically stable or not. Such judgments allow observers '
                         'to predict the physical behavior of objects, and hence '
                         'to guide their motor actions. We investigated the visual '
                         'estimation of physical stability of 3-D objects (shown '
                         'in stereoscopically viewed rendered scenes) and how it '
                         'relates to visual estimates of their center of mass '
                         '(COM). In Experiment 1, observers viewed an object near '
                         'the edge of a table and adjusted its tilt to the '
                         'perceived critical angle, ie, the tilt angle at which '
                         'the object',
             'author': ['SA Cholewiak', 'RW Fleming', 'M Singh'],
             'pub_year': '2015',
             'title': 'Perception of physical stability and center of mass of 3-D '
                      'objects',
             'venue': 'Journal of vision'},
     'citedby_url': '/scholar?cites=15736880631888070187&as_sdt=5,33&sciodt=0,33&hl=en',
     'eprint_url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
     'filled': False,
     'gsrank': 1,
     'num_citations': 23,
     'pub_url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
     'source': 'PUBLICATION_SEARCH_SNIPPET',
     'url_add_sclib': '/citations?hl=en&xsrf=&continue=/scholar%3Fq%3DPerception%2Bof%2Bphysical%2Bstability%2Band%2Bcenter%2Bof%2Bmass%2Bof%2B3D%2Bobjects%26hl%3Den%26as_sdt%3D0,33&citilm=1&json=&update_op=library_add&info=K8ZpoI6hZNoJ&ei=kiahX9qWNs60mAHIspTIBA',
     'url_scholarbib': '/scholar?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=cite&scirp=0&hl=en'}

Please note that the ``author_id`` array is positionally matching with
the ``author`` array. You can use the ``author_id`` to get further
details about the author using the ``search_author_id`` method.

``fill``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Fill the Author and Publications container objects with additional information.
###############################################################################

About the Publications:
'''''''''''''''''''''''

By default, scholarly returns only a lightly filled object for
publication, to avoid overloading Google Scholar. If necessary to get
more information for the publication object, we call this method.

About the Authors:
''''''''''''''''''

If the container object passed to this method is an Author, the sections
desired to be filled can be selected to populate the author with
information from their profile, via the ``sections`` parameter.

The optional ``sections`` parameter takes a list of the portions of
author information to fill, as follows:

-  ``'basics'`` = name, affiliation, and interests;
-  ``'indices'`` = h-index, i10-index, and 5-year analogues;
-  ``'counts'`` = number of citations per year;
-  ``'coauthors'`` = co-authors;
-  ``'publications'`` = publications;
-  ``'public_access'`` = public_access;
-  ``'[]'`` = all of the above (this is the default)

.. code:: python

    >>> search_query = scholarly.search_author('Steven A Cholewiak')
    >>> author = next(search_query)
    >>> scholarly.pprint(scholarly.fill(author, sections=['basics', 'indices', 'coauthors']))
    {'affiliation': 'Vision Scientist',
     'citedby': 304,
     'citedby5y': 226,
     'coauthors': [{'affiliation': 'Kurt Koffka Professor of Experimental '
                                   'Psychology, University of Giessen',
                    'filled': False,
                    'name': 'Roland Fleming',
                    'scholar_id': 'ruUKktgAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Professor of Vision Science, UC Berkeley',
                    'filled': False,
                    'name': 'Martin Banks',
                    'scholar_id': 'Smr99uEAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Durham University, Computer Science & Physics',
                    'filled': False,
                    'name': 'Gordon D. Love',
                    'scholar_id': '3xJXtlwAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Professor of ECE, Purdue University',
                    'filled': False,
                    'name': 'Hong Z Tan',
                    'scholar_id': 'OiVOAHMAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Deepmind',
                    'filled': False,
                    'name': 'Ari Weinstein',
                    'scholar_id': 'MnUboHYAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': "Brigham and Women's Hospital/Harvard Medical "
                                   'School',
                    'filled': False,
                    'name': 'Chia-Chien Wu',
                    'scholar_id': 'dqokykoAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Professor of Psychology and Cognitive Science, '
                                   'Rutgers University',
                    'filled': False,
                    'name': 'Jacob Feldman',
                    'scholar_id': 'KoJrMIAAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Research Scientist at Google Research, PhD '
                                   'Student at UC Berkeley',
                    'filled': False,
                    'name': 'Pratul Srinivasan',
                    'scholar_id': 'aYyDsZ0AAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Formerly: Indiana University, Rutgers '
                                   'University, University of Pennsylvania',
                    'filled': False,
                    'name': 'Peter C. Pantelis',
                    'scholar_id': 'FoVvIK0AAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Professor in Computer Science, University of '
                                   'California, Berkeley',
                    'filled': False,
                    'name': 'Ren Ng',
                    'scholar_id': '6H0mhLUAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Yale University',
                    'filled': False,
                    'name': 'Steven W Zucker',
                    'scholar_id': 'rNTIQXYAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Brown University',
                    'filled': False,
                    'name': 'Ben Kunsberg',
                    'scholar_id': 'JPZWLKQAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Rutgers University, New Brunswick, NJ',
                    'filled': False,
                    'name': 'Manish Singh',
                    'scholar_id': '9XRvM88AAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Silicon Valley Professor of ECE, Purdue '
                                   'University',
                    'filled': False,
                    'name': 'David S. Ebert',
                    'scholar_id': 'fD3JviYAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Clinical Director, Neurolens Inc.,',
                    'filled': False,
                    'name': 'Vivek Labhishetty',
                    'scholar_id': 'tD7OGTQAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'MIT',
                    'filled': False,
                    'name': 'Joshua B. Tenenbaum',
                    'scholar_id': 'rRJ9wTJMUB8C',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Chief Scientist, isee AI',
                    'filled': False,
                    'name': 'Chris Baker',
                    'scholar_id': 'bTdT7hAAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Professor of Psychology, Ewha Womans '
                                   'University',
                    'filled': False,
                    'name': 'Sung-Ho Kim',
                    'scholar_id': 'KXQb7CAAAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Assistant Professor, Boston University',
                    'filled': False,
                    'name': 'Melissa M. Kibbe',
                    'scholar_id': 'NN4GKo8AAAAJ',
                    'source': 'CO_AUTHORS_LIST'},
                   {'affiliation': 'Nvidia Corporation',
                    'filled': False,
                    'name': 'Peter Shirley',
                    'scholar_id': 'nHx9IgYAAAAJ',
                    'source': 'CO_AUTHORS_LIST'}],
     'email_domain': '@berkeley.edu',
     'filled': False,
     'hindex': 9,
     'hindex5y': 9,
     'homepage': 'http://steven.cholewiak.com/',
     'i10index': 8,
     'i10index5y': 7,
     'interests': ['Depth Cues',
                   '3D Shape',
                   'Shape from Texture & Shading',
                   'Naive Physics',
                   'Haptics'],
     'name': 'Steven A. Cholewiak, PhD',
     'organization': 6518679690484165796,
     'scholar_id': '4bahYMkAAAAJ',
     'source': 'SEARCH_AUTHOR_SNIPPETS',
     'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=4bahYMkAAAAJ'}

``citedby``
^^^^^^^^^^^

This is a method for the Publication container objects. It searches
Google Scholar for other articles that cite this Publication and returns
a Publication generator.

``bibtex``
^^^^^^^^^^

You can export a publication to Bibtex by using the ``bibtex`` property.
Here's a quick example:

.. code:: python

    >>> query = scholarly.search_pubs("A density-based algorithm for discovering clusters in large spatial databases with noise")
    >>> pub = next(query)
    >>> scholarly.bibtex(pub)

by running the code above you should get the following Bibtex entry:

.. code:: bib

    @inproceedings{ester1996density,
     abstract = {Clustering algorithms are attractive for the task of class identification in spatial databases. However, the application to large spatial databases rises the following requirements for clustering algorithms: minimal requirements of domain knowledge to determine the input},
     author = {Ester, Martin and Kriegel, Hans-Peter and Sander, J{\"o}rg and Xu, Xiaowei and others},
     booktitle = {Kdd},
     number = {34},
     pages = {226--231},
     pub_year = {1996},
     title = {A density-based algorithm for discovering clusters in large spatial databases with noise.},
     venue = {Kdd},
     volume = {96}
    }

Using proxies
-------------

In general, Google Scholar does not like bots, and can often block
scholarly, especially those pages that contain ``scholar?`` in the URL.
We are actively working towards making scholarly more robust
towards that front.

The most common solution for avoiding network issues is to use proxies
and Tor.

There is a class in the scholarly library, which handles all these
different types of connections for you, called ``ProxyGenerator``.

To use this class simply import it from the scholarly package:

.. code:: python

    from scholarly import ProxyGenerator

Then you need to initialize an object:

.. code:: python

    pg = ProxyGenerator()

Select the desirered connection type from the following options that
come from the ProxyGenerator class:

-  ScraperAPI()
-  Luminati()
-  FreeProxies()
-  SingleProxy()
-  Tor\_Internal()
-  Tor\_External()

All of these methods return ``True`` if the proxy was setup successfully which
you can check before beginning to use it with the ``use_proxy`` method.

Example:

.. code:: python

    success = pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)

Finally set scholarly to use this proxy for your actions

if you want to use one of the above methods:

.. code:: python

    scholarly.use_proxy(pg)

`scholarly` is smart enough to know which requests really need proxy, and which do not.
If you set up a proxy, `scholarly` will by default use `FreeProxies` to fetch pages that will not be actively blocked.
If you would rather have all requests go through the proxy you set, then pass your `pg` object twice.

.. code:: python

    scholarly.use_proxy(pg, pg)

If you want to run it without any proxy (after setting up one):

.. code:: python

    pg = ProxyGenerator()
    scholarly.use_proxy(pg, pg)

``ScraperAPI``
^^^^^^^^^^^^^^
pg.ScraperAPI()
###############

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()

You will have to provide your ScraperAPI key

.. code:: python

    success = pg.ScraperAPI(YOUR_SCRAPER_API_KEY)

Or alternatively you can use the environment variables as in the case of Luminati example.

If you have Startup or higher paid plans, you can use additional options that are allowed for your plan.

.. code:: python

    success = pg.ScraperAPI(YOUR_SCRAPER_API_KEY, country_code='fr', premium=True, render=True)

See https://www.scraperapi.com/pricing/ to see which options are enable for your plan.

Finally, you can route your query through the ScraperAPI proxy

.. code:: python

    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)

``Luminati``
^^^^^^^^^^^^^^^^^
pg.Luminati()
#############

If you have a luminati proxy service, please refer to the environment
setup for Luminati below and simply call the following command before
any function you want to execute.

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()

You can use your own configuration

.. code:: python

    success = pg.Luminati(usr= "your_username",passwd ="your_password", port = "your_port" )

Or alternatively you can use the environment variables set in your .env
file

.. code:: python

    import os
    pg.Luminati(usr=os.getenv("USERNAME"),passwd=os.getenv("PASSWORD"),proxy_port = os.getenv("PORT"))

.. code:: python

    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)

``FreeProxies``
^^^^^^^^^^^^^^^^^^^^
pg.FreeProxies()
################

This uses the ``free-proxy`` pip library to add a proxy to your
configuration.

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    success = pg.FreeProxies()
    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)

``SingleProxy``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pg.SingleProxy(http: str, https:str)
####################################

If you want to use a proxy of your choice, feel free to use this option.

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    success = pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)

**NOTE:** Please create a new proxy object whenever you change proxy
method, as this can lead to unexpected behavior.

``Tor_External``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pg.Tor_External(tor_sock_port: int, tor_control_port: int, tor_password: str)
###############################################################################

This method is deprecated since v1.5

This option assumes that you have access to a Tor server and a ``torrc``
file configuring the Tor server to have a control port configured with a
password; this setup allows scholarly to refresh the Tor ID, if
scholarly runs into problems accessing Google Scholar.

If you want to install and use Tor, then install it using the command

::

    sudo apt-get install -y tor

See
`setup\_tor.sh <https://github.com/scholarly-python-package/scholarly/blob/master/setup_tor.sh>`__
on how to setup a minimal, working ``torrc`` and set the password for
the control server. (Note: the script uses ``scholarly_password`` as the
default password, but you may want to change it for your installation.)

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    success = pg.Tor_External(tor_sock_port=9050, tor_control_port=9051, tor_password="scholarly_password")
    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)

``Tor_Internal``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pg.Tor_internal(tor_cmd=None, tor_sock_port=None, tor_control_port=None)
########################################################################

This method is deprecated since v1.5

If you have Tor installed locally, this option allows scholarly to
launch its own Tor process. You need to pass a pointer to the Tor
executable in your system.

.. code:: python

    from scholarly import scholarly, ProxyGenerator

    pg = ProxyGenerator()
    success = pg.Tor_Internal(tor_cmd = "tor")
    scholarly.use_proxy(pg)

    author = next(scholarly.search_author('Steven A Cholewiak'))
    scholarly.pprint(author)


Setting up environment for Luminati and/or Testing
--------------------------------------------------

To run the ``test_module.py`` it is advised to create a ``.env`` file in
the working directory of the ``test_module.py`` as:

.. code:: bash

    touch .env

.. code:: bash

    nano .env # or any editor of your choice

Define the connection method for the Tests, among these options:

-  luminati (if you have a Luminati proxy service)
-  scraperapi (if you have a ScraperAPI proxy service)
-  freeproxy
-  tor
-  tor\_internal
-  none (if you want a local connection, which is also the default
   value)

ex.

.. code:: bash

    CONNECTION_METHOD = luminati

If using a luminati proxy service please append the following to your
``.env``:

.. code:: bash

    USERNAME = <LUMINATI_USERNAME>
    PASSWORD = <LUMINATI_PASSWORD>
    PORT = <PORT_FOR_LUMINATI>