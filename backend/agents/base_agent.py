"""Base class for all agents.

Each agent has a single responsibility (SOLID-S) and is invoked through
``run`` which provides uniform logging, timing, and error containment.
Concrete agents implement ``_execute`` with their typed input/output.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.logging import get_logger

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class AgentError(Exception):
    """Raised when an agent fails. Wraps the original exception."""


@dataclass(frozen=True)
class AgentResult(Generic[TOut]):
    ok: bool
    value: TOut | None
    error: str | None
    duration_ms: float


class BaseAgent(ABC, Generic[TIn, TOut]):
    name: str = "BaseAgent"

    def __init__(self) -> None:
        self.log = get_logger(f"agent.{self.name}")

    async def run(self, payload: TIn) -> AgentResult[TOut]:
        start = time.perf_counter()
        self.log.info("start")
        try:
            value = await self._execute(payload)
        except Exception as exc:  # noqa: BLE001 - intentional boundary
            duration = (time.perf_counter() - start) * 1000
            self.log.exception("failed after %.1fms", duration)
            return AgentResult(ok=False, value=None, error=str(exc), duration_ms=duration)
        duration = (time.perf_counter() - start) * 1000
        self.log.info("ok in %.1fms", duration)
        return AgentResult(ok=True, value=value, error=None, duration_ms=duration)

    @abstractmethod
    async def _execute(self, payload: TIn) -> TOut: ...
