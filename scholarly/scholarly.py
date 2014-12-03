#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""scholarly.py"""

from bs4 import BeautifulSoup
import dateutil
import httplib
import urllib2

_HEADERS = {'User-Agent': 'Mozilla/2.0 (compatible; MSIE 5.5; Windows NT)'}
_SCHOLARHOST = 'scholar.google.com'

def get_soup(request):
    """Return the BeautifulSoup for a page on scholar.google.com"""
    conn = httplib.HTTPConnection(_SCHOLARHOST)
    conn.request("GET", request, '', _HEADERS)
    resp = conn.getresponse()
    if resp.status == 200:
        html = resp.read()
        html = html.decode('ascii', 'ignore')
        return BeautifulSoup(html)
    else:
        raise Exception('Error: {0} {1}'.format(resp.status, resp.reason))

class Publication(object):
    """Returns a single publication"""
    def __init__(self, __data):
        titlelink = __data.find('a', class_='gsc_a_at')
        self.url_scholar = titlelink['href']
        self.author = [i.strip() for i in __data.find(class_='gs_gray').text.split(',')]
        self.title = titlelink.text
        self.year = __data.find('span', class_='gsc_a_h').text
        self.citedby = __data.find('td', class_='gsc_a_c').text.strip()
        if self.citedby and self.citedby[-1] == '*':
            self.mergedcitations = True
            self.citedby = self.citedby[:-1]
        else:
            self.mergedcitations = False
        self.citedby = int(self.citedby) if self.citedby else 0
        self._filled = False

    def fill(self):
        """Populate the Publication with information from its profile"""
        soup = get_soup(self.url_scholar)
        self.title = soup.find('div', id='gsc_title').text
        if soup.find('a', class_='gsc_title_link'):
            self.url_article = soup.find('a', class_='gsc_title_link')['href']
        for item in soup.findAll('div', class_='gs_scl'):
            key = item.find(class_='gsc_field').text
            val = item.find(class_='gsc_value').text
            if key == u'Authors':
                self.author = [i.strip() for i in val.split(',')]
            elif key == u'Volume': self.volume = int(val)
            elif key == u'Issue': self.issue = int(val)
            elif key == u'Pages': self.pages = val
            elif key == u'Publisher': self.publisher = val
            elif key == u'Publication date':
                pubdate = dateutil.parser.parse(val)
                self.year = pubdate.year
                self.month = pubdate.month
            elif key == u'Description':
                if val[0:8].lower() == u'abstract':
                    val = val[9:].strip()
                self.description = val
        if soup.find('div', class_='gsc_title_ggi'):
            self.url_eprint = soup.find('div', class_='gsc_title_ggi').a['href']
        self._filled = True
        return self

    def __str__(self):
        ret = ''
        for key, val in self.__dict__.items():
            ret += '{0}: {1}\n'.format(key, val)
        return ret

class CitationIndex(object):
    """Returns the citation counts for an Author"""
    def __init__(self, lbb):
        self.since_year = int(lbb.findAll('th', class_='gsc_rsb_sth')[-1].text.split(' ')[1])
        nums = lbb.findAll('td', class_='gsc_rsb_std')
        (self.cites_all, self.cites_cur) = (int(nums[0].text), int(nums[1].text))
        (self.h_all, self.h_cur) = (int(nums[2].text), int(nums[3].text))
        (self.i10_all, self.i10_cur) = (int(nums[4].text), int(nums[5].text))

class Author(object):
    """Returns a single author"""
    def __init__(self, __data):
        if isinstance(__data, (str, unicode)):
            self.url_profile = '/citations?user={0}&hl=en'.format(urllib2.quote(__data))
        else:
            self.name = __data.find('h3', class_='gsc_1usr_name').text
            self.affiliation = __data.find('div', class_='gsc_1usr_aff').text
            self.email = __data.find('div', class_='gsc_1usr_emlb').text
            self.interests = [i.text.strip() for i in __data.findAll('a', class_='gsc_co_int')]
            self.citedby = int(__data.find('div', class_='gsc_1usr_cby').text[9:])
            self.url_profile = __data('a')[0]['href']
            self.url_picture = __data('img')[0]['src']
        self._filled = False

    def fill(self):
        """Populate the Author with information from their profile"""
        pagesize = 100
        soup = get_soup('{0}&pagesize={1}'.format(self.url_profile, pagesize))
        self.name = soup.find('div', id='gsc_prf_in').text
        self.affiliation = soup.find('div', class_='gsc_prf_il').text
        self.interests = [i.text.strip() for i in soup.findAll('a', class_='gsc_prf_ila')]
        self.cindex = CitationIndex(soup.find('table', id='gsc_rsb_st'))
        self.url_picture = soup.find('img')['src']

        self.pubs = list()
        pubstart = 0
        while True:
            pubs = soup.find('table', id='gsc_a_t')
            self.pubs.extend([Publication(i) for i in pubs.findAll('tr', class_='gsc_a_tr')])
            if 'disabled' not in soup.find('button', id='gsc_bpf_next').attrs:
                pubstart += pagesize
                soup = get_soup('{0}&cstart={1}&pagesize={2}'.format(self.url_profile, pubstart, pagesize))
            else: break
        self._filled = True
        return self

    def __str__(self):
        ret = ''
        for key, val in self.__dict__.items():
            ret += '{0}: {1}\n'.format(key, val)
        return ret

def search_author(name):
    """Search authors in Google Scholar.

    It returns the result of the query as a generator. Each element
    is an Author object with the following attributes and methods:
        - name: Name of the author.
        - url_picture: The link to the profile.
        - url_profile: The link to the author's picture.
        - fill(): A method to fetch all the author information.
    """
    soup = get_soup('/citations?view_op=search_authors&hl=en&mauthors={0}'.format(urllib2.quote(name)))
    while True:
        for tablerow in soup.findAll('div', 'gsc_1usr'):
            yield Author(tablerow)
        nextbutton = soup.find(id='gsc_authors_bottom_pag')
        if nextbutton and 'disabled' not in nextbutton[-1].attrs:
            soup = get_soup(nextbutton[-1]['onclick'][17:-1])
        else: break

if __name__ == "__main__":
    author = search_author('Steven A Cholewiak').next()
    author.fill()
    