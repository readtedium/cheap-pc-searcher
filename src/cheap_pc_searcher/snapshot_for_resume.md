# Project Snapshot: Cheap PC Searcher
**Status:** Core logic complete; transitioning from Mock to Real implementations.
**Last successful logical state:** Agent Loop, Normalizer, and Compatibility Engine are architected.

## 1. Completed Components
- **Models (`src/cheap_pc_searcher/models.py`)**: `Part`, `Listing`, `TargetBuild`, `Severity`, `Condition`, `PartCategory`, `CompatibilityIssue`.
- **Normalizer (`src/cheap_pc_searcher/normalize.py`)**: Hybrid approach (Regex + Scaling to LLM) for messy titles.
- **Compatibility Engine (`src/cheap_pc_searcher/compatibility/engine.py`)**: Rules for Socket, DDR Gen, and GPU Length.
- **Agent Loop (`src/cheap_pc_searcher/agent/loop.py`)**: Orchestration (Plan $\rightarrow$ Search $\rightarrow$ Normalize $\rightarrow$ Score $\rightarrow$ Reflect).
- **Registry (`src/cheap_pc_searcher/sources/registry.py`)**: Manager for all external sources.
- **API Shell (`src/cheap_pc_searcher/api/app.py`)**: FastAPI endpoints for `/search`, `/sources`, and `/health`.

## 2. Pending Tasks (The Roadmap)
- [x] **Fix Imports**: All imports are absolute; app and agent loop run end-to-end.
- [x] **Real Sources**: `EbaySource` and `RedditSource` implemented (need API keys).
- [ ] **Environment Config**: Implement `pydantic-settings` to load `.env` values into the `SourceRegistry`.
- [ ] **Frontend**: Build the `web/index.html` to consume the `/search` endpoint.

## 3. Known State
Imports are fixed and bugs (normalizer overwrites, dropped compat issues, Reddit parsing, duplicate TargetBuild) are resolved as of the latest commit.
