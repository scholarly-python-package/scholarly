#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""scholarly.py"""

from __future__ import (division, print_function, unicode_literals)

import bibtexparser
from bs4 import BeautifulSoup
import dateutil
import hashlib
import httplib
import pprint
import random
import re
import time
import urllib2


_GOOGLEID = hashlib.md5(str(random.random())).hexdigest()[:16]
_COOKIE = 'GSP=ID={0}:CF=4'.format(_GOOGLEID)
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36', 
    'Cookie': _COOKIE
    }
_SCHOLARHOST = 'scholar.google.com'
_PUBSEARCH = '/scholar?q={0}'
_AUTHSEARCH = '/citations?view_op=search_authors&hl=en&mauthors={0}'
_KEYWORDSEARCH = '/citations?view_op=search_authors&hl=en&mauthors=label:{0}'
_CITATIONAUTH = '/citations?user={0}&hl=en'
_CITATIONAUTHRE = 'user=([\w-]*)'
_CITATIONPUB = '/citations?view_op=view_citation&citation_for_view={0}'
_CITATIONPUBRE = 'citation_for_view=([\w-]*:[\w-]*)'
_SCHOLARPUB = '/scholar?oi=bibs&hl=en&cites={0}'
_SCHOLARPUBRE = 'cites=([\w-]*)'
_SCHOLARCITERE = 'gs_ocit\(event,\'([\w-]*)\''
_PAGESIZE = 100

def get_soup(request):
    """Return the BeautifulSoup for a page on scholar.google.com/citations"""
    time.sleep(5+random.uniform(0, 5))
    conn = httplib.HTTPConnection(_SCHOLARHOST)
    conn.request("GET", request, '', _HEADERS)
    resp = conn.getresponse()
    if resp.status == 200:
        html = resp.read()
        html = html.decode('utf-8')
        return BeautifulSoup(html)
    else:
        raise Exception('Error: {0} {1}'.format(resp.status, resp.reason))

def search_scholar_soup(soup):
    """Return the BeautifulSoup for a page on scholar.google.com/scholar"""
    while True:
        for tablerow in soup.findAll('div', 'gs_r'):
            yield Publication(tablerow, 'scholar')
        if soup.find(class_='gs_ico gs_ico_nav_next'):
            soup = get_soup(soup.find(class_='gs_ico gs_ico_nav_next').parent['href'])
        else: break

def search_citation_soup(soup):
    """Search Google Scholar citations for authors

    It returns the result of the query as a generator. Each element
    is an Author object with the following attributes and methods:
        - name: Name of the author.
        - url_picture: The link to the profile.
        - url_profile: The link to the author's picture.
        - fill(): A method to fetch all the author information.
    """
    while True:
        for tablerow in soup.findAll('div', 'gsc_1usr'):
            yield Author(tablerow)
        nextbutton = soup.find(id='gsc_authors_bottom_pag')
        if nextbutton and 'disabled' not in nextbutton[-1].attrs:
            soup = get_soup(nextbutton[-1]['onclick'][17:-1])
        else: break

