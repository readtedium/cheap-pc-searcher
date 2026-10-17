from __future__ import annotations

from typing import List, Dict, Any
from .base import BaseSource
from .ebay import EbaySource
from .reddit import RedditSource
from .mock import MockSource
from .craigslist import CraigslistSource
from ._stubs import NeweggSource, AmazonSource, FBMarketplaceSource


class SourceRegistry:
    """
    Manages the registration and instantiation of search sources
    based on configuration.
    """

    def __init__(self, config: Dict[str, Any]):
        self._available_sources = {
            "mock": MockSource,
            "ebay": EbaySource,
            "reddit": RedditSource,
            "craigslist": CraigslistSource,
            "newegg": NeweggSource,
            "amazon": AmazonSource,
            "facebook": FBMarketplaceSource,
        }
        self._instances: Dict[str, BaseSource] = {}
        self._config = config

    def known_sources(self) -> List[str]:
        """Names of every source the registry knows how to build."""
        return list(self._available_sources)

    def get_enabled_sources(self) -> List[str]:
        """Returns the names of sources enabled in the config."""
        return self._config.get("enabled_sources", ["mock"])

    def get_source(self, name: str) -> BaseSource:
        if name in self._instances:
            return self._instances[name]

        if name not in self._available_sources:
            raise ValueError(f"Source '{name}' is not registered.")

        # Initialize with specific config secrets
        if name == "ebay":
            instance = EbaySource(name=name, api_key=self._config.get("ebay_api_key", ""))
        elif name == "reddit":
            instance = RedditSource(
                name=name,
                client_id=self._config.get("reddit_client_id", ""),
                client_secret=self._config.get("reddit_client_secret", ""),
            )
        elif name == "craigslist":
            instance = CraigslistSource(
                name=name,
                city=self._config.get("craigslist_city", "hampton"),
            )
        else:
            instance = self._available_sources[name](name=name)

        self._instances[name] = instance
        return instance

    def get_all_instances(self) -> List[BaseSource]:
        enabled_names = self.get_enabled_sources()
        return [self.get_source(name) for name in enabled_names]
