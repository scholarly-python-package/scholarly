"""Unit tests for ``scholarly.mcp`` (the optional MCP server).

These tests are fully offline: the scholarly API is replaced by a fake, so no request
is ever sent to Google Scholar. Tests that need the MCP SDK (Python 3.10+) are skipped
when it is not installed; everything else also runs on older Python versions.
"""
import asyncio
import datetime
import importlib.util
import sys
import threading
import time
import unittest
from enum import Enum
from unittest import mock

from scholarly import mcp as smcp

HAS_SDK = sys.version_info >= (3, 10) and importlib.util.find_spec("mcp") is not None
needs_sdk = unittest.skipUnless(HAS_SDK, "the MCP SDK (pip install 'scholarly[mcp]', Python 3.10+) is not installed")


class FakeApi:
    """Stands in for the ``scholarly`` singleton and records how it was called."""

    def __init__(self):
        self.calls = []
        self.proxy = None
        self.bibtex_text = "@article{x, title={T}}"
        self.single_pub = {"bib": {"title": "A paper"}, "container_type": "Publication"}
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def search_author(self, name):
        self.calls.append(("search_author", name))
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(0.05)
        with self._lock:
            self.active -= 1
        return iter({"name": "Ada %d" % i, "scholar_id": "ID%d" % i} for i in range(100))

    def search_author_id(self, scholar_id):
        self.calls.append(("search_author_id", scholar_id))
        return {"scholar_id": scholar_id, "filled": False}

    def fill(self, obj, sections=None, sortby="citedby", publication_limit=0):
        self.calls.append(("fill", sections, sortby, publication_limit))
        return dict(obj, filled=True, sections=list(sections))

    def search_pubs(self, query, **kwargs):
        self.calls.append(("search_pubs", query, kwargs))
        return iter({"bib": {"title": "Pub %d" % i}} for i in range(100))

    def search_single_pub(self, title, filled=False):
        self.calls.append(("search_single_pub", title, filled))
        if isinstance(self.single_pub, Exception):
            raise self.single_pub
        return self.single_pub

    def bibtex(self, pub):
        return self.bibtex_text

    def citedby(self, pub):
        return iter({"bib": {"title": "Citing %d" % i}} for i in range(100))

    def get_related_articles(self, pub):
        return iter({"bib": {"title": "Related %d" % i}} for i in range(100))

    def use_proxy(self, pg):
        self.proxy = pg


class TestHelpers(unittest.TestCase):
    def test_jsonable_converts_enums_dates_and_unknown_objects(self):
        class Color(str, Enum):
            RED = "red"

        class Odd:
            def __str__(self):
                return "odd"

        data = {"c": Color.RED, "when": datetime.date(2026, 10, 30), "t": (1, 2), "s": {3},
                "n": None, "o": Odd(), 5: [Color.RED]}
        self.assertEqual(smcp._jsonable(data),
                         {"c": "red", "when": "2026-10-30", "t": [1, 2], "s": [3],
                          "n": None, "o": "odd", "5": ["red"]})

    def test_clamp_limit(self):
        self.assertEqual(smcp._clamp_limit(None), smcp.DEFAULT_LIMIT)
        self.assertEqual(smcp._clamp_limit(None, 10), 10)
        self.assertEqual(smcp._clamp_limit(0), 1)
        self.assertEqual(smcp._clamp_limit(-4), 1)
        self.assertEqual(smcp._clamp_limit(10 ** 6), smcp.MAX_RESULTS)

    def test_take_handles_none_and_short_iterators(self):
        self.assertEqual(smcp._take(None, 3), [])
        self.assertEqual(smcp._take(iter([1, 2]), 5), [1, 2])
        self.assertEqual(smcp._take(iter(range(10)), 3), [0, 1, 2])


