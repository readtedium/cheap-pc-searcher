from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from cheap_pc_searcher.models import Listing
from cheap_pc_searcher.sources.base import BaseSource, extract_price


class CraigslistSource(BaseSource):
    """
    Craigslist search via its public RSS feed — no API key required.

    Feed shape: https://<city>.craigslist.org/search/sss?query=<q>&format=rss
    RSS items carry <title>, <link>, <description>; price is parsed from text.

    Note: Craigslist blocks requests from datacenter IPs (403); this works
    from residential connections and degrades to [] when blocked.
    """

    def __init__(self, name: str = "craigslist", city: str = "hampton"):
        super().__init__(name=name)
        self.city = city

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        import httpx

        url = f"https://{self.city}.craigslist.org/search/sss"
        params = {"query": query, "format": "rss"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                res = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": "CheapPC_Searcher_v1"},
                    timeout=10.0,
                )
                res.raise_for_status()
                return self._parse_rss(res.text, limit)
            except Exception as e:
                print(f"Craigslist RSS Error: {e}")
                return []

    def _parse_rss(self, xml_text: str, limit: int) -> List[Listing]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"Craigslist RSS parse error: {e}")
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
