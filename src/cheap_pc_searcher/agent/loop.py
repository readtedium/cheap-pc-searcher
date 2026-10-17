from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .models import Listing, Part, PartCategory

@dataclass
class TargetBuild:
    """
    The desired PC configuration. 
    The agent uses this to generate search queries.
    """
    name: str
    required_parts: Dict[PartCategory, Dict[str, Any]]
    # e.g. {PartCategory.CPU: {"socket": "AM4", "min_cores": 6}, ...}

class CompatibilityEngine:
    """
    STUB: In a real implementation, this would check if parts fit together
    (e.g. CPU socket vs Motherboard socket).
    """
    async def score_and_filter(
        self, 
        listings: List[Listing], 
        target: TargetBuild
    ) -> List[Listing]:
        # TODO: Implement actual compatibility and value scoring.
        # For now, we just fall back to returning everything that has a parsed_part.
        
        scored = []
        for listing in listings:
            if listing.parsed_part:
                # Simple heuristic: if it's a bundle, we might give it a neutral score
                # if it's a specific part, we'd check against target requirements.
                scored.append(listing)
        
        # Sort by price (ascending) as a naive "value" metric
        return sorted(scored, key=lambda x: x.current_price)

class AgentLoop:
    """
    The core orchestrator for finding components.
    """
    def __init__(
        self,
        sources: List[Any],
        normalizer: Any,
        compatibility_engine: CompatibilityEngine
    ):
        self.sources = sources
        self.normalizer = normalizer
        self.compatibility_engine = compatibility_engine

    async def run(self, target: TargetBuild, max_iterations: int = 3) -> Dict[str, List[Listing]]:
        """
        Executes the Plan -> Search -> Normalize -> Score/Filter -> Reflect loop.
        Returns a mapping of PartCategory to best available Listings.
        """
        final_results: Dict[str, List[Listing]] = {cat.value: [] for cat in PartCategory}
        current_queries = self._plan(target)
        
        iteration = 0
        while iteration < max_iterations:
            print(f"--- Agent Iteration {iteration + 1}/{max_iterations} ---")
            
            # 1. Search
            all_raw_listings: List[Listing] = []
            for query in current_queries:
                for source in self.sources:
                    results = await source.search(query)
                    all_raw_listings.extend(results)
            
            # 2. Normalize
            normalized_listings = []
            for listing in all_raw_listings:
                norm_listing = await self.normalizer.normalize(listing)
                normalized_listings.append(norm_listing)
            
            # 3. Score & Filter
            filtered_listings = await self.compatibility_engine.score_and_filter(
                normalized_listings, target
            )
            
            # 4. Collect valid matches
            found_something = False
            for listing in filtered_listings:
                if listing.parsed_part:
                    cat_key = listing.parsed_part.category.value
                    # Avoid duplicates in the same category
                    if not any(l.raw_url == listing.raw_url for l in final_results[cat_key]):
                        final_results[cat_key].append(listing)
                        found_something = True

            # Check if we have at least one good option for each required category
            all_requirements_met = all(
                len(final_results[cat.value]) > 0 
                for cat in target.required_parts.keys()
            )

            if all_requirements_met:
                print("Goal reached: All part categories have candidates.")
                break
            
            # 5. Reflect
            print("Requirements not fully met. Reflecting...")
            current_queries = self._reflect(target, final_results, current_queries)
            iteration += 1

        return final_results

    def _plan(self, target: TargetBuild) -> List[str]:
        """
        Generates initial queries based on target requirements.
        """
        queries = []
        for category, specs in target.required_parts.items():
            query_parts = [category.value]
            for k, v in specs.items():
                query_parts.append(str(v))
            queries.append(" ".join(query_parts))
        return queries

    def _reflect(
        self, 
        target: TargetBuild, 
        current_results: Dict[str, List[Listing]], 
        old_queries: List[str]
    ) -> List[str]:
        """
        Generates new queries if the previous ones failed.
        """
        new_queries = []
        for category, specs in target.required_parts.items():
            cat_key = category.value
            if len(current_results.get(cat_key, [])) == 0:
                # We didn't find anything for this category.
                # Try a broader query (just the category) or a different spec.
                new_queries.append(category.value)
                
                # If we had specific specs, try removing the most restrictive ones
                # (In a real agent, this would involve an LLM deciding which spec to drop)
                if len(specs) > 1:
                    # Fallback to just the category name
                    pass 
            else:
                # We found something, but maybe we want more variety?
                # For now, let's stick to what worked or expand slightly.
                pass
                
        # If no progress is being made, return a default "safety" set of queries
        if not new_queries:
            return ["pc parts bundle"]
            
        return list(set(new_queries))
