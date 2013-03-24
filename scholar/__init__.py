from scholar import searchAuthor,Author

"""Fetch information from Google Scholar (citations)

At the moment, the module is mainly focus in authors information (aka
citations).

Search for authors (e.g. called "Bello" working for "Chalmers University"):
 >>> import scholar
 >>> l=scholar.searchAuthor('Bello Chalmers').next()
 >>> l.name
 <<< u'Luciano Bello'

Fetch all the infmation of an author:
 >>> l.fillIn()
 >>> l.affiliation
 <<< u'PhD Student of Computer Science, Chalmers University of Technology'

Get an author by id:
 >>> b=scholar.Author('L9Rk-_sAAAAJ')
 >>> b.fillIn()
 >>> b.citationIndex.all
 <<< 15
"""
__version__=  '0.1'
