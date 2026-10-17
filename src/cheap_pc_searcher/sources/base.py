from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from .models import Listing


class BaseSource(ABC):
    """
    The Abstract Base Class for all component sources.
    Each implementation (eBay, Reddit, ShopGoodwill) must implement `search`.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        """
        Perform a search on the specific platform and return a list of Listing objects.
        Note: At this stage, `parsed_part` in the Listing may be None.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
