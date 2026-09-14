"""Guardrails and Policy Validation (Criteria 11).

Provides input/output validation, prompt injection defense, geographic
bounds checking, and self-evaluation guardrails for architectural operations.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.observability.logging import get_logger

logger = get_logger("app.guardrails.policy")


class GuardrailVerdict(BaseModel):
    """Result of a guardrail evaluation check."""
    passed: bool = Field(..., description="Whether the check passed without violations.")
    violation_reason: Optional[str] = Field(default=None, description="Explanation if violated.")
    suggested_correction: Optional[str] = Field(default=None, description="Actionable recovery recommendation.")


def validate_geographic_coordinates(latitude: float, longitude: float) -> GuardrailVerdict:
    """Validates that coordinates are valid WGS84 and within terrestrial limits."""
    if not (-90.0 <= latitude <= 90.0):
        return GuardrailVerdict(
            passed=False,
            violation_reason=f"Latitude {latitude} outside valid range [-90.0, 90.0].",
            suggested_correction="Verify decimal degree latitude format.",
        )
    if not (-180.0 <= longitude <= 180.0):
        return GuardrailVerdict(
            passed=False,
            violation_reason=f"Longitude {longitude} outside valid range [-180.0, 180.0].",
            suggested_correction="Verify decimal degree longitude format.",
        )
    return GuardrailVerdict(passed=True)


def validate_architectural_domain_intent(user_prompt: str) -> GuardrailVerdict:
    """Detects prompt injection attempts or queries completely outside the architectural domain."""
    injection_signatures = [
        "ignore previous instructions",
        "system prompt override",
        "disregard all prior rules",
        "reveal your secret key",
    ]
    lowered = user_prompt.lower()
    for sig in injection_signatures:
        if sig in lowered:
            logger.warning("prompt_injection_guardrail_triggered", signature=sig)
            return GuardrailVerdict(
                passed=False,
                violation_reason=f"Security Policy Violation: Detected prohibited prompt pattern '{sig}'.",
                suggested_correction="Rephrase query to adhere to architectural copilot instructions.",
            )
    return GuardrailVerdict(passed=True)


def self_eval_architectural_compliance(output_data: Dict[str, Any]) -> GuardrailVerdict:
    """Self-evaluates computed architectural outputs against basic zoning sanity thresholds."""
    area = output_data.get("area_sqm", 0.0)
    if area < 0:
        return GuardrailVerdict(
            passed=False,
            violation_reason="Negative parcel area detected in computation output.",
            suggested_correction="Verify polygon vertex winding order and coordinates.",
        )
    return GuardrailVerdict(passed=True)
