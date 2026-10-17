from __future__ import annotations

import asyncio
from typing import List, Dict, Any
from ..models import Listing, PartCategory
from ..sources.registry import SourceRegistry
from ..normalize import Normalizer
from ..compatibility.engine import CompatibilityEngine
from ..agent.planner import TargetBuild


class AgentLoop:
    def __init__(self, registry: SourceRegistry, normalizer: Normalizer):
        self.registry = registry
        self.normalizer = normalizer
        self.compatibility_engine = CompatibilityEngine()

    async def run(self, target_build_json: str) -> List[Listing]:
        """
        The core orchestration loop.
        """
        target_build = TargetBuild.from_json(target_build_json)
        
        # 1. Plan
        queries = self._plan(target_build)
        
        all_listings: List[Listing] = []
        
        # 2. Search (Fan out)
        sources = self.registry.get_all_instances()
        tasks = []
        for query in queries:
            for source in sources:
                tasks.append(self._search_and_normalize(source, query))
        
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        for batch in results:
            all_listings.extend(batch)

        # 3. Score & Filter (Compatibility check)
        final_results = []
        for listing in all_listings:
            if listing.parsed_part:
                issues = self.compatibility_engine.check(target_build, listing.parsed_part)
                
                # Filter out critical mismatches
                if not any(i.severity == "critical" for i in issues):
                    # Add issues to the listing for the UI to show
                    # (In a real app, we might add an 'issues' field to Listing)
                    final_results.append(listing)
        
        # 4. Sort by price (simple heuristic for now)
        final_results.sort(key=lambda x: x.current_price)
        
        return final_results

    def _plan(self, target: TargetBuild) -> List[str]:
        """
        Generates initial search queries based on the target build.
        """
        queries = []
        for category, part in target.parts.items():
            # Basic query: "Ryzen 5 5600X"
            queries.append(part.model_name)
            # Expansion query: "AM4 CPU"
            if category == PartCategory.CPU and "socket" in part.specs:
                queries.append(f"{part.specs['socket']} CPU")
            elif category == PartCategory.RAM and "ddr_gen" in part.specs:
                queries.append(f"DDR{part.specs['ddr_gen']} RAM")
        
        if not queries:
            queries = ["pc parts"]
            
        return queries

    async def _search_and_normalize(self, source, query: str) -> List[Listing]:
        try:
            raw_listings = await source.search(query)
            normalized_listings = []
            for rl in raw_listings:
                normalized = await self.normalizer.normalize(rl)
                normalized_listings.append(normalized)
            return normalized_listings
        except Exception as e:
            print(f"Error in {source.name} for query '{query}': {e}")
            return []
