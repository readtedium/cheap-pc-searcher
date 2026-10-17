from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from cheap_pc_searcher.models import Listing
from cheap_pc_searcher.sources.base import BaseSource, extract_price


class WebSearchSource(BaseSource):
    """
    General web search via Bing's RSS endpoint — no API key required.

    Feed shape: https://www.bing.com/search?q=<q>&format=rss
    Items carry <title>, <link>, <description>; prices are parsed from text
    (many shopping results embed "$N" in the description).

    This gives the agent loop live, keyless coverage of the open web:
    marketplace pages, forum sales posts, and retailer listings all surface
    as raw Listings for the Normalizer.
    """

    def __init__(self, name: str = "websearch"):
        super().__init__(name=name)

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        import httpx

        params = {"q": query, "format": "rss"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                res = await client.get(
                    "https://www.bing.com/search",
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"},
                    timeout=10.0,
                )
                res.raise_for_status()
                return self._parse_rss(res.text, limit)
            except Exception as e:
                print(f"Web search error: {e}")
                return []

    def _parse_rss(self, xml_text: str, limit: int) -> List[Listing]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"Web search RSS parse error: {e}")
            return []

        listings: List[Listing] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            if not title or not link:
                continue

            listings.append(Listing(
                source_name=self.name,
                raw_title=title,
                raw_url=link,
                raw_description=description,
                current_price=extract_price(title, description),
                listing_type="fixed"
            ))
            if len(listings) >= limit:
                break

        return listings
