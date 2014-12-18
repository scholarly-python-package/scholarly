import os
from setuptools import setup

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
	name = 'scholarly',
	py_modules = ['scholarly'],
	version = '0.1',
	description = 'Simple access to Google Scholar authors and citations',
	long_description=(read('README.rst')),
	license='Unlicense',

	author = 'Steven A. Cholewiak',
	author_email = 'steven@cholewiak.com',
	url = 'https://github.com/OrganicIrradiation/scholarly',
	download_url = 'https://github.com/OrganicIrradiation/scholarly/tarball/0.1',
	keywords = ['Google Scholar', 'academics', 'citations'],
	classifiers = [
		'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=['bibtexparser', 'beautifulsoup4'],
)