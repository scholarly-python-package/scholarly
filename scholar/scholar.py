#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import httplib
import urllib2

_HEADERS = {'User-Agent': 'Mozilla/2.0 (compatible; MSIE 5.5; Windows NT)'}
_SCHOLARHOST='scholar.google.com'

def getSoupfromScholar(request):
    conn = httplib.HTTPConnection(_SCHOLARHOST)
    conn.request("GET", request, '', _HEADERS)
    resp = conn.getresponse()
    if resp.status == 200:
        html = resp.read()
        html = html.decode( 'ascii', 'ignore' )
        return BeautifulSoup( html)
    else:
        print 'Error: '
        print resp.status, resp.reason
        exit(-1)

class Publication():
    def __init__(self, publicationTR):
        titleLink=publicationTR.find('a',{'class':'cit-dark-large-link'})
        self.title=titleLink.text
        self.href=titleLink['href']
        self.year=publicationTR.find('td',{'id':'col-year'}).text
        self.citedBy=publicationTR.find('td',{'id':'col-citedby'}).text
        self.citedBy=int(BeautifulSoup(unicode(self.citedBy),convertEntities=BeautifulSoup.HTML_ENTITIES).text) if self.citedBy else 0
        self.asterisk='&lowast;' in publicationTR.find('td',{'id':'col-asterisk'}).text
        moreinfo=publicationTR.findAll('span',{'class':'cit-gray'})
        self.authors= [ i.strip() for i in moreinfo[0].text.split(',')]
        if '...' in self.authors[-1]: #incomplete list of authors
            self.authors[-1]=self.authors[-1].strip('. ')
            self.authors.append(unicode('...'))
        self.venue= moreinfo[1].text if len(moreinfo) > 1 else ''
        self._filledIN=False

    def __str__(self):
        ret='===\n'
        for k,v in self.__dict__.items(): ret+=k+' : '+str(v)+'\n'
        return ret

class CitationIndex():
    def __init__(self, lbb):
        self.graph=lbb.find('img')['src']
        t=lbb.find('td')
        self.sinceYear=t.findAll('td',{'class':'cit-borderleft'})[1].text.split(' ')[1]
        nums=t.findAll('td',{'class':'cit-borderleft cit-data'})
        (self.all,self.since)=(int(nums[0].text),int(nums[1].text))
        (self.hindexAll,self.hindexSince)=(int(nums[2].text),int(nums[3].text))
        (self.i10indexAll,self.i10indexSince)=(int(nums[4].text),int(nums[5].text))

class Author():
    def __init__(self, authorTR):
        if isinstance(authorTR, (str, unicode)): self.profileURL='/citations?user=%s&hl=en' % urllib2.quote(authorTR)
        else:
                self.profileURL=authorTR('a')[-1]['href']
                self.pictureURL=authorTR('img')[0]['src']
                self.name=''.join(authorTR('a')[-1].findAll(text=True))
                self.info=authorTR.findAll(text=True)
        self._filledIN=False

    def fillIn(self):
        pagesize=100
        soup=getSoupfromScholar(self.profileURL+'&pagesize='+str(pagesize))
        userinfo=soup.find('div',{'class':'cit-user-info'})
        self.name=userinfo.find('span',{'id':'cit-name-display'}).text
        self.pictureURL=userinfo.find('img')['src']
        self.affiliation=userinfo.find('span',{'id':'cit-affiliation-display'}).text
        self.interests=[ i.strip() for i in BeautifulSoup(userinfo.find('span',{'id':'cit-int-read'}).text,convertEntities=BeautifulSoup.HTML_ENTITIES).text.split('-')]
        self.pictureURL=userinfo.find('img')['src']
        self.citationIndex=CitationIndex(soup.find('div',{'class':'cit-lbb'}))
        pubs=soup.find('table',{'class':'cit-table'})
        self.publications=[ Publication(i) for i in pubs.findAll('tr',{'class':'cit-table item'})]
        self.publicationsIncomplete='Next' in soup.find('div',{'class':'g-section cit-dgb'}).text
        self._filledIN=True

    def __str__(self):
        ret='--\n'
        print_this=['name','profileURL','affiliation','interests','pictureURL']
        for k,v in self.__dict__.items(): ret+= k+' : '+str(v)+'\n' if k in print_this else ''
        return ret

def searchAuthor(author):
    """Search authors in Google Scholar.

    It returns the result of the query as a generator. Each element
    is an Author object with the following attributes and methods:
        - name: Name of the author.
        - info: Additional information (e.g. Affiliation) as a list.
        - pictureURL: The link to the profile.
        - profileURL: The link to the author's picture.
        - fillIn(): A method to fetch all the author information.
    """
    soup=getSoupfromScholar('/citations?view_op=search_authors&hl=en&mauthors=%s' % urllib2.quote(author))
    next=True
    while next:
        for trs in soup.findAll('div','g-unit'):
                yield Author(trs)
        citdgb=soup.find('div','cit-dgb').findAll('a')
        if citdgb and 'Next &gt;' in citdgb[-1]:
            soup=getSoupfromScholar(citdgb[-1]['href'])
        else: break
