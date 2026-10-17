"""
TODO shells for JS-heavy marketplaces that require headless-browser scraping.

These are registered in the SourceRegistry so config can enable them, but the
scraping itself is not implemented yet — `search` logs a notice and returns [].

Implementation sketch (PLAN.md): a Playwright extra that
  1. opens the search results page for the query,
  2. extracts title/price/url per result card,
  3. returns plain `Listing` objects for the Normalizer.
Do the scraping here only; keep parsing/heuristics in normalize.py.
"""

from __future__ import annotations

from typing import List

from cheap_pc_searcher.models import Listing
from cheap_pc_searcher.sources.base import BaseSource


class _PlaywrightStubSource(BaseSource):
    """Base for sites that need Playwright scraping instead of a public API."""

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        print(f"[{self.name}] not implemented yet — needs Playwright scraping (see PLAN.md)")
        return []


class NeweggSource(_PlaywrightStubSource):
    def __init__(self, name: str = "newegg"):
        super().__init__(name=name)


class AmazonSource(_PlaywrightStubSource):
    def __init__(self, name: str = "amazon"):
        super().__init__(name=name)


class FBMarketplaceSource(_PlaywrightStubSource):
    def __init__(self, name: str = "facebook"):
        super().__init__(name=name)
