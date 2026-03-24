# Codebase improvement plan

This document summarizes high-impact opportunities to improve maintainability, reliability, and release quality for `scholarly`.

## 1) Modernize packaging metadata (high impact, low-medium effort)

### Current state
- `pyproject.toml` only declares the build backend, while package metadata and dependencies are still maintained in `setup.py`.
- `setup.py` still marks the package as `Development Status :: 3 - Alpha`.
- Test configuration uses a legacy `test_suite` setting.

### Why improve
- Keeping metadata in a single source of truth (`pyproject.toml` under PEP 621) reduces drift between tools.
- A modern packaging layout improves compatibility with build tooling and dependency scanners.

### Recommended actions
1. Move project metadata and dependencies from `setup.py` into `pyproject.toml` (`[project]`, `[project.optional-dependencies]`).
2. Keep `setup.py` as a thin compatibility shim (or remove when downstream tooling allows).
3. Add tool config blocks for formatter/linter/test runner (`[tool.pytest.ini_options]`, etc.) if adopted.
4. Revisit package classifier maturity to match actual support expectations.

---

## 2) Split online integration tests from deterministic unit tests (high impact, medium effort)

### Current state
- `test_module.py` performs many live requests against Google Scholar and free-proxy providers.
- The default setup path calls `FreeProxies()` and can fail in CI/restricted networks with proxy errors.

### Why improve
- Network and anti-bot behavior make these tests flaky and environment-dependent.
- Contributors cannot reliably run tests offline.

### Recommended actions
1. Introduce explicit test markers/categories:
   - `unit` (pure parsing/logic, deterministic)
   - `integration` (live network)
2. Move parsing assertions to fixture-based tests with stored HTML snippets.
3. Gate live tests behind an opt-in env var (for example `SCHOLARLY_RUN_LIVE_TESTS=1`) and skip by default.
4. Add CI matrix stages for quick deterministic checks vs scheduled/optional live checks.

---

## 3) Tighten exception boundaries and diagnostics around proxy/navigation (high impact, medium effort)

### Current state
- Navigation/proxy code contains many broad `except Exception` handlers.
- Retries are spread across navigator and proxy layers with mixed logging detail.

### Why improve
- Broad exception handling can hide root causes.
- Harder to reason about retry policy and failure modes across multiple connection paths.

### Recommended actions
1. Replace generic catches with specific exception classes where feasible (`requests`, `httpx`, Selenium, parsing errors).
2. Standardize retry policy in one place (max attempts, backoff, timeout growth).
3. Return/raise structured errors that preserve context (request URL, proxy mode, status code).
4. Add focused unit tests for retry/fallback paths with mocked sessions.

---

## 4) Improve API typing and static analysis coverage (medium impact, medium effort)

### Current state
- Some modules have selective type hints; many public methods still have partial/no type coverage.
- Dynamic dictionary payloads are common and can be error-prone.

### Why improve
- Better typing helps contributors navigate the code and reduces regressions.
- Static analysis can catch interface mismatches early.

### Recommended actions
1. Incrementally type annotate public methods in `_scholarly.py`, `_navigator.py`, and parsers.
2. Introduce `TypedDict`/dataclass models for frequently used payload shapes.
3. Add `mypy` (or pyright) in non-blocking mode first, then tighten gradually.

---

## 5) Documentation and contributor experience upgrades (medium impact, low effort)

### Current state
- README and docs are comprehensive but test execution guidance assumes network-dependent flows.
- Contributor guidance could more clearly separate quick local checks from full integration validation.

### Why improve
- Faster onboarding and fewer false-negative test runs for external contributors.

### Recommended actions
1. Add a short “Local development quick checks” section with deterministic commands.
2. Document required environment variables/services for each integration test category.
3. Add troubleshooting notes for common proxy/network failures.

---

## Quick wins already applied in this branch

- Replaced two identity assertions (`assertIs(..., 0)`) with value assertions (`assertEqual(..., 0)`) in tests.
- Fixed a typo in a test docstring (`fiile` -> `file`).

These are small quality improvements that reduce brittle test style and clean up minor docs noise.
