import hashlib
import random

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36"
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': _USER_AGENT,
    'accept': 'text/html,application/xhtml+xml,application/xml'
    }
_HOST = "https://scholar.google.com"
_AUTHSEARCH = "/citations?view_op=search_authors&hl=en&mauthors={0}"
_CITATIONAUTH = "/citations?user={0}&hl=en"
_CITATIONPUB = "/citations?view_op=view_citation&citation_for_view={0}"
_KEYWORDSEARCH = "/citations?view_op=search_authors&hl=en&mauthors=label:{0}"
_PUBSEARCH = "/scholar?hl=en&q={0}"
_SCHOLARPUB = "/scholar?oi=bibs&hl=en&cites={0}"

_CAPTCHA = "iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']"

_CITATIONAUTHRE = r"user=([\w-]*)"
_CITATIONPUBRE = r"citation_for_view=([\w-]*:[\w-]*)"
_SCHOLARCITERE = r"gs_ocit\(event,\'([\w-]*)\'"
_SCHOLARPUBRE = r"cites=([\w-]*)"
_EMAILAUTHORRE = r"Verified email at "

_pAGESIZE = 100
_PROXY = "127.0.0.1:9150"