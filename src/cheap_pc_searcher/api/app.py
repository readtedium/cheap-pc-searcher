from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from .models import Listing, PartCategory
from .agent.loop import AgentLoop
from .sources.registry import SourceRegistry
from .normalize import Normalizer

app = FastAPI(title="Cheap PC Searcher API")

# In a real app, these would be initialized via dependency injection or a lifespan handler
# For the starter, we initialize them here.
registry = SourceRegistry()
normalizer = Normalizer()
# We'll use a mock loop for now or a real one if keys are provided
agent_loop = AgentLoop(registry=registry, normalizer=normalizer)


class SearchRequest(BaseModel):
    target_build_json: str  # We'll accept a JSON string representing the TargetBuild


@app.get("/")
async def root():
    return {"message": "Cheap PC Searcher API is running. Use /search to find deals."}


@app.get("/sources")
async def list_sources():
    """Returns a list of currently enabled search sources."""
    return {"enabled_sources": list(registry.get_enabled_sources())}


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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
