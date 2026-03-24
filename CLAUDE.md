# CLAUDE.md

## Project Overview

`scholarly` is a Python module for retrieving author and publication data from Google Scholar programmatically. It parses HTML responses from Google Scholar and returns structured data.

- **Language:** Python 3.8+
- **License:** Unlicense (public domain)
- **Current version:** 1.7.11
- **PyPI:** `pip3 install scholarly`

## Repository Structure

```
scholarly/             # Main package
  _scholarly.py        # Core API: search, fill methods (_Scholarly class)
  _navigator.py        # HTTP session management, proxy routing
  _proxy_generator.py  # Proxy service integrations (ScraperAPI, Bright Data, FreeProxy)
  author_parser.py     # HTML parsing for author profiles
  publication_parser.py # HTML parsing for publications
  data_types.py        # TypedDict definitions (Author, Publication, etc.)
test_module.py         # Full test suite (unittest-based)
docs/                  # Sphinx documentation
scripts/               # Helper scripts
.github/workflows/     # CI/CD pipelines
```

## Setup

```bash
pip3 install -e .                    # Editable install for development
pip3 install -r requirements.txt     # Runtime dependencies
pip3 install -r requirements-dev.txt # Dev dependencies (sphinx, coverage)
```

## Testing

```bash
python3 -m unittest -v test_module.py
```

- Uses Python `unittest` framework (not pytest)
- Test classes: `TestScholarly`, `TestLuminati`, `TestScraperAPI`, `TestTorInternal`, `TestScholarlyWithProxy`
- **6 of 17 test cases require premium proxy services** (ScraperAPI or Bright Data credentials). These are skipped when credentials are unavailable.
- Coverage: `coverage run test_module.py && coverage report`

## Linting

Uses **flake8** only. No black, isort, mypy, or pre-commit hooks.

```bash
flake8
```

Configuration (`.flake8`):
- Max line length: **127**
- Max complexity: 10
- Selected rules: E9, E111, F63, F7, F82, F401
- Ignored: E261, E265
- Excluded: `scholarly/__init__.py`, `docs/conf.py`

## CI/CD (GitHub Actions)

- **pythonpackage.yml** — Main CI: runs on Ubuntu, macOS, Windows with Python 3.8. Triggers on push/PR to `main`/`develop`, plus scheduled runs.
- **lint.yaml** — Flake8 linting (called by main workflow).
- **proxytests.yml** — Proxy-dependent tests, runs on push to `main` only (uses GitHub secrets).
- **codeql-analysis.yml** — Security scanning on push/PR to `main`/`develop`.
- **publish-to-pypi.yml** — Publishes to PyPI on tagged commits.

## Contributing Conventions

- **Base branch for PRs:** `develop` (not `main`)
- **Create an issue first** before submitting a PR
- **Commit message style:** imperative mood, concise
  - Bug fixes: `Fix <description>` or `Handle <condition>`
  - Features: `Add <description>`
  - Tests: `Add a unit test to <description>` or `Test that <description>`
  - Version bumps: `Bump version to X.Y.Z`
- **Tests:** add tests for new features; ensure existing tests pass
- **Docs:** verify documentation consistency; build with `cd docs && make html`

## Key Architecture Notes

- `_Scholarly` is the main singleton API class (instantiated as `scholarly` in `__init__.py`)
- Google Scholar responses are parsed via `BeautifulSoup` in the parser modules
- Anti-bot circumvention relies on proxy rotation (`_proxy_generator.py`) and user-agent spoofing
- `_navigator.py` manages the HTTP session and handles retries, redirects, and CAPTCHA detection
- Data types are `TypedDict` subclasses defined in `data_types.py`