class Publication(object):
    """Returns a single publication"""
    def __init__(self, __data, pubtype=None):
        self.bib = dict()
        self.source = pubtype
        if self.source == 'citations':
            self.bib['title'] = __data.find('a', class_='gsc_a_at').text
            self.id_citations = re.findall(_CITATIONPUBRE, __data.find('a', class_='gsc_a_at')['href'])[0]
            self.url_citations = _CITATIONPUB.format(self.id_citations)
        elif self.source == 'scholar':
            self.bib['title'] = __data.find('h3', class_='gs_rt').find('a').text
            self.bib['abstract'] = __data.find('div', class_='gs_rs').text
            self.bib['url'] = __data.find('h3', class_='gs_rt').find('a')['href']
            if __data.find('div', class_='gs_ggs gs_fl'):
                self.bib['eprint'] = __data.find('div', class_='gs_ggs gs_fl').find('a')['href']
            if self.bib['abstract'][0:8].lower() == 'abstract':
                self.bib['abstract'] = self.bib['abstract'][9:].strip()
            citebuttons = __data.findAll('a', class_='gs_nta gs_nph')
            for row in citebuttons:
                if row.text == 'Import into BibTeX':
                    self.url_scholarbib = row['href']
                    break
        self._filled = False

    def fill(self):
        """Populate the Publication with information from its profile"""
        
        if self.source == 'citations':
            soup = get_soup(self.url_citations)
            self.bib['title'] = soup.find('div', id='gsc_title').text
            if soup.find('a', class_='gsc_title_link'):
                self.bib['url'] = soup.find('a', class_='gsc_title_link')['href']
            for item in soup.findAll('div', class_='gs_scl'):
                key = item.find(class_='gsc_field').text
                val = item.find(class_='gsc_value')
                if key == 'Authors':
                    self.bib['author'] = ' and '.join([i.strip() for i in val.text.split(',')])
                elif key == 'Volume': self.bib['volume'] = val.text
                elif key == 'Issue': self.bib['number'] = val.text
                elif key == 'Pages': self.bib['pages'] = val.text
                elif key == 'Publisher': self.bib['publisher'] = val.text
                elif key == 'Publication date': self.bib['year'] = dateutil.parser.parse(val.text).year
                elif key == 'Description':
                    if val.text[0:8].lower() == 'abstract':
                        val = val.text[9:].strip()
                    self.bib['abstract'] = val
                elif key == 'Total citations':
                    self.id_scholarcitedby = re.findall(_SCHOLARPUBRE, val.find('a')['href'])[0]
            if soup.find('div', class_='gsc_title_ggi'):
                self.bib['eprint'] = soup.find('div', class_='gsc_title_ggi').a['href']
            self._filled = True
        elif self.source == 'scholar':
            conn = httplib.HTTPConnection(_SCHOLARHOST)
            conn.request("GET", self.url_scholarbib, '', _HEADERS)
            resp = conn.getresponse()
            if resp.status == 200:
                self.bib = bibtexparser.loads(resp.read()).entries[0]
                self._filled = True
            else:
                raise Exception('Error: {0} {1}'.format(resp.status, resp.reason))
        return self
        
    def citedby(self):
        """Search by Google Scholar's relationship id"""
        if not self.id_scholarcitedby:
            self.fill()
        soup = get_soup(_SCHOLARPUB.format(urllib2.quote(self.id_scholarcitedby)))
        return search_scholar_soup(soup)
    
    def __str__(self):
        return pprint.pformat(self.__dict__)

class Author(object):
    """Returns a single author"""
    def __init__(self, __data):
        if isinstance(__data, (str, unicode)):
            self.id = __data
            self.url_citations = _CITATIONAUTH.format(self.id)
        else:
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
            self.url_citations = _CITATIONAUTH.format(self.id)
            self.url_picture = __data('img')[0]['src']
            self.name = __data.find('h3', class_='gsc_1usr_name').text
            self.affiliation = __data.find('div', class_='gsc_1usr_aff').text
            self.email = __data.find('div', class_='gsc_1usr_emlb').text
            self.interests = [i.text.strip() for i in __data.findAll('a', class_='gsc_co_int')]
            self.citedby = int(__data.find('div', class_='gsc_1usr_cby').text[9:])
        self._filled = False

    def fill(self):
        """Populate the Author with information from their profile"""
        time.sleep(3)
        
        soup = get_soup('{0}&pagesize={1}'.format(self.url_citations, _PAGESIZE))
        self.name = soup.find('div', id='gsc_prf_in').text
        self.affiliation = soup.find('div', class_='gsc_prf_il').text
        self.interests = [i.text.strip() for i in soup.findAll('a', class_='gsc_prf_ila')]
        self.url_picture = soup.find('img')['src']

        self.publications = list()
        pubstart = 0
        while True:
            self.publications.extend([Publication(i, 'citations') for i in soup.findAll('tr', class_='gsc_a_tr')])
            if 'disabled' not in soup.find('button', id='gsc_bpf_next').attrs:
                pubstart += _PAGESIZE
                soup = get_soup('{0}&cstart={1}&pagesize={2}'.format(self.url_citations, pubstart, _PAGESIZE))
            else: break
        self._filled = True
        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)

def search_pubs_query(query):
    """Search by author name, returns a generator of Author objects"""
    soup = get_soup(_PUBSEARCH.format(urllib2.quote(query)))
    return search_scholar_soup(soup)

def search_author(name):
    """Search by author name, returns a generator of Author objects"""
    soup = get_soup(_AUTHSEARCH.format(urllib2.quote(name)))
    return search_citation_soup(soup)

def search_keyword(keyword):
    """Search by keyword, returns a generator of Author objects"""
    soup = get_soup(_KEYWORDSEARCH.format(urllib2.quote(keyword)))
    return search_citation_soup(soup)

if __name__ == "__main__":
    author = search_author('Steven A Cholewiak').next()
    
    print(author.fill())
    