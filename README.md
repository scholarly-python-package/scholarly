# scholarly
scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

## Installation
Use `pip` to install from pypi:

```bash
pip install scholarly
```

or `pip` to install from github:

```bash
pip3 install -U git+https://github.com/OrganicIrradiation/scholarly.git
```

or clone the package using git:

```bash
git clone https://github.com/OrganicIrradiation/scholarly.git
```


If you want to have support for proxies, you may also want to install the following libraries:
```
pip3 install -U free-proxy PySocks 
```

If you want to use Tor as proxy:
```
sudo apt-get install -y tor
```

## Requirements
Requires [arrow](http://crsmithdev.com/arrow/), [Beautiful Soup](https://pypi.python.org/pypi/beautifulsoup4/), [bibtexparser](https://pypi.python.org/pypi/bibtexparser/), and [requests[security]](https://pypi.python.org/pypi/requests/).
Also [pysocks](https://pypi.org/project/PySocks/) for using a proxy.




## Usage
Because `scholarly` does not use an official API, no key is required. Simply:

```python
from scholarly import scholarly

print(next(scholarly.search_author('Steven A. Cholewiak')))
```

### Methods
* `search_author` -- Search for an author by name and return a generator of Author objects.

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

* `search_keyword` -- Search by keyword and return a generator of Author objects.

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

* `search_pubs` -- Search for articles/publications and return generator of Publication objects.

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
                     'the object …',
         'author': 'SA Cholewiak and RW Fleming and M Singh',
         'eprint': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
         'title': 'Perception of physical stability and center of mass of 3-D '
                  'objects',
         'url': 'https://jov.arvojournals.org/article.aspx?articleID=2213254',
         'venue': 'Journal of vision',
         'year': ' 2015'},
 'citedby': 19,
 'filled': False,
 'id_scholarcitedby': '15736880631888070187',
 'source': 'scholar',
 'url_scholarbib': 'https://scholar.googleusercontent.com/scholar.bib?q=info:K8ZpoI6hZNoJ:scholar.google.com/&output=citation&scisdr=CgXsOAkeGAA:AAGBfm0AAAAAXsLLJNxa7vzefAEwz6a3tLCEoMsli6vj&scisig=AAGBfm0AAAAAXsLLJNK0I3FleN-7_r_TxUF8m5JDa9W5&scisf=4&ct=citation&cd=0&hl=en'}
```

* You can export a publication to Bibtex by using the `bibtex` property.
Here's a quick example:

```python
>>> query = scholarly.search_pubs("A density-based algorithm for discovering clusters in large spatial databases with noise")
>>> pub = next(query)
>>> pub.bibtex
```

by running the code above you should get the following bibtext entry:

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




* `Author.fill(sections=[])` -- Populate the Author object with
  information from their profile. The optional `sections` parameter takes a
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
>>> print(author.fill(sections=['basic', 'citation_indices', 'co-authors']))
{'affiliation': 'Vision Scientist',
 'citedby': 262,
 'citedby5y': 186,
 'coauthors': [{'affiliation': 'Kurt Koffka Professor of Experimental Psychology, University '
                'of Giessen',
                'filled': False,
                'id': 'ruUKktgAAAAJ',
                'name': 'Roland Fleming'},
               {'affiliation': 'Professor of Vision Science, UC Berkeley',
                'filled': False,
                'id': 'Smr99uEAAAAJ',
                'name': 'Martin Banks'},
               ...
               {'affiliation': 'Professor and Dean, School of Engineering, University of '
                'California, Merced',
                'filled': False,
                'id': 'r6MrFYoAAAAJ',
                'name': 'Edwin D. Hirleman Jr.'},
               {'affiliation': 'Vice President of Research, NVIDIA Corporation',
                'filled': False,
                'id': 'AE7Xvl0AAAAJ',
                'name': 'David Luebke'}],
 'email': '@berkeley.edu',
 'filled': False,
 'hindex': 8,
 'hindex5y': 8,
 'i10index': 7,
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

### Example
Here's a quick example demonstrating how to retrieve an author's profile then retrieve the titles of the papers that cite his most popular (cited) paper.

```python
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

### Using a proxy
Just run `scholarly.use_proxy()`. Parameters are an http and an https proxy.
*Note: this is a completely optional - opt-in feature'

Example using FreeProxy:

```python
from fp.fp import FreeProxy
from scholarly import scholarly

proxy = FreeProxy(rand=True, timeout=1, country_id=['US', 'CA']).get()  
scholarly.use_proxy(http=proxy, https=proxy)

author = next(scholarly.search_author('Steven A Cholewiak'))
print(author)
```

Example using Tor:

```python
from scholarly import scholarly
# default values are shown below
proxies = {'http' : 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
scholarly.use_proxy(**proxies)
# If proxy is correctly set up, the following runs through it
author = next(scholarly.search_author('Steven A Cholewiak'))
print(author)
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

## License
The original code that this project was forked from was released by [Bello Chalmers](https://github.com/lbello/chalmers-web) under a [WTFPL](http://www.wtfpl.net/) license. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).
