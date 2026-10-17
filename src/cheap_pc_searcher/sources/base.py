from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List
<<<<<<< HEAD

from ..models import Listing


def extract_price(*texts: str) -> float:
    """Extract a dollar amount from marketplace title or description text."""
    for text in texts:
        match = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", text or "")
=======
from cheap_pc_searcher.models import Listing


# Matches "$120", "$1,050.50", "$ 75" in titles/descriptions
_PRICE_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)")


def extract_price(*texts: str) -> float:
    """
    Best-effort price extraction from raw listing text.
    Returns 0.0 when no price can be found (the agent loop sorts those last).
    """
    for text in texts:
        match = _PRICE_RE.search(text or "")
>>>>>>> f438e5e93b19fce5989cc383a719cee8d3eadeb8
        if match:
            return float(match.group(1).replace(",", ""))
    return 0.0


class BaseSource(ABC):
    """
    The Abstract Base Class for all component sources.
    Each implementation (eBay, Reddit, Craigslist, ...) must implement `search`.
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
