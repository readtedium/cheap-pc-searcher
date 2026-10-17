# cheap-pc-searcher — Project Plan

A Python tool that **deep-searches multiple marketplaces** for inexpensive PC
components *and* peripherals, driven by an **LLM agent loop**, with a
**compatibility engine** that validates every candidate against a *target build*
the user already has.

This document is the agreed **project starter** scope: it should run end-to-end
on day one (mock/offline data) and leave clear seams for the team to fill in.

---

## Goal

- Find cheap PC parts across many sites.
- Surface **unexpected** parts (serendipity), not just exact keyword matches.
- Keep **compatibility** front-and-center: every result is validated against the
  user's target build.

---

## Proposed architecture

```
cheap-pc-searcher/
├── pyproject.toml            # uv-managed; deps + optional extras
├── .env.example              # API keys (LLM, eBay, SerpApi…)
├── README.md                 # architecture + "where to plug in"
├── src/cheap_pc_searcher/
│   ├── config.py             # pydantic-settings, typed env
│   ├── models.py             # Part, Listing, TargetBuild, CompatibilityIssue
│   ├── normalize.py          # raw listing text -> typed Part (heuristics + LLM hook)
│   ├── compatibility/
│   │   ├── rules.py          # socket, DDR gen, form factor, PSU wattage, GPU length…
│   │   └── engine.py         # runs rules against a TargetBuild -> report
│   ├── sources/
│   │   ├── base.py           # Source ABC: async search(query) -> list[Listing]
│   │   ├── registry.py       # name -> adapter, enabled from config
│   │   ├── mock.py           # fixture-backed, always works (tests/demo)
│   │   ├── ebay.py           # real: eBay Browse API
│   │   ├── craigslist.py     # real: RSS search feed, no key
│   │   └── _stubs.py         # Newegg / Amazon / FB Marketplace TODO shells (Playwright)
│   ├── agent/
│   │   ├── llm.py            # provider-agnostic OpenAI-compatible client + offline fake
│   │   ├── prompts.py        # query-planning + reflection prompts
│   │   └── loop.py           # the deep-search agent loop
│   ├── service.py            # orchestrates: plan -> fan out -> normalize -> score
│   └── api/
│       ├── app.py            # FastAPI app + static mount
│       └── routes.py         # POST /search, GET /sources, POST /compatibility
├── web/index.html            # single-file UI (no build step), results table + filters
└── tests/                    # compatibility rules + source adapters + loop
```

---

## Stack (and why)

| Choice | Rationale |
|---|---|
| **FastAPI + uvicorn** | Async-native, so fanning out to many sources is trivial; matches the "web UI" choice |
| **Pydantic v2 + pydantic-settings** | One typed model for parts/listings; env config validated at startup |
| **httpx** | Async HTTP for API sources |
| **Playwright (optional extra)** | Only for JS-heavy sites (Newegg/Amazon) — not needed to run the starter |
| **Provider-agnostic LLM client** | Thin OpenAI-compatible wrapper + an offline "fake" so the demo/tests never need a key. Works with Gemini/OpenRouter/Ollama/local |
| **Static `web/index.html`** | Zero build step; team can swap in React later without touching the API |

Deliberately avoiding heavier frameworks (Scrapy, LangChain) in the starter —
they add ceremony before the loop is proven. Easy to add later.

## Run locally

Install the API dependencies and start FastAPI from the repository root:

```sh
python -m pip install fastapi pydantic uvicorn
python -m uvicorn cheap_pc_searcher.api.app:app --app-dir src --reload
```

Open `http://127.0.0.1:8000/` to use the frontend. The same server provides
`GET /health`, `GET /sources`, and `POST /search`.

---

## The five subsystems

1. **Sources** — one ABC, N adapters. Each returns raw `Listing`s. Adding a site
   = one file + one registry line. The natural place for teammates to parallelize.
2. **Normalizer** — the hard, high-value part: turning messy titles
   ("AMD Ry 5 5600 6-core AM4") into a typed `Part(category, specs)`. Ship
   deterministic regex/keyword rules first, with an `LLMNormalizer` hook for the
   weird cases.
3. **Compatibility engine** — *pure functions*, fully unit-testable, no network.
   Rules: CPU socket <-> mobo, mobo <-> DDR4/DDR5, case form factor <-> mobo,
   PSU wattage >= estimated load, case clearance <-> GPU length, cooler <-> socket.
   Returns issue objects with severity.
