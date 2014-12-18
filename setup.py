from distutils.core import setup
setup(
	name = 'scholarly',
	packages = ['scholarly'],
	version = '0.1',
	description = 'Simplified access to Google Scholar authors and citations',
	author = 'Steven A. Cholewiak',
	author_email = 'steven@cholewiak.com',
	url = 'https://github.com/OrganicIrradiation/scholarly',
	keywords = ['Google Scholar', 'academics', 'citations'],
	classifiers = [],
	install_requires=[
	    "bibtexparser",
	    "beautifulsoup4",
	],
)