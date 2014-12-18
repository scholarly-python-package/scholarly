scholarly.py
===========

Changes
-------

Note that because of the nature of web scraping, this project will be in **perpetual beta**.

### v0.1

* Initial release.


What is this?
-------------

[Google Scholar](http://scholar.google.com/) is a database of authors and their publications. Data is returned to you in a friendly, Pythonic way:

  {'_filled': False,
   'affiliation': u'Postdoctoral Fellow, University of Giessen',
   'citedby': 72,
   'email': u'@psychol.uni-giessen.de',
   'id': '4bahYMkAAAAJ',
   'interests': [u'3D Shape',
                 u'Shape from Texture',
                 u'Shape from Shading',
                 u'Naive Physics',
                 u'Haptics'],
   'name': u'Steven A. Cholewiak',
   'url_citations': '/citations?user=4bahYMkAAAAJ&hl=en',
   'url_picture': '/citations?view_op=view_photo&user=4bahYMkAAAAJ&citpid=1'}

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
Because `scholarly` does not use an official API, so no key is required. Simply:

```python
import scholarly

print search_author('Steven A. Cholewiak').next()
```

License
-------

The original code that this project was forked from was released by [Bello Chalmers](https://github.com/lbello/chalmers-web) under a 'Do What the Fuck You Want to Public License'. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).