4. **Agent loop** — iterative: plan queries -> fan out -> normalize ->
   score/compat-check -> reflect (new queries, category pivots) -> repeat up to
   `max_rounds`. Exposes `search_parts` and `check_compatibility` as tools to the LLM.
5. **API + UI** — `POST /search` returns ranked, compat-annotated deals; the page
   renders a filterable table.

---

## The "unexpected parts" feature (the differentiator)

Three mechanisms in the loop:

- **Query expansion** — the LLM generates spec-level and synonym variants
  ("AM4 cpu", "5600X used", "ryzen 5 6 core") so oddball listings surface.
- **Category pivoting / cross-sell** — after finding a CPU deal, speculate on
  adjacent categories the target build might upgrade.
- **Serendipity scoring** — reward listings that *match the specs* but have
  *unusual titles or mis-categorized placement* (e.g. "gaming PC parts lot"
  containing a usable GPU). This is where "deep search" beats keyword search.

---

## Hackathon team split (suggested)

- **A:** sources + normalization (data-in)
- **B:** compatibility rules + engine + tests (correctness)
- **C:** agent loop + LLM client + scoring (the "deep" part)
- **D:** FastAPI + `web/index.html` (the shell), plus README/demo

---

## Build order

1. `pyproject.toml`, config, models — the shared vocabulary
2. Compatibility engine + tests (no deps on anything else)
3. Mock source + normalizer -> **end-to-end run with fake data**
4. Agent loop with the offline LLM -> **demoable without any API key**
5. Real sources (eBay, Craigslist) + stubs
6. API + UI, then wire the live LLM

---

## Open decisions

1. **Stack OK?** FastAPI + static HTML + httpx, or a React frontend / different
   web framework?
2. **Start runnable offline** (mock source + fake LLM, then add keys)?
   *Recommended: yes.*
3. **Scaffold depth:** pure skeleton with `TODO`s, or working stubs for the
   compatibility engine + mock source + loop so the team can run it immediately?
   *Recommended: the latter.*
4. **Target-build input:** JSON in the request body to start, or a small
   "paste your parts" form in the UI?

**Current working default:** FastAPI + static UI, runs offline first, working
compatibility engine + mock source, JSON target build.

---

## Community Wisdom (dev.to)

- [Building an Autonomous Competitor Price Monitor with Python, Playwright, and Discord](https://dev.to/reigen/building-an-autonomous-competitor-price-monitor-with-python-playwright-and-discord-zero-saas-ama) — pairs Playwright with SQLite for a self-hosted price engine instead of paying for SaaS.
- [How to Scrape E-Commerce Sites for AI Agents Using Playwright and LLMs](https://dev.to/alterlab/how-to-scrape-e-commerce-sites-for-ai-agents-using-playwright-and-llms-j5g) — agents want structured JSON from the scrape layer, not raw HTML; that is the normalizer's job.
- [Your Agent Is Paying an LLM to Run a For-Loop](https://dev.to/mech_app_ai/your-agent-is-paying-an-llm-to-run-a-for-loop-why-most-agent-harnesses-route-every-tool-call-2ggf) — keep deterministic logic (compatibility checking) out of the model's inference path.
- [Production-Ready FastAPI Project Structure (2026 Guide)](https://dev.to/datanestdigital/production-ready-fastapi-project-structure-2026-guide-b1g) — concrete FastAPI layout worth mirroring.
- [Why Memory Compatibility (QVL) Matters on Modern DDR5 Systems](https://dev.to/bios-doctor/why-memory-compatibility-qvl-matters-on-modern-ddr5-systems-2689) — DDR5 compatibility is subtler than "DDR5 fits DDR5."

---

## Event context

Built during **Hacktoberfest Hack Day Hampton x RevolutionVA** (MLH, Oct 17, 2026),
and it fits the live DEV Challenge **Hacktoberfest Open-Source AI: Week 2 —
"Side Hustle"** (through Oct 18, tag `#hf26challenge`): build something with
open-source AI someone would actually pay for.

Relevant prize categories: **Best Use of SerpApi** (search), **MongoDB Atlas**
(storage), **Tiger Data** (price history / time-series), **DigitalOcean**
(hosting), **Render**, **Gemma** (open weights).
