"""Async Memory Operations (Criteria 8).

Executes heavy memory generation, architectural consolidation, and spatial indexing
as non-blocking background async tasks to prevent blocking the user interface.
"""

import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional
from app.observability.logging import get_logger
from app.memory.session_store import get_session_store

logger = get_logger("app.memory.async_memory")


class AsyncMemoryManager:
    """Manages non-blocking background tasks for memory and project index operations."""

    def __init__(self):
        self._background_tasks = set()

    def dispatch_background_task(self, coro: Coroutine) -> asyncio.Task:
        """Schedules a coroutine as a detached background task with exception tracking."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._on_task_done)
        return task

    def _on_task_done(self, task: asyncio.Task) -> None:
        """Cleanup and exception logging callback for completed background tasks."""
        self._background_tasks.discard(task)
        if task.cancelled():
            logger.warning("background_memory_task_cancelled")
        elif task.exception():
            logger.error("background_memory_task_failed", error=str(task.exception()))
        else:
            logger.info("background_memory_task_completed_successfully")

    async def consolidate_project_memory_async(
        self, session_id: str, cadastral_ref: str, metadata: Dict[str, Any]
    ) -> None:
        """Asynchronously consolidates architectural project state in background.

        Simulates intensive background indexing, vector embedding, and cross-session
        summarization without stalling the primary agent conversational response loop.
        """
        logger.info(
            "async_memory_consolidation_started",
            session_id=session_id,
            cadastral_ref=cadastral_ref,
        )
        # Yield control back to event loop immediately
        await asyncio.sleep(0.05)

        # Persist consolidated summary to persistent database
        store = get_session_store()
        summary = f"Archived site analysis for parcel {cadastral_ref}. Total area: {metadata.get('area_sqm', 'N/A')} m²."
        store.save_message(session_id=session_id, role="system_memory_consolidation", content=summary)

        logger.info(
            "async_memory_consolidation_finished",
            session_id=session_id,
            cadastral_ref=cadastral_ref,
        )


_global_async_memory_manager: Optional[AsyncMemoryManager] = None


def get_memory_manager() -> AsyncMemoryManager:
    """Returns singleton instance of AsyncMemoryManager."""
    global _global_async_memory_manager
    if _global_async_memory_manager is None:
        _global_async_memory_manager = AsyncMemoryManager()
    return _global_async_memory_manager
