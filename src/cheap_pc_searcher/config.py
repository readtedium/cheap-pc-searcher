from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed environment configuration (loads .env if present).

    ENABLED_SOURCES uses JSON list syntax, e.g.:
        ENABLED_SOURCES=["mock","craigslist"]
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    enabled_sources: List[str] = Field(default_factory=lambda: ["websearch"])
    ebay_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    craigslist_city: str = "hampton"
