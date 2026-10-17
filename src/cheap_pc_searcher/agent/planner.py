from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from ..models import Part, PartCategory

@dataclass
class TargetBuild:
    """
    Represents the user's current hardware setup to validate against.
    """
    parts: Dict[PartCategory, Part] = field(default_factory=dict)
    
    # Global constraints
    total_wattage_limit: float = 0.0
    case_form_factor: Optional[str] = None  # e.g., "ATX", "mATX", "ITX"
    gpu_max_length_mm: Optional[float] = None
    
    @classmethod
    def from_json(cls, json_str: str) -> TargetBuild:
        import json
        data = json.loads(json_str)
        # This is a simplified parser for the starter
        # In production, use Pydantic for this too.
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
