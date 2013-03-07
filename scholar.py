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

class Author():
    def __init__(self, authorTR):
        self.authorTR=authorTR
        self.pictureURL=authorTR('img')[0]['src']
        self.profileURL=authorTR('a')[-1]['href']
        self.name=''.join(authorTR('a')[-1].findAll(text=True))
        self.info=authorTR.findAll(text=True)

    def fillInAuthor(self):
        soup=getSoupfromScholar(self.profileURL+'&pagesize=100')

    def __str__(self):
        ret= "Name:       %s\n" % self.name
        ret+="profileURL: %s\n" % self.profileURL
        ret+="pictureURL: %s\n" % self.pictureURL
        ret+="info:\n%s\n" % self.info
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
