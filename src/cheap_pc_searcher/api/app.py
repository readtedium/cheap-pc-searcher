from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from cheap_pc_searcher.models import Listing, PartCategory, TargetBuild
from cheap_pc_searcher.config import Settings
from cheap_pc_searcher.agent.loop import AgentLoop
from cheap_pc_searcher.sources.registry import SourceRegistry
from cheap_pc_searcher.normalize import Normalizer


# --- Models for the API Request/Response ---

class SearchRequest(BaseModel):
    """
    The payload sent by the Frontend.

    Accepts either handshake shape:
      {"target_build_json": "<json str>"}  — stringified target build (web UI)
      {"target_build": {...}}              — typed object (preferred)
    """
    target_build: Optional[TargetBuild] = None
    target_build_json: Optional[str] = None

    @model_validator(mode="after")
    def _require_one(self) -> "SearchRequest":
        if self.target_build is None and not self.target_build_json:
            raise ValueError("Provide either 'target_build' or 'target_build_json'")
        return self


class SourceStatus(BaseModel):
    """Information about enabled sources."""
    name: str
    enabled: bool


# --- Dependency Injection ---

# Config comes from the environment (or .env); see config.py and .env.example
settings = Settings()
registry = SourceRegistry(settings.model_dump())
normalizer = Normalizer()
agent_loop = AgentLoop(registry=registry, normalizer=normalizer)


app = FastAPI(
    title="Cheap PC Searcher API",
    description="Search for cheap, compatible PC components across multiple marketplaces.",
    version="0.1.0"
)

# The web UI is served from this same app at "/" (single origin), but it can
# also be hosted elsewhere (e.g. :8990) — allow cross-origin calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

web_directory = Path(__file__).resolve().parents[3] / "web"
app.mount("/web_inspo", StaticFiles(directory=web_directory / "web_inspo"), name="web-inspo")


# --- Endpoints ---

@app.get("/")
async def root():
    """Serve the single-file web UI."""
    return FileResponse(web_directory / "index.html")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/sources")
async def get_sources():
    """Returns the enabled source names (shape expected by the web UI)."""
    enabled = registry.get_enabled_sources()
    return {
        "enabled_sources": enabled,
        "sources": [
            SourceStatus(name=name, enabled=(name in enabled))
            for name in registry.known_sources()
        ],
    }


@app.post("/search", response_model=List[Listing])
async def search_parts(request: SearchRequest):
    """
    The agent plans, searches, normalizes, and validates listings for a target build.
    """
    try:
        # The AgentLoop.run expects a JSON string representing the TargetBuild.
        # Normalize either handshake shape into that string.
        if request.target_build is not None:
            target_json = request.target_build.model_dump_json()
        else:
            target_json = request.target_build_json

        results = await agent_loop.run(target_json)
        return results
    except Exception as e:
        print(f"Search Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the deep search loop.")


@app.get("/compatibility/validate")
async def validate_part(category: PartCategory, model_name: str, socket: str = None, ddr_gen: int = None):
    """
    A utility endpoint for the frontend to manually test compatibility logic
    without running a full agent loop.
    """
    from cheap_pc_searcher.models import Part
    from cheap_pc_searcher.compatibility.engine import CompatibilityEngine

    # We create a dummy target build for testing
    dummy_target = TargetBuild(parts={})

    # Mocking a candidate part
    candidate = Part(
        category=category,
        model_name=model_name,
        specs={"socket": socket, "ddr_gen": ddr_gen}
    )

    engine = CompatibilityEngine()
    issues = engine.check(dummy_target, candidate)

    return {
        "part": candidate,
        "issues": issues
    }
