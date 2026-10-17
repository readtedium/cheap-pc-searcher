from __future__ import annotations

import asyncio
import re
from typing import List
from cheap_pc_searcher.sources.base import BaseSource
from cheap_pc_searcher.models import Listing, Part, PartCategory, Condition



class EbaySource(BaseSource):
    """
    A real implementation of the eBay Browse API.
    Note: This requires an eBay Developer API Key.
    """

    def __init__(self, name: str, api_key: str):
        super().__init__(name=name)
        self.api_key = api_key
        self.base_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-EBAY-C-PRODUCT-API-SITEID": "0"  # US Site
        }

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        import httpx
        
        params = {
            "q": query,
            "limit": limit,
            "filter": "conditions:{USED}"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url, 
                    headers=self.headers, 
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                listings = []
                for item in data.get("itemSummaries", []):
                    listings.append(Listing(
                        source_name=self.name,
                        raw_title=item.get("title", ""),
                        raw_url=item.get("itemWebUrl", ""),
                        current_price=float(item.get("price", {}).get("value", 0)),
                        currency=item.get("price", {}).get("currency", "USD"),
                        raw_description=item.get("description", ""), # Note: Browse API might not return full desc
                        listing_type="fixed" # Simplified
                    ))
                return listings

            except Exception as e:
                print(f"eBay API Error: {e}")
                return []
