import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='scholarly',
    version='1.5.0',
    author='Steven A. Cholewiak, Panos Ipeirotis, Victor Silva, Arun Kannawadi',
    author_email='steven@cholewiak.com, panos@stern.nyu.edu, vsilva@ualberta.ca, arunkannawadi@astro.princeton.edu',
    description='Simple access to Google Scholar authors and citations',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Unlicense',

    url='https://github.com/scholarly-python-package/scholarly',
    packages=setuptools.find_packages(),
    keywords=['Google Scholar', 'academics', 'citations'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=['arrow',
                      'beautifulsoup4',
                      'bibtexparser',
                      'deprecated',
                      'requests[security]',
                      'requests[socks]',
                      'fake_useragent',
                      'PySocks',
                      'selenium',
                      'python-dotenv',
                      'free-proxy',
                      'sphinx_rtd_theme',
                      'typing_extensions'
                      ],
    extras_require={
        'tor': ['stem'],
    },
    test_suite="test_module.py"
)
