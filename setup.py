import os
import setuptools

def get_description():
    with open("README.md", "r") as fh:
        return fh.read()

setuptools.setup(
    name = 'scholarly',
    version = '0.3.0',
    author = 'Victor N. Silva',
    author_email = 'noreply@noreply.com',

    description = 'Scrape Google Scholar!',
    long_description=get_description(),
    long_description_content_type="text/markdown",
    license='Unlicense',

    url = 'https://github.com/silvavn/scholarly',
    packages=setuptools.find_packages(),
    download_url = 'https://github.com/OrganicIrradiation/scholarly/tarball/v0.3.0',
    keywords = ['Google Scholar', 'academics', 'citations', 'selenium', 'webscrapping'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Researchers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=['arrow', 'beautifulsoup4', 'bibtexparser', 'requests[security]'],
    test_suite="test.py"
)