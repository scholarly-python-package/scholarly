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

    # Retrieve the author's data, fill-in, and print
    scholarly = get_scholarly_instance()
    search_query = scholarly.search_author('Steven A. Cholewiak')
    author = next(search_query).fill()
    print(author)

    # Print the titles of the author's publications
    print([pub.bib['title'] for pub in author.publications])

    # Take a closer look at the first publication
    pub = author.publications[0].fill()
    print(pub)

    # Which papers cited that publication?
    print([citation.bib['title'] for citation in pub.get_citedby()])

    # What is the bibtex of that publication?
    print(pub.bibtex)