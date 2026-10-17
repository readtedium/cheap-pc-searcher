from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ..models import Part, PartCategory, CompatibilityIssue, Severity


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


class CompatibilityEngine:
    """
    A pure-function engine that runs validation rules against a TargetBuild.
    """

    def check(self, target: TargetBuild, candidate: Part) -> List[CompatibilityIssue]:
        issues = []
        
        # 1. Rule: CPU <-> Motherboard (Socket Match)
        if candidate.category == PartCategory.CPU:
            mobo = target.parts.get(PartCategory.MOTHERBOARD)
            if mobo:
                candidate_socket = candidate.specs.get("socket")
                mobo_socket = mobo.specs.get("socket")
                if candidate_socket and mobo_socket and candidate_socket != mobo_socket:
                    issues.append(CompatibilityIssue(
                        component=candidate.model_name,
                        message=f"Socket mismatch: CPU is {candidate_socket}, but Motherboard is {mobo_socket}",
                        severity=Severity.CRITICAL
                    ))

        # 2. Rule: RAM <-> Motherboard (DDR Generation)
        if candidate.category == PartCategory.RAM:
            mobo = target.parts.get(PartCategory.MOTHERBOARD)
            if mobo:
                candidate_ddr = candidate.specs.get("ddr_gen")
                mobo_ddr = mobo.specs.get("ddr_gen")
                if candidate_ddr and mobo_ddr and candidate_ddr != mobo_ddr:
                    issues.append(CompatibilityIssue(
                        component=candidate.model_name,
                        message=f"DDR mismatch: RAM is DDR{candidate_ddr}, but Motherboard is DDR{mobo_ddr}",
                        severity=Severity.CRITICAL
                    ))

        # 3. Rule: GPU <-> Case (Length Clearance)
        if candidate.category == PartCategory.GPU:
            if target.gpu_max_length_mm and candidate.specs.get("length_mm"):
                if candidate.specs["length_mm"] > target.gpu_max_length_mm:
                    issues.append(CompatibilityIssue(
                        component=candidate.model_name,
                        message=f"GPU too long: {candidate.specs['length_mm']}mm exceeds case limit of {target.gpu_max_length_mm}mm",
                        severity=Severity.CRITICAL
                    ))

        # 4. Rule: PSU <-> System (Power Budget - Simplified)
        # In a real engine, we'd calculate estimated load from all target parts.
        if candidate.category == PartCategory.PSU:
            # For now, just check if the candidate PSU is too low if we had a target load
            pass

        return issues
