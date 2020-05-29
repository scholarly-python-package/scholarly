[![Python package](https://github.com/scholarly-python-package/scholarly/workflows/Python%20package/badge.svg?branch=master)](https://github.com/scholarly-python-package/scholarly/actions?query=branch%3Amaster)

[![Documentation Status](https://readthedocs.org/projects/scholarly/badge/?version=latest)](https://scholarly.readthedocs.io/en/latest/?badge=latest)


# scholarly
scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

## Documentation

Check the [documentation](https://scholarly.readthedocs.io/en/latest/?badge=latest) for a complete reference!

## Installation
Use `pip` to install from pypi:

```bash
pip3 install scholarly
```

or `pip` to install from github:

```bash
pip3 install -U git+https://github.com/OrganicIrradiation/scholarly.git
```


## Usage
Because `scholarly` does not use an official API, no key is required. Simply:

```python
from scholarly import scholarly

print(next(scholarly.search_author('Steven A. Cholewiak')))
```

### Example
Here's a quick example demonstrating how to retrieve an author's profile then retrieve the titles of the papers that cite his most popular (cited) paper.

```python
from scholarly import scholarly

# Retrieve the author's data, fill-in, and print
search_query = scholarly.search_author('Steven A Cholewiak')
author = next(search_query).fill()
print(author)

# Print the titles of the author's publications
print([pub.bib['title'] for pub in author.publications])

# Take a closer look at the first publication
pub = author.publications[0].fill()
print(pub)

# Which papers cited that publication?
print([citation.bib['title'] for citation in pub.get_citedby()])
```

## Tests

To run tests execute the `test_module.py` file as:

```bash
python3 test_module
```

or
```bash
python3 -m unittest -v test_module.py
```

## Build Docs

To build the documentation execute the make file as:

```bash
make html
```

## License
The original code that this project was forked from was released by [Luciano Bello](https://github.com/lbello/chalmers-web) under a [WTFPL](http://www.wtfpl.net/) license. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).
