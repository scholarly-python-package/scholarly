#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import dateutil
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
        return BeautifulSoup(html)
    else:
        print 'Error: '
        print resp.status, resp.reason
        exit(1)

class Publication():
    def __init__(self, publicationTR):
        titleLink=publicationTR.find('a',class_='gsc_a_at')
        self.href=titleLink['href']
        self.info = dict()
        self.info['title']=titleLink.text
        self.info['year']=publicationTR.find('span',class_='gsc_a_h').text
        self.info['citedby']=publicationTR.find('td',class_='gsc_a_c').text.strip()
        self.info['citedby']=int(self.info['citedby']) if self.info['citedby'] else 0
        self.info['author']=' and '.join([i.strip() for i in publicationTR.find(class_='gs_gray').text.split(',')])
        self._filledIN=False

    def fill(self):
        soup=getSoupfromScholar(self.href)
        self.info['title']=soup.find('div', id='gsc_title').text
        if soup.find('a', class_='gsc_title_link'):
            self.info['url']=soup.find('a', class_='gsc_title_link')['href']
        allinfo=soup.findAll('div', class_='gs_scl')
        for item in allinfo[:-2]:
            key = item.find(class_='gsc_field').text
            val = item.find(class_='gsc_value').text
            if key == u'Authors':
                self.info[u'author']=' and '.join([i.strip() for i in val.split(',')])
            elif key == u'Publication date':
                dt = dateutil.parser.parse(val)
                self.info[u'year']=dt.year
                self.info[u'month']=dt.month
            elif key == u'Description':
                if val[0:8].lower() == u'abstract':
                    val = val[9:].strip()
                self.info[u'abstract']=val
            else:
                self.info[key] = val
        if soup.find('div', class_='gsc_title_ggi'):
            self.info['eprint']=soup.find('div', class_='gsc_title_ggi').a['href']
        self._filledIN=True
        return self
        
    def __str__(self):
        ret='===\n'
        for k,v in self.__dict__.items(): ret+=k+' : '+str(v)+'\n'
        return ret

class CitationIndex():
    def __init__(self, lbb):
        self.sinceYear=int(lbb.findAll('th', {'class', 'gsc_rsb_sth'})[-1].text.split(' ')[1])
        nums=lbb.findAll('td',{'class':'gsc_rsb_std'})
        (self.all,self.since)=(int(nums[0].text),int(nums[1].text))
        (self.hindexAll,self.hindexSince)=(int(nums[2].text),int(nums[3].text))
        (self.i10indexAll,self.i10indexSince)=(int(nums[4].text),int(nums[5].text))

class Author():
    def __init__(self, authorTR):
        if isinstance(authorTR, (str, unicode)): self.url_profile='/citations?user=%s&hl=en' % urllib2.quote(authorTR)
        else:
            self.url_profile=authorTR('a')[0]['href']
            self.url_picture=authorTR('img')[0]['src']
            self.name=''.join(authorTR('a')[1].findAll(text=True))
            self.info=authorTR.findAll(text=True)
        self._filledIN=False

    def fill(self):
        pagesize=100
        soup=getSoupfromScholar(self.url_profile+'&pagesize='+str(pagesize))
        userinfo=soup.find('div',{'id':'gsc_prf'})
        self.name=userinfo.find('div',{'id':'gsc_prf_in'}).text
        self.url_picture=userinfo.find('img')['src']
        infolist=userinfo.findAll('div',{'class':'gsc_prf_il'})
        self.affiliation=infolist[0].text
        self.interests=[i.text.strip() for i in infolist[1].findAll('a', {'class','gsc_prf_ila'})]
        self.citationIndex=CitationIndex(soup.find('table',{'id':'gsc_rsb_st'}))
        pubs=soup.find('table',{'id':'gsc_a_t'})
        self.publications=[Publication(i) for i in pubs.findAll('tr',{'class':'gsc_a_tr'})]
        self.publicationsIncomplete=not ('disabled' in soup.find('button', id='gsc_bpf_next').attrs)
        self._filledIN=True
        return self

    def __str__(self):
        ret='--\n'
        print_this=['name','url_profile','affiliation','interests','url_picture']
        for k,v in self.__dict__.items(): ret+= k+' : '+str(v)+'\n' if k in print_this else ''
        return ret

def searchAuthor(author):
    """Search authors in Google Scholar.

    It returns the result of the query as a generator. Each element
    is an Author object with the following attributes and methods:
        - name: Name of the author.
        - info: Additional information (e.g. Affiliation) as a list.
        - url_picture: The link to the profile.
        - url_profile: The link to the author's picture.
        - fillIn(): A method to fetch all the author information.
    """
    soup = getSoupfromScholar('/citations?view_op=search_authors&hl=en&mauthors={0}'.format(urllib2.quote(author)))
    next=True
    while next:
        for trs in soup.findAll('div','gsc_1usr'):
            yield Author(trs)
        citdgb = soup.find(id = 'gsc_authors_bottom_pag')
        if citdgb and not ('disabled' in citdgb[-1].attrs):
            soup=getSoupfromScholar(citdgb[-1]['onclick'][17:-1])
        else: break

if __name__ == "__main__":
    a = searchAuthor('Steven A Cholewiak').next()
    a.fill()