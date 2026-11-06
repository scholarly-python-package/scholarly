Running scholarly as an MCP server
==================================

``scholarly`` can run as a `Model Context Protocol <https://modelcontextprotocol.io/>`_ (MCP)
server, so that LLM agents and other MCP clients can query Google Scholar as a tool.
The MCP layer is optional and needs Python 3.10 or newer::

    pip3 install scholarly[mcp]

It works with both the 1.x (``FastMCP``) and 2.x (``MCPServer``) generations of the
`MCP Python SDK <https://github.com/modelcontextprotocol/python-sdk>`_.

Launching the server
--------------------

The ``scholarly-mcp`` command (equivalently ``python -m scholarly.mcp``) starts the server::

    scholarly-mcp                                   # stdio transport (default)
    scholarly-mcp --transport sse --port 8000
    scholarly-mcp --transport streamable-http --host 127.0.0.1 --port 8000
    scholarly-mcp --proxy free --log-level INFO

``--transport``
    ``stdio`` (default) for clients that start the server themselves, or the network
    transports ``sse`` and ``streamable-http``.
``--host`` / ``--port``
    Interface and port of the network transports (default ``127.0.0.1:8000``). The network
    transports have **no authentication**, so only bind a non-loopback address on a trusted
    network; the server logs a warning when you do.
``--proxy``
    ``none`` (default), ``free``, ``tor`` or ``scraperapi``. This configures the same
    :class:`ProxyGenerator <scholarly.ProxyGenerator>` that the Python API uses, and the server
    refuses to start if the proxy cannot be set up rather than silently running unproxied.
``--log-level``
    Logging threshold. Logs are written to ``stderr`` because ``stdout`` carries the protocol
    on the ``stdio`` transport.

Credentials are read from the environment, never from command line flags, so that they do not
appear in process listings:

``SCRAPER_API_KEY``
    API key for ``--proxy scraperapi``.
``SCHOLARLY_TOR_SOCKS_PORT``, ``SCHOLARLY_TOR_CONTROL_PORT``, ``SCHOLARLY_TOR_PASSWORD``
    Settings of an already running Tor instance for ``--proxy tor`` (defaults ``9050``, ``9051``
    and an empty password).

A ``.env`` file is honoured, as for the Python API.

Client configuration
--------------------

For clients that launch the server (for example Claude Desktop)::

    {
      "mcpServers": {
        "scholarly": {
          "command": "scholarly-mcp",
          "args": ["--proxy", "free"]
        }
      }
    }

Tools
-----

All tools are read-only and take plain names, identifiers or titles, because an MCP client
cannot hold on to ``Author`` or ``Publication`` objects between calls. Results are plain JSON.
Tools that return a list accept a ``limit`` (at most 50 per call).

``search_authors(name, limit=5)``
    Search authors by name, optionally with an affiliation, e.g. ``"Marty Banks, Berkeley"``.
``get_author(scholar_id, sections=None, sortby="citedby", publication_limit=10)``
    Fetch an author profile by Google Scholar id. ``sections`` is any of ``basics``, ``indices``,
    ``counts``, ``coauthors``, ``publications`` and ``public_access`` (default: all but
    ``public_access``). ``publication_limit=0`` fetches every publication.
``search_publications(query, limit=5, year_low=None, year_high=None, sort_by="relevance", patents=True)``
    Search publications with a free-text query.
``get_publication(title)``
    Full details of the best match for a title.
``get_bibtex(title)``
    BibTeX entry of the best match for a title.
``get_citing_publications(title, limit=10)``
    Publications that cite the best match for a title.
``get_related_articles(title, limit=10)``
    Articles related to the best match for a title.

Calls are executed one at a time. ``scholarly`` keeps a single stateful session and Google
Scholar penalises bursts, so concurrent requests would only make blocking more likely.

Errors and limitations
----------------------

Invalid arguments, "no such publication" and Google Scholar refusing to serve the request are
reported to the client as tool errors with an explanatory message. Unexpected internal errors are
reported as errors too; SDK 2.x deliberately withholds their details from the client.

Google Scholar sometimes answers a blocked client with a sign-in or CAPTCHA page rather than an
error, which ``scholarly`` parses as "no results". Empty listings therefore carry a ``note``
explaining that an empty result can mean "blocked". Keep ``limit`` small, avoid repeating
identical queries, and use ``--proxy`` (see "Using proxies" in the :doc:`quickstart`).
