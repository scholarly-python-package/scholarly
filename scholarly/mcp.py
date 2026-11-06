"""Run ``scholarly`` as a `Model Context Protocol <https://modelcontextprotocol.io/>`_ (MCP) server.

This module is optional. Install the MCP SDK with::

    pip install "scholarly[mcp]"

and launch the server with the ``scholarly-mcp`` console script (or
``python -m scholarly.mcp``)::

    scholarly-mcp                              # stdio transport (default)
    scholarly-mcp --transport streamable-http --host 127.0.0.1 --port 8000
    scholarly-mcp --proxy free                 # route requests through free proxies

The server exposes thin, stateless wrappers over the public ``scholarly`` API.
Every tool takes plain JSON-friendly arguments (names, ids, titles) and returns
plain JSON-friendly results, because MCP clients cannot hold on to Python
``Author``/``Publication`` objects between calls.

Secrets are read from the environment only (never from command line flags, so
they do not show up in process listings):

``SCRAPER_API_KEY``
    API key used by ``--proxy scraperapi``.
``SCHOLARLY_TOR_SOCKS_PORT`` / ``SCHOLARLY_TOR_CONTROL_PORT`` / ``SCHOLARLY_TOR_PASSWORD``
    Settings used by ``--proxy tor`` (an already running Tor instance).
"""
import argparse
import asyncio
import datetime
import functools
import inspect
import itertools
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Dict, List, Optional

from ._proxy_generator import DOSException, MaxTriesExceededException

SERVER_NAME = "scholarly"

SERVER_INSTRUCTIONS = (
    "Query Google Scholar for authors, publications, citations and BibTeX through the "
    "`scholarly` library. Google Scholar rate-limits and CAPTCHAs automated clients "
    "aggressively, so keep `limit` values small and avoid repeating identical queries. "
    "Lookups by Google Scholar author id (`scholar_id`) are the most reliable; lookups by "
    "free text return the best match only."
)

#: Hard cap on results returned by a single tool call. Every ~10 results costs one
#: extra HTTP request to Google Scholar, so this also bounds the blast radius of a call.
MAX_RESULTS = 50
DEFAULT_LIMIT = 5

AUTHOR_SECTIONS = ("basics", "indices", "counts", "coauthors", "publications", "public_access")
DEFAULT_AUTHOR_SECTIONS = ("basics", "indices", "counts", "coauthors", "publications")
AUTHOR_SORT_KEYS = ("citedby", "year")
PUBLICATION_SORT_KEYS = ("relevance", "date")

PROXY_CHOICES = ("none", "free", "tor", "scraperapi")
TRANSPORT_CHOICES = ("stdio", "sse", "streamable-http")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


class ProxyConfigError(RuntimeError):
    """Raised when the requested proxy mode cannot be configured."""


#: Attached to empty listings. Google Scholar sometimes answers automated clients with a
#: sign-in/CAPTCHA page instead of an error, which scholarly parses as "no results".
EMPTY_RESULT_NOTE = (
    "No results. This may be a genuine absence of matches, but Google Scholar also returns "
    "empty pages to rate-limited or blocked clients (notably for author searches). Try again "
    "later, vary the query, or run the server with --proxy."
)

#: Failures the calling agent can act on (fix the arguments, retry later, use a proxy).
#: These are reported to the client verbatim. Anything else is treated as a bug and, on
#: MCP SDK 2.x, deliberately not leaked to the client.
ANTICIPATED_ERRORS = (ValueError, MaxTriesExceededException, DOSException)


def _jsonable(obj: Any) -> Any:
    """Recursively convert scholarly objects into JSON-serialisable builtins."""
    if isinstance(obj, Enum):
        return _jsonable(obj.value)
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)


def _clamp_limit(limit: Optional[int], default: int = DEFAULT_LIMIT) -> int:
    """Return ``limit`` constrained to ``1..MAX_RESULTS`` (``default`` when ``None``)."""
    if limit is None:
        limit = default
    return max(1, min(int(limit), MAX_RESULTS))


def _take(iterator: Any, limit: int) -> List[Any]:
    """Return at most ``limit`` items from a (possibly ``None``) iterator."""
    if iterator is None:
        return []
    return list(itertools.islice(iterator, limit))


