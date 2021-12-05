# CHANGELOG

## Changes in v1.5.0
## Features
- Fetch the public access mandates information from a Scholar profile and mark the publications whether or not they satisfy the open-access mandate.
- Fetch an author's organization identifer from their Scholar profile
- Search for all authors affiliated with an organization
- Fetch homepage URL from a Scholar profile
## Enhancements
- Make `FreeProxies` more robust
- Stop the misleading traceback error message #313
## Bugfixes
- Fix bug in exception handling #366
---
## Changes in v1.4.4
## Bugfix
- Fix a bug that would have prevented setting up ScraperAPI with exactly 1000 successful requests during the first week of the trial #356
## Enhancement
- Use FreeProxy instead of premium proxy servers when possible
---
## Changes in v1.4.3
## Bugfix
- Fill the complete title of publications even if it appears truncated
- Robustly handle exceptions when more than 20 coauthors of a scholar cannot be fetched
 ---
## Changes in v1.4.2
## Bugfix
- ScraperAPI proxy works reliably
 ---
## Changes in v1.4.0
## Features
- Fetch the complete list of coauthors #322
- Fetch all citeids for a given publication #324
- Make scholarly objects inherently serializable #325
- Expose scholarly specific exceptions #327
## Bugfixes
- Test Tor on macOS and skip the test if tor is not installed #323
- Get cites_id and citedby_url without having to fill the publication #328
---
## Changes in v1.3.0
## Features
- Make the Author and Publication objects serializable
- Make `cites_id` a list to allow for multiple values
- Fetch all (more than 20) coauthors from a Scholar profile
