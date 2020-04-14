import os
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'scholarly',
    version = '0.2.5',
    author = 'Steven A. Cholewiak',
    author_email = 'steven@cholewiak.com',

    description = 'Simple access to Google Scholar authors and citations',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Unlicense',

    url = 'https://github.com/OrganicIrradiation/scholarly',
    packages=setuptools.find_packages(),
    download_url = 'https://github.com/OrganicIrradiation/scholarly/tarball/v0.2.5',
    keywords = ['Google Scholar', 'academics', 'citations'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=['arrow', 'beautifulsoup4', 'bibtexparser', 'requests[security]'],
    test_suite="test.py"
)