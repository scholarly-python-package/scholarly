# CHANGELOG

## Changes in v1.7.0

### Features
- Add a new `citation` entry to `pub` fetched from an author profile with formatted citation entry #423.

### Bugfixes
- Fix pprint failures on Windows #413.
- Thoroughly handle 1000 or more publications that are available (or not) according to public access mandates #414.
- Fix errors in `download_mandates_csv` that may occassionally occur for agencies without a policy link #413.

## Changes in v1.6.3

### Bugfix
- search_pubs method did not respect include_last_year, which is now fixed #420, #421.

### Enhancement
- Unit tests involving funding agency mandates are a bit more robust.

## Changes in v1.6.2

### Bugfix
- Fix an error in the workflow publishing to PyPI.

## Changes in v1.6.1

### Bugfix
- Handle 1000 or more publications that are available (or not) according to public access mandates #414.

### Enhancement
- Fetch 20+ coauthors without requiring geckodriver/chrome-driver to be installed #411.

## Changes in v1.6.0

### Features
- Download table of funding agencies as a CSV file with URL to the funding mandates included
- Downlad top-ranking journals in general, under sub-categories and in different languages as a CSV file

### Bugfixes
- #392
- #394

## Changes in v1.5.1

### Feature
- Support chromium (chrome-driver) as an alternative to geckodriver #387

### Improvements
- Firefox/Geckodriver operates in headless mode
- Increase test coverage to include all public APIs
- Clean up legacy code and improve coding styles
- Remove the use of deprecated functions in dependency packages

### Bugfix
- Stop attempting to reuse a closed webdriver

## Changes in v1.5.0
### Features
- Fetch the public access mandates information from a Scholar profile and mark the publications whether or not they satisfy the open-access mandate.
- Fetch an author's organization identifer from their Scholar profile
- Search for all authors affiliated with an organization
- Fetch homepage URL from a Scholar profile
### Enhancements
- Make `FreeProxies` more robust
- Stop the misleading traceback error message #313
### Bugfix
- Fix bug in exception handling #366
---
## Changes in v1.4.4
### Bugfix
- Fix a bug that would have prevented setting up ScraperAPI with exactly 1000 successful requests during the first week of the trial #356
### Enhancement
- Use FreeProxy instead of premium proxy servers when possible
---
## Changes in v1.4.3
### Bugfixes
- Fill the complete title of publications even if it appears truncated
- Robustly handle exceptions when more than 20 coauthors of a scholar cannot be fetched
 ---
## Changes in v1.4.2
### Bugfix
- ScraperAPI proxy works reliably
 ---
## Changes in v1.4.0
### Features
- Fetch the complete list of coauthors #322
- Fetch all citeids for a given publication #324
- Make scholarly objects inherently serializable #325
- Expose scholarly specific exceptions #327
### Bugfixes
- Test Tor on macOS and skip the test if tor is not installed #323
- Get cites_id and citedby_url without having to fill the publication #328
---
## Changes in v1.3.0
### Features
- Make the Author and Publication objects serializable
- Make `cites_id` a list to allow for multiple values
- Fetch all (more than 20) coauthors from a Scholar profile
