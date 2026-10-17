from __future__ import annotations

import asyncio
import re
from typing import List
from .base import BaseSource
from cheap_pc_searcher.models import Listing, Part, PartCategory, Condition


class MockSource(BaseSource):
    """
    A source that returns hardcoded data for testing the agent loop
    without needing network access or API keys.
    """

    def __init__(self, name: str = "mock"):
        super().__init__(name=name)
        self._data = {
            "cpu": [
                Listing(
                    source_name=name,
                    raw_title="AMD Ryzen 5 3600 - Great condition",
                    raw_url="https://example.com/1",
                    current_price=50.0,
                    parsed_part=Part(
                        category=PartCategory.CPU,
                        brand="AMD",
                        model_name="Ryzen 5 3600",
                        specs={"socket": "AM4", "cores": 6},
                        condition=Condition.USED
                    )
                ),
                Listing(
                    source_name=name,
                    raw_title="Old Intel CPU Lot",
                    raw_url="https://example.com/2",
                    current_price=20.0,
                    is_bundle=True,
                    parsed_part=Part(
                        category=PartCategory.BUNDLE,
                        brand="Intel",
                        model_name="Unknown Intel CPUs",
                        specs={"type": "bundle"},
                        condition=Condition.USED
                    )
                )
            ],
            "bundle": [
                Listing(
                    source_name=name,
                    raw_title="Refurbished Dell OptiPlex 7070 SFF Desktop PC",
                    raw_url="https://example.com/4",
                    current_price=145.0,
                    is_bundle=True,
                    parsed_part=Part(
                        category=PartCategory.BUNDLE,
                        brand="Dell",
                        model_name="OptiPlex 7070 SFF",
                        specs={"type": "desktop", "condition": "refurbished", "os": "windows"},
                        condition=Condition.REFURBISHED
                    )
                )
            ],
            "ram": [
                Listing(
                    source_name=name,
                    raw_title="DDR4 16GB Kit 3200MHz",
                    raw_url="https://example.com/3",
                    current_price=35.0,
                    parsed_part=Part(
                        category=PartCategory.RAM,
                        brand="Generic",
                        model_name="DDR4 16GB 3200MHz",
                        specs={"capacity": "16GB", "type": "DDR4", "speed": "3200MHz"},
                        condition=Condition.USED
                    )
                )
            ]
        }

    # Query synonyms so expanded queries ("processor", "ryzen", "prebuilt") match
    _CATEGORY_TERMS = {
        "cpu": ("cpu", "processor", "ryzen", "intel", "xeon", "threadripper"),
        "ram": ("ram", "memory", "ddr"),
        "bundle": ("pc", "desktop", "prebuilt", "bundle", "computer"),
    }

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        # Simulate network latency
        await asyncio.sleep(0.1)

        query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        results = []

        # Match on category name, query synonyms, the normalized category, or
        # word overlap with the listing title, so queries like "Ryzen 5 3600",
        # "DDR4 RAM", or "Complete Prebuilt Desktop" surface the right fixtures.
        for category, listings in self._data.items():
            terms = set(self._CATEGORY_TERMS.get(category, ())) | {category}
            category_hit = bool(terms & query_tokens)
            for listing in listings:
                if category_hit:
                    results.append(listing)
                    continue
                title_tokens = set(re.findall(r"[a-z0-9]+", listing.raw_title.lower()))
                part_tokens = set()
                if listing.parsed_part:
                    part_tokens.add(listing.parsed_part.category.value)
                if part_tokens & query_tokens or query_tokens & title_tokens:
                    results.append(listing)

        return results[:limit]
