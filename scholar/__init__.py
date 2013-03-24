from scholar import searchAuthor,Author

"""Fetch information from Google Scholar

At the moment, the module is mainly focus in authors information fetch.

Search for authors (e.g. called "Bello" working for "Chalmers University"):
 >>> import scholar
 >>> l=scholar.searchAuthor('Bello Chalmers').next()
 >>> l.name
 <<< u'Luciano Bello'

Fetch all the infmation of an author:


"""
__version__=  '0.1'
