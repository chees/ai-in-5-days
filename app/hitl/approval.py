"""Human-in-the-Loop (HITL) Hooks (Criteria 12).

Defines explicit code stops and confirmation gates that interrupt automated
execution and require human confirmation before high-stakes architectural actions
(such as municipal permit filings, legal zoning classification overrides, or
property boundary amendments).
"""

from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field
from app.observability.logging import get_logger

logger = get_logger("app.hitl.approval")


class ActionApprovalRequest(BaseModel):
    """Payload representing a high-stakes action pending human sign-off."""
    action_id: str = Field(..., description="Unique identifier for the action gate.")
    action_name: str = Field(..., description="Name of high-stakes operation.")
    impact_level: str = Field(..., description="Risk tier: 'CRITICAL', 'HIGH', 'MEDIUM'.")
    summary: str = Field(..., description="Clear explanation of the consequence of the action.")
    proposed_payload: Dict[str, Any] = Field(..., description="Arguments that will be executed upon approval.")


class ActionApprovalResponse(BaseModel):
    """Human decision record."""
    approved: bool = Field(..., description="True if human confirmed the action, False if rejected.")
    reviewer_comments: Optional[str] = Field(default=None, description="Notes from the human reviewer.")


class HumanInTheLoopCheckpoint:
    """Manages execution stops requiring explicit human authorization."""

    def __init__(self):
        self._pending_requests: Dict[str, ActionApprovalRequest] = {}

    def require_approval_before_execution(
        self,
        action_name: str,
        summary: str,
        payload: Dict[str, Any],
        impact_level: str = "HIGH",
    ) -> ActionApprovalRequest:
        """Interrupts execution flow and creates a pending approval ticket.

        Args:
            action_name: Name of high-stakes operation.
            summary: Human-readable description of potential legal or physical impacts.
            payload: Parameters to be executed.
            impact_level: Risk tier ('CRITICAL', 'HIGH').

        Returns:
            ActionApprovalRequest ticket requiring explicit confirmation.
        """
        import uuid
        action_id = f"HITL-{uuid.uuid4().hex[:8]}"
        req = ActionApprovalRequest(
            action_id=action_id,
            action_name=action_name,
            impact_level=impact_level,
            summary=summary,
            proposed_payload=payload,
        )
        self._pending_requests[action_id] = req
        logger.warning(
            "hitl_approval_gate_triggered",
            action_id=action_id,
            action_name=action_name,
            impact_level=impact_level,
        )
        return req

    def process_human_decision(
        self, action_id: str, approved: bool, reviewer_comments: Optional[str] = None
    ) -> ActionApprovalResponse:
        """Records human decision and releases or blocks execution."""
        if action_id not in self._pending_requests:
            raise KeyError(f"No pending HITL request found with ID {action_id}")

        req = self._pending_requests.pop(action_id)
        logger.info(
            "hitl_decision_recorded",
            action_id=action_id,
            action_name=req.action_name,
            approved=approved,
            comments=reviewer_comments,
        )
        return ActionApprovalResponse(approved=approved, reviewer_comments=reviewer_comments)


_global_hitl_checkpoint: Optional[HumanInTheLoopCheckpoint] = None


def get_hitl_checkpoint() -> HumanInTheLoopCheckpoint:
    """Returns singleton instance of HumanInTheLoopCheckpoint."""
    global _global_hitl_checkpoint
    if _global_hitl_checkpoint is None:
        _global_hitl_checkpoint = HumanInTheLoopCheckpoint()
    return _global_hitl_checkpoint
