# cheap-pc-searcher

Deep-searches multiple marketplaces for inexpensive PC components and
peripherals, driven by an LLM agent loop, with a compatibility engine that
validates every candidate against a target build you already have.

## Run it

```bash
uv sync
uv run uvicorn cheap_pc_searcher.api.app:app --reload
```

- `GET /` — health check
- `GET /sources` — enabled sources
- `POST /search` — body `{"target_build": {"parts": {"cpu": {...}, ...}}}`;
  returns ranked listings with compatibility `issues` attached
- `GET /compatibility/validate` — quick manual compatibility check

Offline by default: the `mock` source is enabled, so `/search` works with no
API keys. Enable others via env config (see `.env.example`): `ebay` (Browse API
key), `reddit` (OAuth app), `craigslist` (RSS, no key — blocked from datacenter
IPs), and Playwright stubs `newegg` / `amazon` / `facebook`.

## Layout

- `config.py` — `pydantic-settings` env config (`.env`) driving the registry
- `models.py` — `Part`, `Listing`, `TargetBuild`, `CompatibilityIssue`
- `normalize.py` — messy marketplace title → typed `Part` (regex heuristics, LLM hook)
- `compatibility/engine.py` — pure-function rules (socket, DDR gen, GPU length)
- `agent/loop.py` — plan → fan out → normalize → compat-check → rank
- `sources/` — one ABC, N adapters (mock, ebay, reddit, craigslist, stubs), config-driven registry
- `api/app.py` — FastAPI endpoints

See `PLAN.md` for the full architecture and roadmap.
