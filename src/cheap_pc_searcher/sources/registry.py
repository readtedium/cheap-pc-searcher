from __future__ import annotations

import asyncio
from typing import List, Dict, Any
from .base import BaseSource
from .ebay import EbaySource
from .reddit import RedditSource
from .mock import MockSource

class SourceRegistry:
    """
    Manally manages the registration and instantiation of search sources
    based on configuration.
    """

    def __init__(self, config: Dict[str, Any]):
        self._available_sources = {
            "mock": MockSource,
            "ebay": EbaySource,
            "reddit": RedditSource,
        }
        self._instances: Dict[str, BaseSource] = {}
        self._config = config

    def get_enabled_sources(self) -> List[str]:
        """Returns the names of sources enabled in the config."""
        return self._config.get("enabled_sources", ["mock"])

    def get_source(self, name: str) -> BaseSource:
        if name in self._instances:
            return self._instances[name]
        
        if name in self._available_sources:
            # Initialize with specific config secrets
            if name == "ebay":
                instance = EbaySource(name=name, api_key=self._config["ebay_api_key"])
            elif name == "reddit":
                instance = RedditSource(
                    name=name, 
                    client_id=self._config["reddit_client_id"],
                    client_secret=self._config["reddit_client_secret"]
                )
            else:
                instance = self._available_sources[name](name=name)
            
            self._instances[name] = instance
            return instance
        
        raise ValueError(f"Source '{name}' is not registered.")

    def get_all_instances(self) -> List[BaseSource]:
        enabled_names = self.get_enabled_sources()
        return [self.get_source(name) for name in enabled_names]
