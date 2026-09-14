"""Intent vs. Outcome Capture (Criteria 14).

Explicitly tracks and logs the agent's intended action *before* execution
and the concrete outcome *after* execution, linking them via correlation ID.
"""

import functools
import time
import uuid
from typing import Any, Callable, Dict, Optional
from app.observability.logging import get_logger

logger = get_logger("app.observability.intent_tracker")


def record_intent_and_outcome(
    agent_name: str,
    intent: str,
    action_type: str,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> str:
    """Logs the declared intent of an agent prior to tool/subagent execution.

    Args:
        agent_name: Identifier of the agent declaring intent.
        intent: Human-readable statement of what the agent plans to achieve.
        action_type: Category of action (e.g. 'TOOL_INVOCATION', 'SUBAGENT_DELEGATION').
        payload: Input arguments or target parameters.
        correlation_id: Optional trace/correlation ID. Generated if omitted.

    Returns:
        The correlation ID to correlate with the outcome log.
    """
    cid = correlation_id or str(uuid.uuid4())
    logger.info(
        "agent_intent_declared",
        stage="INTENT",
        correlation_id=cid,
        agent_name=agent_name,
        intent=intent,
        action_type=action_type,
        payload=payload or {},
    )
    return cid


def record_outcome(
    correlation_id: str,
    agent_name: str,
    status: str,
    outcome_summary: str,
    duration_ms: float,
    result_data: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """Logs the actual outcome of an executed action, paired with its prior intent."""
    log_method = logger.error if status == "FAILURE" else logger.info
    log_method(
        "agent_outcome_recorded",
        stage="OUTCOME",
        correlation_id=correlation_id,
        agent_name=agent_name,
        status=status,
        outcome_summary=outcome_summary,
        duration_ms=round(duration_ms, 2),
        result_data=result_data,
        error=error,
    )


def trace_action(agent_name: str, intent_description: str):
    """Decorator for functions/tools to automatically capture Intent vs Outcome."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cid = record_intent_and_outcome(
                agent_name=agent_name,
                intent=intent_description,
                action_type=func.__name__,
                payload={"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}},
            )
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                record_outcome(
                    correlation_id=cid,
                    agent_name=agent_name,
                    status="SUCCESS",
                    outcome_summary=f"Successfully executed {func.__name__}",
                    duration_ms=duration_ms,
                    result_data=result,
                )
                return result
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                record_outcome(
                    correlation_id=cid,
                    agent_name=agent_name,
                    status="FAILURE",
                    outcome_summary=f"Execution failed for {func.__name__}: {str(exc)}",
                    duration_ms=duration_ms,
                    error=str(exc),
                )
                raise
        return wrapper
    return decorator
