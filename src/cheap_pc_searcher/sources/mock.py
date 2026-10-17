from __future__ import annotations

import asyncio
from typing import List
from .base import BaseSource
from ..models import Listing, Part, PartCategory, Condition


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
                    source_name="mock",
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
                    source_name="mock",
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
            "ram": [
                Listing(
                    source_name="mock",
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
            ],
            "bundle": [
                Listing(
                    source_name=name,
                    raw_title="Refurbished Dell OptiPlex Desktop PC",
                    raw_url="https://example.com/4",
                    current_price=145.0,
                    parsed_part=Part(
                        category=PartCategory.BUNDLE,
                        brand="Dell",
                        model_name="OptiPlex Desktop PC",
                        specs={"type": "desktop"},
                        condition=Condition.REFURBISHED
                    )
                )
            ],
        }

    async def search(self, query: str, limit: int = 20) -> List[Listing]:
        # Simulate network latency
        await asyncio.sleep(0.1)
        
        query_lower = query.lower()
        results = []
        
        category_terms = {
            "cpu": ("cpu", "processor"),
            "ram": ("ram", "memory"),
            "bundle": ("pc", "desktop", "prebuilt", "bundle"),
        }
        for category, listings in self._data.items():
            if any(term in query_lower for term in category_terms[category]):
                results.extend(listings)
        
        return results[:limit]
