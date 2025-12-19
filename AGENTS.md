# Repository Guidelines

Contributor notes for the MCP OCI OPSI server. Keep changes small, documented, and runnable.

## Project Structure & Module Organization
- `mcp_oci_opsi/`: core package; `python -m mcp_oci_opsi` picks `main_v3.py` (default) or `main.py` when `MCP_VERSION=v2`. Subfolders: `servers/` (cache, opsi, dbm, admin), `auth/`, and `tools_*.py` modules for cache, OPSI, DB management, profiles, and skills.
- `scripts/`: setup and cache automation (`setup_and_build.sh`, `quick_cache_build.sh`, `tenancy_review.py`).
- `docs/`, `wiki/`, `Screenshots/`, `skills/`: user guides, troubleshooting, visuals, and workflow prompts.
- `terraform/`: optional OCI VM deployment; `docker-compose.yml` and `Dockerfile` for HTTP transport dev runs.
- Tests sit at repository root (`test_all_mcp_tools.py`, `test_macs_direct.py`, etc.); keep new tests as `test_*.py`.

## Build, Test, and Development Commands
- Env + install: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev,database]"` (or `uv pip install -e ".[dev,database]"`).
- Cache + setup: `./scripts/setup_and_build.sh [--profile PROFILE]`; fast refresh: `./scripts/quick_cache_build.sh`.
- Run server: `python -m mcp_oci_opsi` (default `MCP_VERSION=v2`, stdio). Network transports: `MCP_TRANSPORT=http|sse|streamable-http MCP_PORT=8000 python -m mcp_oci_opsi`.
- Note: `MCP_VERSION=v3` runs a local bootstrap/CLI helper and does not start an MCP server.
- Tests: `pytest`; `pytest --cov=mcp_oci_opsi`; scope with `pytest -k "<keyword>"`.
- Format/lint: `ruff check mcp_oci_opsi` and `black mcp_oci_opsi` (line length 100).

## Coding Style & Naming Conventions
- Python 3.10+, Pydantic models, and type hints; prefer Google-style docstrings.
- `snake_case` for functions/variables, `CamelCase` for classes, `UPPER_SNAKE` for constants. Tool code stays in `tools_*.py`; shared server logic goes in `servers/*.py`.
- Keep functions small; log OCI errors with context, avoid printing secrets; return structured dicts for MCP responses.
- New prompts/skills belong in `skills/`; keep names descriptive (`sql_performance.skill.json`).

## Testing Guidelines
- Stub OCI clients or reuse cached sample data; avoid hitting real tenancies. Keep fixtures near tests or in light helpers.
- Name tests by behavior (`test_cache_expiry_updates`, `test_opsi_sql_stats_limits`). Maintain isolation—no writes outside temp dirs; cache outputs belong in user home only when unavoidable.
- Cover new tool parameters, error paths, and backward compatibility (v2 vs v3 selection).

## Commit & Pull Request Guidelines
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`); reference issue IDs when applicable.
- Before pushing: run `ruff`, `black`, and `pytest`; update docs if behavior or setup changes.
- Pull requests should include a short description, testing notes (commands run), and screenshots/output snippets when changing prompts, cache visuals, or HTTP responses. Keep secrets, OCIDs, and tenancy names out of commits and examples.
