[![Python package](https://github.com/scholarly-python-package/scholarly/workflows/Python%20package/badge.svg?branch=main)](https://github.com/scholarly-python-package/scholarly/actions?query=branch%3Amain)
[![codecov](https://codecov.io/gh/scholarly-python-package/scholarly/branch/main/graph/badge.svg?token=0svtI9yVSQ)](https://codecov.io/gh/scholarly-python-package/scholarly)
[![Documentation Status](https://readthedocs.org/projects/scholarly/badge/?version=latest)](https://scholarly.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/27442991.svg)](https://zenodo.org/badge/latestdoi/27442991)


# scholarly

scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way without having to solve CAPTCHAs.

## Installation

Use `pip` to install the latest release from pypi:

```bash
pip3 install scholarly
```

or `pip` to install from github:

```bash
pip3 install -U git+https://github.com/scholarly-python-package/scholarly.git
```

`scholarly` follows [Semantic Versioning](https://semver.org/).

### Optional dependencies

- **geckodriver** provides the browser capabilities that may be needed to fully utilize the library. Currently, if a Scholar profile has more than 20 co-authors, `geckodriver` is needed to fetch the complete list.
If not installed, `scholarly` will fetch only up to 20 co-authors.

    To install `geckodriver`, download the latest version from their [Github repo](https://github.com/mozilla/geckodriver/releases) and the executable should be in the system path.
    Follow the appropriate installation instructions:
    [macOS](https://stackoverflow.com/a/67211136) | [Ubuntu](https://askubuntu.com/a/871077) | [Windows](https://stackoverflow.com/a/56926716)

- **Tor**:

    `scholarly` comes with a handful of APIs to set up proxies to circumvent anti-bot measures.
    Tor methods are deprecated since v1.5 and are not actively tested or supported.
    If you wish to use Tor, install `scholarly` using the `tor` tag as
    ```bash
    pip3 install scholarly[tor]
    ```
## Tests

To check if your installation is succesful, run the tests by executing the `test_module.py` file as:

```bash
python3 test_module
```

or

```bash
python3 -m unittest -v test_module.py
```
## Documentation

Check the [documentation](https://scholarly.readthedocs.io/en/latest/?badge=latest) for a [complete API reference](https://scholarly.readthedocs.io/en/stable/scholarly.html) and a [quickstart guide](https://scholarly.readthedocs.io/en/stable/quickstart.html).

### Examples

```python
from scholarly import scholarly

# Retrieve the author's data, fill-in, and print
# Get an iterator for the author results
search_query = scholarly.search_author('Steven A Cholewiak')
# Retrieve the first result from the iterator
first_author_result = next(search_query)
scholarly.pprint(first_author_result)

# Retrieve all the details for the author
author = scholarly.fill(first_author_result )
scholarly.pprint(author)

# Take a closer look at the first publication
first_publication = author['publications'][0]
first_publication_filled = scholarly.fill(first_publication)
scholarly.pprint(first_publication_filled)

# Print the titles of the author's publications
publication_titles = [pub['bib']['title'] for pub in author['publications']]
print(publication_titles)

# Which papers cited that publication?
citations = [citation['bib']['title'] for citation in scholarly.citedby(first_publication_filled)]
print(citations)
```

**IMPORTANT**: Making certain types of queries, such as `scholarly.citedby` or `scholarly.search_pubs`, will lead to Google Scholar blocking your requests and may eventually block your IP address.
You must use proxy services to avoid this situation.
See the ["Using proxies" section](https://scholarly.readthedocs.io/en/stable/quickstart.html#using-proxies) in the documentation for more details. Here's a short example:

```python
from scholarly import ProxyGenerator

# Set up a ProxyGenerator object to use free proxies
# This needs to be done only once per session
pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

# Now search Google Scholar from behind a proxy
search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
scholarly.pprint(next(search_query))
```

`scholarly` also has APIs that work with several premium (paid) proxy services.
`scholarly` is smart enough to know which queries need proxies and which do not.
It is therefore recommended to always set up a proxy in the beginning of your application.

#### Disclaimer

The developers use `ScraperAPI` to run the tests in Github Actions.
The developers of `scholarly` are not affiliated with any of the proxy services and do not profit from them. If your favorite service is not supported, please submit an issue or even better, follow it up with a pull request.

## Citing

If you have used this codebase in a scientific publication, please cite this software as following:

```bibtex
@software{cholewiak2021scholarly,
  author  = {Cholewiak, Steven A. and Ipeirotis, Panos and Silva, Victor and Kannawadi, Arun},
  title   = {{SCHOLARLY: Simple access to Google Scholar authors and citation using Python}},
  year    = {2021},
  doi     = {10.5821/zenodo.5764802},
  license = {Unlicense},
  url = {https://github.com/scholarly-python-package/scholarly},
  version = {1.5.0}
}
```

## License

The original code that this project was forked from was released by [Luciano Bello](https://github.com/lbello/chalmers-web) under a [WTFPL](http://www.wtfpl.net/) license. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).
