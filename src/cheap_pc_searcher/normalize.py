from __future__ import annotations

import re
from typing import Optional, Dict, Any
from .models import Listing, Part, PartCategory, Condition


class Normalizer:
    """
    The Normalizer is responsible for turning messy, human-written 
    marketplace titles into structured, typed Part objects.
    
    It uses a tiered approach:
    1. Deterministic Regex/Heuristics (Fast, cheap, reliable for common patterns)
    2. LLM-based extraction (Slow, expensive, handles the "weird" surplus/bundle cases)
    """

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client

    async def normalize(self, listing: Listing) -> Listing:
        """
        Attempts to parse the listing. If heuristics fail or confidence is low,
        it falls back to the LLM.
        """
        # A source that already normalized the listing (e.g. fixtures) wins
        if listing.parsed_part:
            return listing

        # 1. Try Heuristics first
        part = self._apply_heuristics(listing)

        # 2. Check if we need the LLM
        # We use the LLM if:
        # - No part was found
        # - It's a bundle (hard to parse with regex)
        # - The confidence is low (subjective, but can be implemented)
        if not part or listing.is_bundle or self._is_messy(listing.raw_title):
            llm_part = await self._apply_llm(listing)
            # Keep the heuristic result when the LLM is unavailable or fails
            part = llm_part or part

        if part:
            listing.parsed_part = part
        
        return listing

    def _apply_heuristics(self, listing: Listing) -> Optional[Part]:
        """
        Fast regex-based extraction for common patterns.
        """
        title = listing.raw_title.lower()
        
        # Example: RAM detection
        if "ddr" in title and ("gb" in title or "mb" in title):
            capacity_match = re.search(r'(\d+)\s?gb', title)
            speed_match = re.search(r'(\d+)\s?mhz', title)
            
            if capacity_match:
                return Part(
                    category=PartCategory.RAM,
                    model_name=listing.raw_title, # Fallback
                    specs={
                        "capacity": f"{capacity_match.group(1)}GB",
                        "speed": f"{speed_match.group(1)}MHz" if speed_match else "unknown"
                    },
                    condition=self._infer_condition(title)
                )

        # Example: CPU Socket detection
        if any(s in title for s in ["am4", "am5", "lga1700", "lga1200", "socket"]):
            socket_match = re.search(r'(am4|am5|lga\d+)', title)
            return Part(
                category=PartCategory.CPU,
                model_name=listing.raw_title,
                specs={"socket": socket_match.group(1) if socket_match else "unknown"},
                condition=self._infer_condition(title)
            )

        return None

    async def _apply_llm(self, listing: Listing) -> Optional[Part]:
        """
        Uses the LLM to perform deep semantic parsing.
        This is where we handle "Old Intel CPU Lot" or "Gaming PC Parts Bundle".
        """
        if not self.llm_client:
            return None

        prompt = f"""
        Extract structured hardware component data from this marketplace listing.
        
        Listing Title: "{listing.raw_title}"
        Listing Description: "{listing.raw_description or 'N/A'}"

        Return ONLY a JSON object with this schema:
        {{
          "category": "cpu" | "gpu" | "ram" | "motherboard" | "storage" | "psu" | "case" | "cooler" | "peripheral" | "bundle" | "unknown",
          "brand": "string or null",
          "model_name": "string",
          "specs": {{ "key": "value" }},
          "condition": "new" | "used" | "refurbished" | "for_parts" | "surplus"
        }}
        """
        
        try:
            # This assumes the llm_client has a method to return parsed JSON
            response = await self.llm_client.complete_json(prompt)
            return Part(**response)
        except Exception as e:
            print(f"LLM Normalization failed: {e}")
            return None

    def _infer_condition(self, title: str) -> Condition:
        title = title.lower()
        if "new" in title or "sealed" in title:
            return Condition.NEW
        if "refurbished" in title or "renewed" in title:
            return Condition.REFURBISHED
        if "parts" in title or "broken" in title or "as-is" in title:
            return Condition.FOR_PARTS
        if "surplus" in title or "bulk" in title:
            return Condition.SURPLUS
        return Condition.USED

    def _is_messy(self, title: str) -> bool:
        """
        Heuristic to decide if a title is too vague for regex.
        e.g., 'Lot of parts', 'Old computer components'
        """
        vague_keywords = ["lot", "bundle", "parts", "stuff", "assorted", "various"]
        return any(word in title.lower() for word in vague_keywords)
