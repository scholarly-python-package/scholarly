[![Python package](https://github.com/scholarly-python-package/scholarly/workflows/Python%20package/badge.svg?branch=master)](https://github.com/scholarly-python-package/scholarly/actions?query=branch%3Amaster)

[![Documentation Status](https://readthedocs.org/projects/scholarly/badge/?version=latest)](https://scholarly.readthedocs.io/en/latest/?badge=latest)

# scholarly

scholarly is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

## Important Note

This is version 1.4 of the `scholarly` library. There has been a major refactor in the way the library operates and it's code structure and it **will break** most existing code, based on the previous (v0.x) versions.

## Documentation

Check the [documentation](https://scholarly.readthedocs.io/en/latest/?badge=latest) for a complete reference and a quickstart quide.

## Installation

Use `pip` to install from pypi:

```bash
pip3 install scholarly
```

or `pip` to install from github:

```bash
pip3 install -U git+https://github.com/scholarly-python-package/scholarly.git
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
