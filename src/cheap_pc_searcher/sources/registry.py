from __future__ import annotations

from typing import Dict, List, Type
from ..sources.base import BaseSource
from ..sources.mock import MockSource


class SourceRegistry:
    """
    Manages the registration and instantiation of search sources.
    This allows the Agent to easily 'fan out' to all enabled sources.
    """

    def __init__(self):
        # Map of name -> Source Class
        self._available_sources: Dict[str, Type[BaseSource]] = {
            "mock": MockSource,
            # "ebay": EbaySource,  <-- To be implemented
            # "reddit": RedditSource, <-- To be implemented
            # "shopgoodwill": ShopGoodwillSource, <-- To be implemented
        }
        # Instances of initialized sources
        self._instances: Dict[str, BaseSource] = {}

    def get_enabled_sources(self) -> List[str]:
        """Returns the names of all currently instantiated sources."""
        return list(self._instances.keys())

    def get_source(self, name: str) -> BaseSource:
        """Retrieves an existing source instance or creates a new one."""
        if name in self._instances:
            return self._instances[name]
        
        if name in self._available_sources:
            instance = self._available_sources[name](name=name)
            self._instances[name] = instance
            return instance
        
        raise ValueError(f"Source '{name}' is not registered.")

    def get_all_instances(self) -> List[BaseSource]:
        """Returns all active source instances."""
        # Ensure all known sources are instantiated for the fan-out
        for name in self._available_sources:
            if name not in self._instances:
                self.get_source(name)
        return list(self._instances.values())