class TestScholarlyTools(unittest.TestCase):
    def setUp(self):
        self.api = FakeApi()
        self.tools = smcp.ScholarlyTools(self.api)

    def test_search_authors_respects_limit(self):
        out = self.tools.search_authors("Ada Lovelace", 3)
        self.assertEqual((out["query"], out["count"], len(out["results"])), ("Ada Lovelace", 3, 3))

    def test_search_authors_caps_limit_at_max_results(self):
        self.assertEqual(self.tools.search_authors("Ada", 10 ** 6)["count"], smcp.MAX_RESULTS)

    def test_search_authors_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            self.tools.search_authors("   ")

    def test_get_author_uses_default_sections_and_publication_limit(self):
        out = self.tools.get_author("ABC123")
        self.assertTrue(out["filled"])
        self.assertEqual(out["sections"], list(smcp.DEFAULT_AUTHOR_SECTIONS))
        self.assertIn(("fill", list(smcp.DEFAULT_AUTHOR_SECTIONS), "citedby", 10), self.api.calls)

    def test_get_author_validates_inputs(self):
        with self.assertRaises(ValueError):
            self.tools.get_author("ABC", sections=["nonsense"])
        with self.assertRaises(ValueError):
            self.tools.get_author("ABC", sortby="alphabet")
        with self.assertRaises(ValueError):
            self.tools.get_author("")

    def test_get_author_zero_publication_limit_means_unlimited_and_negative_is_clamped(self):
        self.tools.get_author("ABC", publication_limit=-5)
        self.assertEqual(self.api.calls[-1][3], 0)

    def test_search_publications_forwards_filters(self):
        out = self.tools.search_publications("deep learning", 2, year_low=2020, year_high=2024,
                                             sort_by="date", patents=False)
        self.assertEqual(out["count"], 2)
        _, query, kwargs = [c for c in self.api.calls if c[0] == "search_pubs"][0]
        self.assertEqual(query, "deep learning")
        self.assertEqual(kwargs, {"patents": False, "year_low": 2020, "year_high": 2024, "sort_by": "date"})

    def test_search_publications_validates_sort_by(self):
        with self.assertRaises(ValueError):
            self.tools.search_publications("q", sort_by="newest")

    def test_missing_publication_becomes_a_clear_error(self):
        for missing in (None, {}, IndexError("empty"), StopIteration()):
            self.api.single_pub = missing
            with self.assertRaisesRegex(ValueError, "No publication found"):
                self.tools.get_publication("nothing")

    def test_get_publication_asks_for_a_filled_record(self):
        self.tools.get_publication("A paper")
        self.assertIn(("search_single_pub", "A paper", True), self.api.calls)

    def test_get_bibtex(self):
        out = self.tools.get_bibtex("A paper")
        self.assertEqual(out, {"title": "A paper", "bibtex": "@article{x, title={T}}"})

    def test_get_bibtex_errors_when_scholar_returns_nothing(self):
        self.api.bibtex_text = None
        with self.assertRaisesRegex(ValueError, "no BibTeX"):
            self.tools.get_bibtex("A paper")

    def test_citing_and_related_listings(self):
        self.assertEqual(self.tools.get_citing_publications("A paper", 4)["count"], 4)
        self.assertEqual(self.tools.get_related_articles("A paper", 2)["count"], 2)

    def test_empty_listings_explain_that_blocking_is_possible(self):
        self.api.search_author = lambda name: iter([])
        out = self.tools.search_authors("Nobody")
        self.assertEqual((out["count"], out["results"]), (0, []))
        self.assertIn("blocked", out["note"])
        self.assertNotIn("note", smcp.ScholarlyTools(FakeApi()).search_authors("Ada", 1))

    def test_citing_and_related_tolerate_none(self):
        self.api.citedby = lambda pub: None
        self.api.get_related_articles = lambda pub: None
        self.assertEqual(self.tools.get_citing_publications("A paper")["results"], [])
        self.assertEqual(self.tools.get_related_articles("A paper")["results"], [])


