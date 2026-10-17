from __future__ import annotations

from typing import List
from cheap_pc_searcher.sources.base import BaseSource, extract_price
from cheap_pc_searcher.models import Listing


class RedditSource(BaseSource):
    """
    A real implementation for r/hardwareswap.
    Uses the Reddit API to find enthusiast-grade used parts.
    """

    def __init__(self, name: str, client_id: str, client_secret: str):
        super().__init__(name=name)
        self.client_id = client_id
        self.client_secret = client_secret

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        import httpx

        async with httpx.AsyncClient() as client:
            try:
                # 1. Get Access Token (Simplified)
                # In a real app, you'd manage token refresh logic.
                auth_data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
                auth_res = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    data=auth_data,
                    headers={"User-Agent": "CheapPC_Searcher_v1"},
                )
                token = auth_res.json().get("access_token")

                if not token:
                    return []

                headers = {"Authorization": f"Bearer {token}", "User-Agent": "CheapPC_Searcher_v1"}

                # 2. Search the subreddit (restrict_sr keeps the search inside r/hardwareswap)
                res = await client.get(
                    "https://oauth.reddit.com/r/hardwareswap/search",
                    headers=headers,
                    params={"q": query, "limit": limit, "sort": "new", "restrict_sr": 1},
                    timeout=10.0,
                )
                res.raise_for_status()
                data = res.json()

                # Reddit's listing envelope nests posts under data.data.children
                children = data.get("data", {}).get("children", [])

                listings = []
                for post in children:
                    listing_data = post.get("data", {})
                    title = listing_data.get("title", "")
                    body = listing_data.get("selftext", "")

                    listings.append(Listing(
                        source_name=self.name,
                        raw_title=title,
                        raw_url=f"https://reddit.com{listing_data.get('permalink', '')}",
                        raw_description=body,
                        current_price=extract_price(title, body),
                        listing_type="fixed"
                    ))
                return listings

            except Exception as e:
                print(f"Reddit API Error: {e}")
                return []
