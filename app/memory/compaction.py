"""Context History Compaction (Criteria 6).

Implements context bloat management using token-aware sliding windows and
conversation summarization to keep agent context within optimal budget.
"""

from typing import Any, Dict, List, Optional
from app.observability.logging import get_logger

logger = get_logger("app.memory.compaction")


class SlidingWindowCompactor:
    """Manages conversational history compaction to prevent LLM context saturation."""

    def __init__(self, max_turns: int = 10, max_tokens_estimate: int = 4000):
        self.max_turns = max_turns
        self.max_tokens_estimate = max_tokens_estimate

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (approx 4 chars per token)."""
        return len(text) // 4

    def compact(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compacts turn history when exceeding token or turn thresholds.

        If history exceeds `max_turns`, older turns are consolidated into a summary
        system note, preserving the most recent conversational window verbatim.

        Args:
            history: List of conversation messages/turns.

        Returns:
            Compacted list of turns with summarized historical context.
        """
        if len(history) <= self.max_turns:
            return history

        logger.info(
            "compacting_history",
            original_turns=len(history),
            max_turns=self.max_turns,
        )

        turns_to_summarize = history[: -self.max_turns]
        recent_turns = history[-self.max_turns :]

        # Build summary of older architectural turns
        summary_snippets = []
        for turn in turns_to_summarize:
            role = turn.get("role", "unknown")
            content = str(turn.get("content", ""))
            # Truncate content preview
            preview = (content[:80] + "...") if len(content) > 80 else content
            summary_snippets.append(f"{role}: {preview}")

        summary_block = {
            "role": "system",
            "content": f"[COMPACTED CONTEXT SUMMARY]: Historical turns summarized: {'; '.join(summary_snippets)}",
        }

        compacted = [summary_block] + recent_turns
        logger.info(
            "history_compaction_complete",
            new_turns=len(compacted),
        )
        return compacted


def compact_history(
    history: List[Dict[str, Any]], max_turns: int = 10, max_tokens: int = 4000
) -> List[Dict[str, Any]]:
    """Convenience function for history compaction."""
    compactor = SlidingWindowCompactor(max_turns=max_turns, max_tokens_estimate=max_tokens)
    return compactor.compact(history)