class TestConfigureProxy(unittest.TestCase):
    def setUp(self):
        self.api = FakeApi()
        patcher = mock.patch("scholarly._proxy_generator.ProxyGenerator")
        self.PG = patcher.start()
        self.addCleanup(patcher.stop)
        self.pg = self.PG.return_value

    def test_none_is_a_no_op(self):
        smcp.configure_proxy("none", self.api, env={})
        self.PG.assert_not_called()
        self.assertIsNone(self.api.proxy)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            smcp.configure_proxy("carrier-pigeon", self.api, env={})

    def test_free(self):
        self.pg.FreeProxies.return_value = True
        smcp.configure_proxy("free", self.api, env={})
        self.assertIs(self.api.proxy, self.pg)

    def test_failure_to_configure_is_an_error_not_a_silent_fallback(self):
        self.pg.FreeProxies.return_value = False
        with self.assertRaises(smcp.ProxyConfigError):
            smcp.configure_proxy("free", self.api, env={})
        self.assertIsNone(self.api.proxy)

    def test_scraperapi_reads_key_from_env_only(self):
        self.pg.ScraperAPI.return_value = True
        smcp.configure_proxy("scraperapi", self.api, env={"SCRAPER_API_KEY": "k"})
        self.pg.ScraperAPI.assert_called_once_with("k")

    def test_scraperapi_without_key(self):
        with self.assertRaisesRegex(smcp.ProxyConfigError, "SCRAPER_API_KEY"):
            smcp.configure_proxy("scraperapi", self.api, env={})

    def test_tor_uses_defaults_and_env_overrides(self):
        self.pg.Tor_External.return_value = True
        smcp.configure_proxy("tor", self.api, env={})
        self.pg.Tor_External.assert_called_with(9050, 9051, "")
        smcp.configure_proxy("tor", self.api, env={"SCHOLARLY_TOR_SOCKS_PORT": "1",
                                                   "SCHOLARLY_TOR_CONTROL_PORT": "2",
                                                   "SCHOLARLY_TOR_PASSWORD": "pw"})
        self.pg.Tor_External.assert_called_with(1, 2, "pw")

    def test_tor_rejects_bad_port(self):
        with self.assertRaises(smcp.ProxyConfigError):
            smcp.configure_proxy("tor", self.api, env={"SCHOLARLY_TOR_SOCKS_PORT": "abc"})


class TestCli(unittest.TestCase):
    def test_defaults(self):
        args = smcp.build_parser().parse_args([])
        self.assertEqual((args.transport, args.host, args.port, args.proxy, args.log_level),
                         ("stdio", "127.0.0.1", 8000, "none", "WARNING"))

    def test_rejects_unknown_transport(self):
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            smcp.build_parser().parse_args(["--transport", "carrier-pigeon"])

    def test_main_reports_missing_sdk_with_exit_code_2(self):
        with mock.patch.object(smcp, "_import_server_class", side_effect=ImportError("install mcp")), \
                mock.patch("sys.stderr") as err:
            self.assertEqual(smcp.main([]), 2)
        self.assertIn("install mcp", "".join(c.args[0] for c in err.write.call_args_list))

    def test_main_reports_proxy_failure_with_exit_code_2(self):
        with mock.patch.object(smcp, "create_server"), \
                mock.patch.object(smcp, "configure_proxy", side_effect=smcp.ProxyConfigError("nope")), \
                mock.patch.object(smcp, "run_server") as run, mock.patch("sys.stderr"):
            self.assertEqual(smcp.main(["--proxy", "free"]), 2)
        run.assert_not_called()

    def test_main_wires_arguments_through(self):
        with mock.patch.object(smcp, "create_server") as create, \
                mock.patch.object(smcp, "configure_proxy") as proxy, \
                mock.patch.object(smcp, "run_server") as run:
            code = smcp.main(["--transport", "sse", "--host", "127.0.0.1", "--port", "9001", "--proxy", "free"])
        self.assertEqual(code, 0)
        create.assert_called_once_with(host="127.0.0.1", port=9001)
        proxy.assert_called_once_with("free")
        run.assert_called_once_with(create.return_value, "sse", "127.0.0.1", 9001)

    def test_main_warns_when_binding_a_non_loopback_address(self):
        with mock.patch.object(smcp, "create_server"), mock.patch.object(smcp, "configure_proxy"), \
                mock.patch.object(smcp, "run_server"), self.assertLogs("scholarly.mcp", "WARNING") as logs:
            smcp.main(["--transport", "streamable-http", "--host", "0.0.0.0"])
        self.assertIn("without authentication", logs.output[0])

    def test_run_server_dispatch_for_both_sdk_generations(self):
        class MCPServer:  # mcp >= 2: host/port are given at run time
            def run(self, **kwargs):
                self.kwargs = kwargs

        class FastMCP:  # mcp 1.x: host/port were bound at construction
            def run(self, **kwargs):
                self.kwargs = kwargs

        v2, v1 = MCPServer(), FastMCP()
        smcp.run_server(v2, "sse", "127.0.0.1", 9)
        smcp.run_server(v1, "sse", "127.0.0.1", 9)
        self.assertEqual(v2.kwargs, {"transport": "sse", "host": "127.0.0.1", "port": 9})
        self.assertEqual(v1.kwargs, {"transport": "sse"})
        smcp.run_server(v2, "stdio")
        self.assertEqual(v2.kwargs, {"transport": "stdio"})
        with self.assertRaises(ValueError):
            smcp.run_server(v2, "carrier-pigeon")


