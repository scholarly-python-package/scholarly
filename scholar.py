#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import httplib
import urllib2

HEADERS = {'User-Agent': 'Mozilla/2.0 (compatible; MSIE 5.5; Windows NT)'}
SCHOLARHOST='scholar.google.com'

def getSoupfromScholar(request):
    conn = httplib.HTTPConnection(SCHOLARHOST)
    conn.request("GET", request, '', HEADERS)
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
        self.filledIN=False

    def __str__(self):
        ret='===\n'
        for k,v in self.__dict__.items(): ret+=k+' : '+str(v)+'\n'
        return ret

class Author():
    def __init__(self, authorTR):
        if isinstance(authorTR, (str, unicode)): self.profileURL='/citations?user=%s&hl=en' % urllib2.quote(authorTR)
        else:
                self.profileURL=authorTR('a')[-1]['href']
                self.pictureURL=authorTR('img')[0]['src']
                self.name=''.join(authorTR('a')[-1].findAll(text=True))
                self.info=authorTR.findAll(text=True)
        self.filledIN=False

    def fillIn(self):
        pagesize=100
        soup=getSoupfromScholar(self.profileURL+'&pagesize='+str(pagesize))
        userinfo=soup.find('div',{'class':'cit-user-info'})
        self.name=userinfo.find('span',{'id':'cit-name-display'}).text
        self.pictureURL=userinfo.find('img')['src']
        self.affiliation=userinfo.find('span',{'id':'cit-affiliation-display'}).text
        self.interests=[ i.strip() for i in BeautifulSoup(userinfo.find('span',{'id':'cit-int-read'}).text,convertEntities=BeautifulSoup.HTML_ENTITIES).text.split('-')]
        table=soup.find('table',{'class':'cit-table'})
        self.publications=[ Publication(i) for i in filter(lambda x: bool(x('input',{'type':'checkbox'})),table.findAll('tr'))]
        self.publicationsIncomplete='Next' in soup.find('div',{'class':'g-section cit-dgb'}).text
        self.filledIN=True
        return soup

    def __str__(self):
        ret='--\n'
        print_this=['name','profileURL','affiliation','interests','pictureURL']
        for k,v in self.__dict__.items(): ret+= k+' : '+str(v)+'\n' if k in print_this else ''
        return ret

def searchAuthor(author):
    conn = httplib.HTTPConnection(SCHOLARHOST)
    nextLink='/citations?view_op=search_authors&hl=en&mauthors=%s' % urllib2.quote(author)
    ret=[]
    while nextLink:
        soup=getSoupfromScholar(nextLink)
        for trs in soup('tr'):
                if bool(len(trs('a',{'class':'cit-dark-large-link'}))): yield Author(trs)
                elif 'Next &gt;' in trs.text: nextLink=trs('a')[-1]['href']
                else: nextLink=False
