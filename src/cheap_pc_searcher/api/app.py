from __future__ import annotations

import json
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cheap_pc_searcher.models import Listing, PartCategory, TargetBuild
from cheap_pc_searcher.config import Settings
from cheap_pc_searcher.agent.loop import AgentLoop
from cheap_pc_searcher.sources.registry import SourceRegistry
from cheap_pc_searcher.normalize import Normalizer


# --- Models for the API Request/Response ---

class SearchRequest(BaseModel):
    """The payload sent by the Frontend."""
    target_build: TargetBuild


class SourceStatus(BaseModel):
    """Information about enabled sources."""
    name: str
    enabled: bool


# --- Dependency Injection ---

# Config comes from the environment (or .env); see config.py and .env.example
_settings = Settings()
_registry = SourceRegistry(_settings.model_dump())
_normalizer = Normalizer()
_agent = AgentLoop(registry=_registry, normalizer=_normalizer)

app = FastAPI(
    title="Cheap PC Searcher API",
    description="Search for cheap, compatible PC components across multiple marketplaces.",
    version="0.1.0"
)

# The web UI is served from its own origin (e.g. :8990); allow it to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "online", "version": "0.1.0"}


@app.get("/sources", response_model=List[SourceStatus])
async def get_sources():
    """Returns every known source with its enabled status."""
    enabled = _registry.get_enabled_sources()
    return [
        SourceStatus(name=name, enabled=(name in enabled))
        for name in _registry.known_sources()
    ]


@app.post("/search", response_model=List[Listing])
async def search_parts(request: SearchRequest):
    """
    Perform a deep search for compatible parts.
    The Host/Frontend sends a TargetBuild JSON.
    The Agent finds, normalizes, and validates parts.
    """
    try:
        # The AgentLoop.run expects a JSON string representing the TargetBuild
        # We convert our Pydantic model back to JSON to keep the Agent's interface stable.
        target_json = request.target_build.model_dump_json()
        
        results = await _agent.run(target_json)
        return results
    except Exception as e:
        # In a real app, log the actual error and return a clean message
        print(f"Search Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the deep search loop.")


@app.get("/compatibility/validate")
async def validate_part(category: PartCategory, model_name: str, socket: str = None, ddr_gen: int = None):
    """
    A utility endpoint for the frontend to manually test compatibility logic 
    without running a full agent loop.
    """
    # This is a simplified manual trigger for the frontend developers
    from cheap_pc_searcher.models import Part
    from cheap_pc_searcher.compatibility.engine import CompatibilityEngine
    
    # We create a dummy target build for testing
    # In reality, this would be more complex
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
