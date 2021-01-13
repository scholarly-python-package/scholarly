[![Python package](https://github.com/scholarly-python-package/scholarly/workflows/Python%20package/badge.svg?branch=master)](https://github.com/scholarly-python-package/scholarly/actions?query=branch%3Amaster)

[![Documentation Status](https://readthedocs.org/projects/scholarly/badge/?version=latest)](https://scholarly.readthedocs.io/en/latest/?badge=latest)

# scholarly

scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

## Important Note

This is version 1.0 of the `scholarly` library. There has been a major refactor in the way the library operates and it's code structure and it **will break** most existing code, based on the previous versions.

## Documentation

Check the [documentation](https://scholarly.readthedocs.io/en/latest/?badge=latest) for a complete reference.

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
author = scholarly.fill(next(search_query))
print(author)

# Print the titles of the author's publications
print([pub['bib']['title'] for pub in author['publications']])

# Take a closer look at the first publication
pub = scholarly.fill(author['publications'][0])
print(pub)

# Which papers cited that publication?
print([citation['bib']['title'] for citation in scholarly.citedby(pub)])
```

## Methods for `scholar`

#### `search_author` -- Search for an author by name and return a generator of Author objects.

```python
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
```

#### `search_author_id` -- Search for an author by the id visible in the url of an Authors profile.

```python
>>> author = scholarly.search_author_id('Smr99uEAAAAJ')
>>> scholarly.pprint(author)
{'affiliation': 'Professor of Vision Science, UC Berkeley',
 'email_domain': '@berkeley.edu',
 'filled': False,
 'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
 'name': 'Martin Banks',
 'scholar_id': 'Smr99uEAAAAJ',
 'source': 'AUTHOR_PROFILE_PAGE'}
```

#### `search_keyword` -- Search by keyword and return a generator of Author objects.

```python
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
```

#### `search_pubs` -- Search for articles/publications and return generator of Publication objects.

```python
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
```

Please note that the `author_id` array is positionally matching with the `author` array.
You can use the `author_id` to get further details about the author using the `search_author_id` method.

#### `fill` - fill the Author and Publications container objects with additional information.

##### About the Publications:

By default, scholarly returns only a lightly filled object for publication, to avoid overloading Google Scholar.
If necessary to get more information for the publication object, we call this method.

##### About the Authors:

If the container object passed to this method is an Author, the sections desired to be filled can be selected to populate the author with information from their profile, via the `sections` parameter.

The optional `sections` parameter takes a
list of the portions of author information to fill, as follows:

- `'basics'` = name, affiliation, and interests;
- `'indices'` = h-index, i10-index, and 5-year analogues;
- `'counts'` = number of citations per year;
- `'coauthors'` = co-authors;
- `'publications'` = publications;
- `'[]'` = all of the above (this is the default)

```python
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
 'i10index': 8,
 'i10index5y': 7,
 'interests': ['Depth Cues',
               '3D Shape',
               'Shape from Texture & Shading',
               'Naive Physics',
               'Haptics'],
 'name': 'Steven A. Cholewiak, PhD',
 'scholar_id': '4bahYMkAAAAJ',
 'source': 'SEARCH_AUTHOR_SNIPPETS',
 'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=4bahYMkAAAAJ'}
```

#### `citedby`

This is a method for the Publication container objects. It searches Google Scholar for other articles that cite this Publication and returns a Publication generator.

#### `bibtex`

You can export a publication to Bibtex by using the `bibtex` property.
Here's a quick example:

```python
>>> query = scholarly.search_pubs("A density-based algorithm for discovering clusters in large spatial databases with noise")
>>> pub = next(query)
>>> scholarly.bibtex(pub)
```

by running the code above you should get the following Bibtex entry:

```bib
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
```

## Using proxies

In general, Google Scholar does not like bots, and can often block scholarly. We are actively
working towards making scholarly more robust towards that front.

The most common solution for avoiding network issues is to use proxies and Tor.

There is a class in the scholarly library, which handles all these different types of connections for you, called `ProxyGenerator`.

To use this class simply import it from the scholarly package:

```python
from scholarly import ProxyGenerator
```

Then you need to initialize an object:

```python
pg = ProxyGenerator()
```

Select the desirered connection type from the following options that come from the ProxyGenerator class:

- Tor_Internal()
- Tor_External()
- Luminati()
- FreeProxies()
- SingleProxy()
  Example:

```python
pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
```

Finally set scholarly to use this proxy for your actions

if you want to use one of the above methods:

```python
scholarly.use_proxy(pg)
```

or if you want to run it without any proxy:

```python
scholarly.use_proxy(None)
```

#### `pg.Tor_External(tor_sock_port: int, tor_control_port: int, tor_password: str)`

This option assumes that you have access to a Tor server and a `torrc` file configuring the Tor server
to have a control port configured with a password; this setup allows scholarly to refresh the Tor ID,
if scholarly runs into problems accessing Google Scholar.

If you want to install and use Tor, then install it using the command

```
sudo apt-get install -y tor
```

See [setup_tor.sh](https://github.com/scholarly-python-package/scholarly/blob/master/setup_tor.sh)
on how to setup a minimal, working `torrc` and set the password for the control server. (Note:
the script uses `scholarly_password` as the default password, but you may want to change it for your
installation.)

```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.Tor_External(tor_sock_port=9050, tor_control_port=9051, tor_password="scholarly_password")
scholarly.use_proxy(pg)

author = next(scholarly.search_author('Steven A Cholewiak'))
scholarly.pprint(author)
```

#### `pg.Tor_internal(tor_cmd=None, tor_sock_port=None, tor_control_port=None)`

If you have Tor installed locally, this option allows scholarly to launch its own Tor process.
You need to pass a pointer to the Tor executable in your system.

```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.Tor_Internal(tor_cmd = "tor")
scholarly.use_proxy(pg)

author = next(scholarly.search_author('Steven A Cholewiak'))
scholarly.pprint(author)
```

#### `pg.FreeProxies()`

This uses the `free-proxy` pip library to add a proxy to your configuration.

```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

author = next(scholarly.search_author('Steven A Cholewiak'))
scholarly.pprint(author)
```

#### `pg.Luminati()`

If you have a luminati proxy service, please refer to the environment setup for Luminati below
and simply call the following command before any function you want to execute.

```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
```

You can use your own configuration

```python
pg.Luminati(usr= "your_username",passwd ="your_password", port = "your_port" )
```

Or alternatively you can use the environment variables set in your .env file

```python
import os
pg.Luminati(usr=os.getenv("USERNAME"),passwd=os.getenv("PASSWORD"),proxy_port = os.getenv("PORT"))
```

```python
scholarly.use_proxy(pg)

author = next(scholarly.search_author('Steven A Cholewiak'))
scholarly.pprint(author)
```

#### `pg.SingleProxy(http: str, https:str)`

If you want to use a proxy of your choice, feel free to use this option.

```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.SingleProxy(http = <your http proxy>, https = <your https proxy>)
scholarly.use_proxy(pg)

author = next(scholarly.search_author('Steven A Cholewiak'))
scholarly.pprint(author)
```

**NOTE:** Please create a new proxy object whenever you change proxy method, as this can lead to unexpected behavior.

## Setting up environment for Luminati and/or Testing

To run the `test_module.py` it is advised to create a `.env` file in the working directory of the `test_module.py` as:

```bash
touch .env
```

```bash
nano .env # or any editor of your choice
```

Define the connection method for the Tests, among these options:

- luminati (if you have a luminati proxy service)
- freeproxy
- tor
- tor_internal
- none (if you want a local connection, which is also the default value)

ex.

```bash
CONNECTION_METHOD = luminati
```

If using a luminati proxy service please append the following to your `.env`:

```bash
USERNAME = <LUMINATI_USERNAME>
PASSWORD = <LUMINATI_PASSWORD>
PORT = <PORT_FOR_LUMINATI>
```

## Tests

### Run the tests

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
