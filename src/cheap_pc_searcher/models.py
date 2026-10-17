from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PartCategory(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    RAM = "ram"
    MOTHERBOARD = "motherboard"
    STORAGE = "storage"
    PSU = "psu"
    CASE = "case"
    COOLER = "cooler"
    PERIPHERAL = "peripheral"
    BUNDLE = "bundle"
    UNKNOWN = "unknown"


class Condition(str, Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    FOR_PARTS = "for_parts"
    SURPLUS = "surplus"


class Part(BaseModel):
    """
    The 'Gold Standard' normalized representation of a component.
    This is what the Compatibility Engine actually uses.
    """
    model_config = ConfigDict(frozen=True)

    category: PartCategory
    brand: Optional[str] = None
    model_name: str  # e.g., "Ryzen 5 5600X" or "DDR4 3200MHz"
    
    # Technical specs extracted by the Normalizer
    # Using a dict for flexibility, but keys should be standardized
    specs: Dict[str, Any] = Field(default_factory=dict) 
    # Example specs: {"socket": "AM4", "ddr_gen": 4, "wattage": 650, "form_factor": "ATX"}

    condition: Condition = Condition.USED


class Listing(BaseModel):
    """
    The raw/semi-structured data coming from a Source.
    """
    source_name: str  # e.g., "ebay", "reddit", "shopgoodwill"
    raw_title: str    # The exact text from the site
    raw_url: str
    raw_description: Optional[str] = None
    
    # Price info
    current_price: float
    currency: str = "USD"
    
    # The 'Normalized' version of this listing
    # If this is None, the Normalizer hasn't processed it yet.
    parsed_part: Optional[Part] = None

    # Metadata for the Agent to help with "Serendipity"
    is_bundle: bool = False
    confidence_score: float = Field(default=1.0, description="How sure the normalizer is about the specs")
    
    # For ShopGoodwill/eBay: indicates if it's an auction or buy-it-now
    listing_type: str = "fixed"  # "fixed" or "auction"