def _payload(result):
    """Extract the structured tool output from either SDK generation's call_tool result."""
    structured = result[1] if isinstance(result, tuple) else result.structured_content
    return structured["result"]


@needs_sdk
class TestServer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.api = FakeApi()
        self.server = smcp.create_server(self.api)

    async def test_registers_every_tool(self):
        tools = await self.server.list_tools()
        self.assertEqual([t.name for t in tools], [name for name, _ in smcp.TOOL_SPECS])
        for tool in tools:
            self.assertTrue(tool.description)

    async def test_tools_are_advertised_as_read_only(self):
        for tool in await self.server.list_tools():
            if tool.annotations is None:  # very old SDKs without annotations
                continue
            hints = tool.annotations.model_dump(by_alias=True)
            self.assertTrue(hints["readOnlyHint"])
            self.assertTrue(hints["openWorldHint"])
            self.assertFalse(hints["destructiveHint"])

    async def test_call_tool_end_to_end(self):
        out = _payload(await self.server.call_tool("search_authors", {"name": "Ada", "limit": 2}))
        self.assertEqual((out["query"], out["count"]), ("Ada", 2))
        out = _payload(await self.server.call_tool("get_bibtex", {"title": "A paper"}))
        self.assertEqual(out["bibtex"], self.api.bibtex_text)

    async def _error_text(self, tool, arguments):
        """Call a tool that must fail; return whatever error text the client would see."""
        try:
            result = await self.server.call_tool(tool, arguments)
        except Exception as exc:  # mcp raises ...
            return str(exc)
        # ... or returns an error result
        self.assertTrue(getattr(result, "is_error", False), "tool unexpectedly succeeded: %r" % (result,))
        return str(result)

    async def test_tool_errors_reach_the_client(self):
        self.api.single_pub = None
        self.assertIn("No publication found", await self._error_text("get_publication", {"title": "nothing"}))

    async def test_bad_arguments_reach_the_client(self):
        text = await self._error_text("search_publications", {"query": "q", "sort_by": "newest"})
        self.assertIn("Invalid sort_by", text)

    async def test_google_scholar_blocking_is_explained_to_the_client(self):
        self.api.single_pub = smcp.MaxTriesExceededException("Cannot fetch from Google Scholar.")
        self.assertIn("Cannot fetch from Google Scholar", await self._error_text("get_bibtex", {"title": "x"}))

    async def test_unexpected_crashes_are_reported_as_errors_not_successes(self):
        self.api.single_pub = RuntimeError("internal detail /secret/path")
        text = await self._error_text("get_bibtex", {"title": "x"})
        self.assertIn("get_bibtex", text)  # an error was reported; SDK 2.x withholds the detail

    async def test_calls_are_serialised_onto_one_worker_thread(self):
        await asyncio.gather(*(self.server.call_tool("search_authors", {"name": "Ada %d" % i})
                               for i in range(4)))
        self.assertEqual(self.api.max_active, 1)
        self.assertEqual(len([c for c in self.api.calls if c[0] == "search_author"]), 4)


if __name__ == "__main__":
    unittest.main()