def _validate_choice(value: str, choices: tuple, name: str) -> str:
    if value not in choices:
        raise ValueError("Invalid %s %r; expected one of: %s" % (name, value, ", ".join(choices)))
    return value


class ScholarlyTools:
    """The logic behind each MCP tool, kept free of any MCP SDK dependency.

    :param api: the ``scholarly`` API object. Defaults to the module level singleton;
                tests inject a fake.
    """

    def __init__(self, api: Any = None):
        if api is None:
            import scholarly as _pkg
            api = _pkg.scholarly
        self.api = api

    # -- helpers -----------------------------------------------------------------
    def _find_publication(self, title: str, filled: bool = False) -> Any:
        """Best-match publication for a title/query, with a clear error if there is none."""
        if not title or not title.strip():
            raise ValueError("title must be a non-empty string")
        try:
            pub = self.api.search_single_pub(title, filled=filled)
        except (StopIteration, IndexError):
            pub = None
        if not pub:
            raise ValueError("No publication found on Google Scholar for %r" % title)
        return pub

    @staticmethod
    def _listing(query: Any, items: List[Any]) -> Dict[str, Any]:
        listing = {"query": query, "count": len(items), "results": _jsonable(items)}
        if not items:
            listing["note"] = EMPTY_RESULT_NOTE
        return listing

    # -- tools -------------------------------------------------------------------
    def search_authors(self, name: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Search authors by name (optionally with affiliation, e.g. ``"Marty Banks, Berkeley"``)."""
        if not name or not name.strip():
            raise ValueError("name must be a non-empty string")
        items = _take(self.api.search_author(name), _clamp_limit(limit))
        return self._listing(name, items)

    def get_author(self, scholar_id: str, sections: Optional[List[str]] = None,
                   sortby: str = "citedby", publication_limit: int = 10) -> Dict[str, Any]:
        """Fetch an author profile by Google Scholar id and fill the requested sections."""
        if not scholar_id or not scholar_id.strip():
            raise ValueError("scholar_id must be a non-empty string")
        sections = list(sections) if sections else list(DEFAULT_AUTHOR_SECTIONS)
        for section in sections:
            _validate_choice(section, AUTHOR_SECTIONS, "section")
        _validate_choice(sortby, AUTHOR_SORT_KEYS, "sortby")
        publication_limit = max(0, int(publication_limit))
        author = self.api.search_author_id(scholar_id)
        author = self.api.fill(author, sections=sections, sortby=sortby,
                               publication_limit=publication_limit)
        return _jsonable(author)

    def search_publications(self, query: str, limit: Optional[int] = None,
                            year_low: Optional[int] = None, year_high: Optional[int] = None,
                            sort_by: str = "relevance", patents: bool = True) -> Dict[str, Any]:
        """Search publications with a free-text Google Scholar query."""
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        _validate_choice(sort_by, PUBLICATION_SORT_KEYS, "sort_by")
        results = self.api.search_pubs(query, patents=patents, year_low=year_low,
                                       year_high=year_high, sort_by=sort_by)
        return self._listing(query, _take(results, _clamp_limit(limit)))

    def get_publication(self, title: str) -> Dict[str, Any]:
        """Return the best-matching publication for a title, with full details filled in."""
        return _jsonable(self._find_publication(title, filled=True))

    def get_bibtex(self, title: str) -> Dict[str, Any]:
        """Return the BibTeX entry of the best-matching publication for a title."""
        pub = self._find_publication(title)
        bibtex = self.api.bibtex(pub)
        if not bibtex:
            raise ValueError("Google Scholar returned no BibTeX for %r" % title)
        return {"title": _jsonable(pub.get("bib", {}).get("title", title)), "bibtex": bibtex}

    def get_citing_publications(self, title: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """List publications that cite the best-matching publication for a title."""
        pub = self._find_publication(title)
        return self._listing(title, _take(self.api.citedby(pub), _clamp_limit(limit, 10)))

    def get_related_articles(self, title: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """List articles Google Scholar considers related to the best-matching publication."""
        pub = self._find_publication(title)
        return self._listing(title, _take(self.api.get_related_articles(pub), _clamp_limit(limit, 10)))


# (tool name, description). Each name is also the ScholarlyTools method that implements it.
TOOL_SPECS = (
    ("search_authors", "Search Google Scholar authors by name."),
    ("get_author", "Fetch a Google Scholar author profile (indices, counts, coauthors, publications)."),
    ("search_publications", "Search Google Scholar publications with a free-text query."),
    ("get_publication", "Get full details of the best-matching publication for a title."),
    ("get_bibtex", "Get the BibTeX entry of the best-matching publication for a title."),
    ("get_citing_publications", "List publications that cite the best-matching publication for a title."),
    ("get_related_articles", "List articles related to the best-matching publication for a title."),
)

_DESCRIPTIONS = dict(TOOL_SPECS)


def configure_proxy(mode: str, api: Any = None, env: Optional[Dict[str, str]] = None) -> None:
    """Route ``scholarly`` traffic through the requested proxy.

    :param mode: one of :data:`PROXY_CHOICES`.
    :raises ProxyConfigError: if the proxy cannot be configured.
    """
    _validate_choice(mode, PROXY_CHOICES, "proxy mode")
    if mode == "none":
        return
    env = os.environ if env is None else env
    if api is None:
        import scholarly as _pkg
        api = _pkg.scholarly
    from ._proxy_generator import ProxyGenerator

    pg = ProxyGenerator()
    if mode == "free":
        ok = pg.FreeProxies()
    elif mode == "scraperapi":
        key = env.get("SCRAPER_API_KEY")
        if not key:
            raise ProxyConfigError("--proxy scraperapi requires the SCRAPER_API_KEY environment variable")
        ok = pg.ScraperAPI(key)
    else:  # tor
        try:
            socks_port = int(env.get("SCHOLARLY_TOR_SOCKS_PORT", 9050))
            control_port = int(env.get("SCHOLARLY_TOR_CONTROL_PORT", 9051))
        except ValueError as exc:
            raise ProxyConfigError("Invalid Tor port in environment: %s" % exc)
        ok = pg.Tor_External(socks_port, control_port, env.get("SCHOLARLY_TOR_PASSWORD", ""))
    if not ok:
        raise ProxyConfigError("Could not set up the %r proxy; scholarly would run unproxied" % mode)
    api.use_proxy(pg)


def _import_server_class():
    """Return ``(server_class, sdk_major)`` for the installed MCP SDK (1.x or 2.x)."""
    try:
        from mcp.server.mcpserver import MCPServer  # mcp >= 2
        return MCPServer, 2
    except ImportError:
        pass
    try:
        from mcp.server.fastmcp import FastMCP  # mcp 1.x
        return FastMCP, 1
    except ImportError:
        raise ImportError(
            "The MCP SDK is required to run scholarly as an MCP server. "
            "Install it with: pip install \"scholarly[mcp]\" (requires Python 3.10+)")


def _tool_error_class(sdk_major: int) -> Any:
    """The MCP SDK's ``ToolError``: the only exception type whose message always reaches the client."""
    if sdk_major == 2:
        from mcp.server.mcpserver.exceptions import ToolError
    else:
        from mcp.server.fastmcp.exceptions import ToolError
    return ToolError


def create_server(api: Any = None, host: str = "127.0.0.1", port: int = 8000) -> Any:
    """Build the MCP server with all scholarly tools registered.

    ``host``/``port`` only matter for the network transports. With mcp 1.x they are
    bound to the server here; with mcp 2.x they are passed to :func:`run_server`.
    """
    server_cls, sdk_major = _import_server_class()
    if sdk_major == 1:
        server = server_cls(SERVER_NAME, instructions=SERVER_INSTRUCTIONS, host=host, port=port)
    else:
        server = server_cls(SERVER_NAME, instructions=SERVER_INSTRUCTIONS)

    tools = ScholarlyTools(api)
    tool_error = _tool_error_class(sdk_major)
    # Scholarly is a stateful singleton (shared session and proxy) and Google Scholar
    # punishes bursts, so run every tool on one worker thread, one call at a time.
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scholarly-mcp")

    # Advertise tools as read-only / open-world when the SDK supports annotations.
    tool_kwargs = {}
    if "annotations" in inspect.signature(server.tool).parameters:
        from mcp.types import ToolAnnotations
        tool_kwargs["annotations"] = ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)

    async def _call(method_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        method = getattr(tools, method_name)
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(executor, functools.partial(method, *args, **kwargs))
        except ANTICIPATED_ERRORS as exc:
            raise tool_error(str(exc) or type(exc).__name__) from exc

    @server.tool(name="search_authors", description=_DESCRIPTIONS["search_authors"], **tool_kwargs)
    async def search_authors(name: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        return await _call("search_authors", name, limit)

    @server.tool(name="get_author", description=_DESCRIPTIONS["get_author"], **tool_kwargs)
    async def get_author(scholar_id: str, sections: Optional[List[str]] = None,
                         sortby: str = "citedby", publication_limit: int = 10) -> Dict[str, Any]:
        return await _call("get_author", scholar_id, sections, sortby, publication_limit)

    @server.tool(name="search_publications", description=_DESCRIPTIONS["search_publications"], **tool_kwargs)
    async def search_publications(query: str, limit: int = DEFAULT_LIMIT,
                                  year_low: Optional[int] = None, year_high: Optional[int] = None,
                                  sort_by: str = "relevance", patents: bool = True) -> Dict[str, Any]:
        return await _call("search_publications", query, limit, year_low, year_high, sort_by, patents)

    @server.tool(name="get_publication", description=_DESCRIPTIONS["get_publication"], **tool_kwargs)
    async def get_publication(title: str) -> Dict[str, Any]:
        return await _call("get_publication", title)

    @server.tool(name="get_bibtex", description=_DESCRIPTIONS["get_bibtex"], **tool_kwargs)
    async def get_bibtex(title: str) -> Dict[str, Any]:
        return await _call("get_bibtex", title)

    @server.tool(name="get_citing_publications", description=_DESCRIPTIONS["get_citing_publications"],
                 **tool_kwargs)
    async def get_citing_publications(title: str, limit: int = 10) -> Dict[str, Any]:
        return await _call("get_citing_publications", title, limit)

    @server.tool(name="get_related_articles", description=_DESCRIPTIONS["get_related_articles"], **tool_kwargs)
    async def get_related_articles(title: str, limit: int = 10) -> Dict[str, Any]:
        return await _call("get_related_articles", title, limit)

    return server


def run_server(server: Any, transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run ``server`` on the given transport (blocks until the server stops)."""
    _validate_choice(transport, TRANSPORT_CHOICES, "transport")
    if transport == "stdio":
        server.run(transport="stdio")
    elif type(server).__name__ == "MCPServer":  # mcp >= 2 takes host/port at run time
        server.run(transport=transport, host=host, port=port)
    else:  # mcp 1.x bound host/port in create_server()
        server.run(transport=transport)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scholarly-mcp",
        description="Run scholarly (Google Scholar) as a Model Context Protocol server.")
    parser.add_argument("--transport", choices=TRANSPORT_CHOICES, default="stdio",
                        help="MCP transport (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="interface to bind for sse/streamable-http (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000,
                        help="port to listen on for sse/streamable-http (default: 8000)")
    parser.add_argument("--proxy", choices=PROXY_CHOICES, default="none",
                        help="proxy for Google Scholar requests; credentials are read from the "
                             "environment (default: none)")
    parser.add_argument("--log-level", choices=LOG_LEVELS, default="WARNING",
                        help="log level, written to stderr (default: WARNING)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point of the ``scholarly-mcp`` console script."""
    args = build_parser().parse_args(argv)

    # stdout carries the MCP protocol on the stdio transport, so log to stderr only.
    logging.basicConfig(level=args.log_level, stream=sys.stderr,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logging.getLogger("scholarly").setLevel(args.log_level)

    try:
        server = create_server(host=args.host, port=args.port)
    except ImportError as exc:
        print("scholarly-mcp: %s" % exc, file=sys.stderr)
        return 2
    try:
        configure_proxy(args.proxy)
    except ProxyConfigError as exc:
        print("scholarly-mcp: %s" % exc, file=sys.stderr)
        return 2

    if args.transport != "stdio" and args.host not in _LOOPBACK_HOSTS:
        logging.getLogger(__name__).warning(
            "Binding %s:%d without authentication; anyone who can reach this port can "
            "drive Google Scholar queries through your proxy and IP.", args.host, args.port)

    try:
        run_server(server, args.transport, args.host, args.port)
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Ctrl+C is how a server is normally stopped by hand, not a failure: don't print a
        # traceback and don't report an error status.
        logging.getLogger(__name__).info("Shutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
