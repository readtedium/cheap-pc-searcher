from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


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


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CompatibilityIssue(BaseModel):
    component: str
    message: str
    severity: Severity


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

    # Compatibility findings attached by the AgentLoop after validation
    issues: List[CompatibilityIssue] = Field(default_factory=list)


class TargetBuild(BaseModel):
    """
    Represents the user's current hardware setup to validate against.
    """
    parts: Dict[PartCategory, Part] = Field(default_factory=dict)

    # Global constraints
    total_wattage_limit: float = 0.0
    case_form_factor: Optional[str] = None  # e.g., "ATX", "mATX", "ITX"
    gpu_max_length_mm: Optional[float] = None

    @classmethod
    def from_json(cls, json_str: str) -> TargetBuild:
        import json
        data = json.loads(json_str)

        parts = {}
        for cat_str, part_data in data.get("parts", {}).items():
            cat = PartCategory(cat_str)
            parts[cat] = Part(**part_data)

        return cls(
            parts=parts,
            total_wattage_limit=data.get("total_wattage_limit", 0.0),
            case_form_factor=data.get("case_form_factor"),
            gpu_max_length_mm=data.get("gpu_max_length_mm")
        )
