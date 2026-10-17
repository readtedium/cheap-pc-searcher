from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..agent.loop import AgentLoop
from ..models import Listing
from ..normalize import Normalizer
from ..sources.registry import SourceRegistry

app = FastAPI(title="Cheap PC Searcher API")
web_directory = Path(__file__).resolve().parents[3] / "web"
app.mount("/web_inspo", StaticFiles(directory=web_directory / "web_inspo"), name="web-inspo")

registry = SourceRegistry()
normalizer = Normalizer()
agent_loop = AgentLoop(registry=registry, normalizer=normalizer)


class SearchRequest(BaseModel):
    target_build_json: str


@app.get("/")
async def root():
    return FileResponse(web_directory / "index.html")


@app.get("/sources")
async def list_sources():
    """Returns a list of currently enabled search sources."""
    registry.get_all_instances()
    return {"enabled_sources": registry.get_enabled_sources()}


@app.post("/search", response_model=List[Listing])
async def search_parts(request: SearchRequest):
    """
    The main entry point.
    The agent takes the target build, plans, searches, normalizes, and scores.
    """
    try:
        # In a real implementation, we'd parse the JSON into a TargetBuild object
        # For now, we pass the string to the agent which will handle it.
        results = await agent_loop.run(request.target_build_json)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
