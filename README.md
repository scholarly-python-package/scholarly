[![Python package](https://github.com/scholarly-python-package/scholarly/workflows/Python%20package/badge.svg?branch=master)](https://github.com/scholarly-python-package/scholarly/actions?query=branch%3Amaster)

[![Documentation Status](https://readthedocs.org/projects/scholarly/badge/?version=latest)](https://scholarly.readthedocs.io/en/latest/?badge=latest)

# scholarly

scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

## Documentation

Check the [documentation](https://scholarly.readthedocs.io/en/latest/?badge=latest) for a complete reference. (Warning: Still under development, please excuse the messiness.)

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
print([citation.bib['title'] for citation in pub.citedby])
```

## Methods for `scholar`

#### `search_author` -- Search for an author by name and return a generator of Author objects.

```python
>>> search_query = scholarly.search_author('Marty Banks, Berkeley')
>>> print(next(search_query))
{'affiliation': 'Professor of Vision Science, UC Berkeley',
 'citedby': 20160,
 'email': '@berkeley.edu',
 'filled': False,
 'id': 'Smr99uEAAAAJ',
 'interests': ['vision science', 'psychology', 'human factors', 'neuroscience'],
 'name': 'Martin Banks',
 'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=Smr99uEAAAAJ'}
```

#### `search_keyword` -- Search by keyword and return a generator of Author objects.

```python
>>> search_query = scholarly.search_keyword('Haptics')
>>> print(next(search_query))
{'affiliation': 'Postdoctoral research assistant, University of Bremen',
 'citedby': 55943,
 'email': '@collision-detection.com',
 'filled': False,
 'id': 'lHrs3Y4AAAAJ',
 'interests': ['Computer Graphics',
               'Collision Detection',
               'Haptics',
               'Geometric Data Structures'],
 'name': 'Rene Weller',
 'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=lHrs3Y4AAAAJ'}
```

#### `search_pubs` -- Search for articles/publications and return generator of Publication objects.

```python
>>> search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
>>> print(next(search_query))
{'bib': {'abstract': 'Humans can judge from vision alone whether an object is '
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
         'author_id': ['4bahYMkAAAAJ', '3xJXtlwAAAAJ', 'Smr99uEAAAAJ'],
         'cites': '23',
         'eprint': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
         'gsrank': '1',
         'title': 'Perception of physical stability and center of mass of 3-D '
                  'objects',
         'url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
         'venue': 'Journal of vision',
         'year': '2015'},
 'citations_link': '/scholar?cites=15736880631888070187&as_sdt=5,33&sciodt=0,33&hl=en',
 'filled': False,
 'source': 'scholar',
 'url_add_sclib': '/citations?hl=en&xsrf=&continue=/scholar%3Fq%3DPerception%2Bof%2Bphysical%2Bstability%2Band%2Bcenter%2Bof%2Bmass%2Bof%2B3D%2Bobjects%26hl%3Den%26as_sdt%3D0,33&citilm=1&json=&update_op=library_add&info=K8ZpoI6hZNoJ&ei=ewEtX7_JOIvrmQHcvJqoDA',
 'url_scholarbib': '/scholar?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=cite&scirp=0&hl=en'}
```

Please note that the `author_id` array is positionally matching the `author` array. 
You can use the `author_id` to get further details about the author using the `search_author_id` method.    

### Methods for `Publication` objects

#### `fill`

By default, scholarly returns only a lightly filled object for publication, to avoid overloading Google Scholar.
If necessary to get more information for the publication object, we call the `.fill()` method.

#### `citedby` 

Searches Google Scholar for other articles that cite this Publication and returns a Publication generator.

#### `bibtex`

You can export a publication to Bibtex by using the `bibtex` property.
Here's a quick example:

```python
>>> query = scholarly.search_pubs("A density-based algorithm for discovering clusters in large spatial databases with noise")
>>> pub = next(query)
>>> pub.bibtex
```

by running the code above you should get the following Bibtex entry:

```bib
@inproceedings{ester1996density,
 abstract = {Clustering algorithms are attractive for the task of class identification in spatial databases. However, the application to large spatial databases rises the following requirements for clustering algorithms: minimal requirements of domain knowledge to determine the input},
 author = {Ester, Martin and Kriegel, Hans-Peter and Sander, J{\"o}rg and Xu, Xiaowei},
 booktitle = {Kdd},
 cites = {17500},
 eprint = {https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf?source=post_page---------------------------},
 gsrank = {1},
 number = {34},
 pages = {226--231},
 title = {A density-based algorithm for discovering clusters in large spatial databases with noise.},
 url = {https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf?source=post_page---------------------------},
 venue = {Kdd},
 volume = {96},
 year = {1996}
}
```

### Methods for `Author` objects

#### `Author.fill(sections=[])` -- Populate the Author object with information from their profile.

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
>>> print(author.fill(sections=['basics', 'indices', 'coauthors']))
{'affiliation': 'Vision Scientist',
 'citedby': 288,
 'citedby5y': 211,
 'coauthors': [{'affiliation': 'Kurt Koffka Professor of Experimental Psychology, University '
                'of Giessen',
 'filled': False,
 'id': 'ruUKktgAAAAJ',
 'name': 'Roland Fleming'},
               {'affiliation': 'Professor of Vision Science, UC Berkeley',
 'filled': False,
 'id': 'Smr99uEAAAAJ',
 'name': 'Martin Banks'},
               {'affiliation': 'Durham University, Computer Science & Physics',
 'filled': False,
 'id': '3xJXtlwAAAAJ',
 'name': 'Gordon D. Love'},
               {'affiliation': 'Professor of ECE, Purdue University',
 'filled': False,
 'id': 'OiVOAHMAAAAJ',
 'name': 'Hong Z Tan'},
               {'affiliation': 'Deepmind',
 'filled': False,
 'id': 'MnUboHYAAAAJ',
 'name': 'Ari Weinstein'},
               {'affiliation': "Brigham and Women's Hospital/Harvard Medical School",
 'filled': False,
 'id': 'dqokykoAAAAJ',
 'name': 'Chia-Chien Wu'},
               {'affiliation': 'Professor of Psychology and Cognitive Science, Rutgers '
                'University',
 'filled': False,
 'id': 'KoJrMIAAAAAJ',
 'name': 'Jacob Feldman'},
               {'affiliation': 'Research Scientist at Google Research, PhD Student at UC '
                'Berkeley',
 'filled': False,
 'id': 'aYyDsZ0AAAAJ',
 'name': 'Pratul Srinivasan'},
               {'affiliation': 'Formerly: Indiana University, Rutgers University, University '
                'of Pennsylvania',
 'filled': False,
 'id': 'FoVvIK0AAAAJ',
 'name': 'Peter C. Pantelis'},
               {'affiliation': 'Professor in Computer Science, University of California, '
                'Berkeley',
 'filled': False,
 'id': '6H0mhLUAAAAJ',
 'name': 'Ren Ng'},
               {'affiliation': 'Yale University',
 'filled': False,
 'id': 'rNTIQXYAAAAJ',
 'name': 'Steven W Zucker'},
               {'affiliation': 'Brown University',
 'filled': False,
 'id': 'JPZWLKQAAAAJ',
 'name': 'Ben Kunsberg'},
               {'affiliation': 'Rutgers University, New Brunswick, NJ',
 'filled': False,
 'id': '9XRvM88AAAAJ',
 'name': 'Manish Singh'},
               {'affiliation': 'Kent State University',
 'filled': False,
 'id': 'itUoRvUAAAAJ',
 'name': 'Kwangtaek Kim'},
               {'affiliation': 'Silicon Valley Professor of ECE, Purdue University',
 'filled': False,
 'id': 'fD3JviYAAAAJ',
 'name': 'David S. Ebert'},
               {'affiliation': 'MIT',
 'filled': False,
 'id': 'rRJ9wTJMUB8C',
 'name': 'Joshua B. Tenenbaum'},
               {'affiliation': 'Chief Scientist, isee AI',
 'filled': False,
 'id': 'bTdT7hAAAAAJ',
 'name': 'Chris Baker'},
               {'affiliation': 'Professor of Psychology, Ewha Womans University',
 'filled': False,
 'id': 'KXQb7CAAAAAJ',
 'name': 'Sung-Ho Kim'},
               {'affiliation': 'Assistant Professor, Boston University',
 'filled': False,
 'id': 'NN4GKo8AAAAJ',
 'name': 'Melissa M. Kibbe'},
               {'affiliation': 'Nvidia Corporation',
 'filled': False,
 'id': 'nHx9IgYAAAAJ',
 'name': 'Peter Shirley'}],
 'email': '@berkeley.edu',
 'filled': False,
 'hindex': 8,
 'hindex5y': 8,
 'i10index': 8,
 'i10index5y': 7,
 'id': '4bahYMkAAAAJ',
 'interests': ['Depth Cues',
               '3D Shape',
               'Shape from Texture & Shading',
               'Naive Physics',
               'Haptics'],
 'name': 'Steven A. Cholewiak, PhD',
 'url_picture': 'https://scholar.google.com/citations?view_op=medium_photo&user=4bahYMkAAAAJ'}
```

## Using proxies

In general, Google Scholar does not like bots, and can often block scholarly. We are actively
working towards making scholarly more robust towards that front.

The most common solution for avoiding network issues is to use proxies and Tor.

The following options are available:

#### `scholarly.use_proxy`

Here is an example using the [FreeProxy](https://pypi.org/project/free-proxy/) library

```python
from fp.fp import FreeProxy
from scholarly import scholarly

def set_new_proxy():
    while True:
        proxy = FreeProxy(rand=True, timeout=1).get()
        proxy_works = scholarly.use_proxy(http=proxy, https=proxy)
        if proxy_works:
            break
    print("Working proxy:", proxy)
    return proxy

set_new_proxy()

while True:
    try:
        search_query = scholarly.search_pubs('Perception of physical stability and center of mass of 3D objects')
        print("Got the results of the query")
        break
    except Exception as e:
        print("Trying new proxy")
        set_new_proxy()

pub = next(search_query)
print(pub)

while True:
    try:
        filled = pub.fill()
        print("Filled the publication")
        break
    except Exception as e:
        print("Trying new proxy")
        set_new_proxy()

print(filled)
```

#### `scholarly.use_tor()`

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
from scholarly import scholarly

scholarly.use_tor(tor_sock_port=9050, tor_control_port=9051, tor_pw="scholarly_password")

author = next(scholarly.search_author('Steven A Cholewiak'))
print(author)
```

#### `scholarly.launch_tor()`

If you have Tor installed locally, this option allows scholarly to launch its own Tor process.
You need to pass a pointer to the Tor executable in your system,

```python
from scholarly import scholarly

scholarly.launch_tor('/usr/bin/tor',9030,9031)

author = next(scholarly.search_author('Steven A Cholewiak'))
print(author)
```

#### `scholarly.use_lum_proxy()`

If you have a luminaty proxy service, please refer to the environment setup for Luminaty below
and simply call the following command before any function you want to execute.

```python
scholarly.use_lum_proxy()
```

## Setting up environment for Luminaty and/or Testing

To run the `test_module.py` it is advised to create a `.env` file in the working directory of the `test_module.py` as:

```bash
touch .env
```

```bash
nano .env # or any editor of your choice
```

Define the connection method for the Tests, among these options:

- luminaty (if you have a luminaty proxy service)
- freeproxy
- tor
- none (if you want a local connection, which is also the default value)

ex.

```bash
CONNECTION_METHOD = luminaty
```

If using a luminaty proxy service please append the following to your `.env`:

```bash
USERNAME = <LUMINATY_USERNAME>
PASSWORD = <LUMINATY_PASSWORD>
PORT = <PORT_FOR_LUMINATY>
```

## Tests

### Run the tests

To run tests execute the `test_module.py` file as:

```bash
python3 test_module.py
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
