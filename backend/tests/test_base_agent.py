import pytest

from agents.base_agent import BaseAgent


class _DoubleAgent(BaseAgent[int, int]):
    name = "double"

    async def _execute(self, payload: int) -> int:
        return payload * 2


class _BoomAgent(BaseAgent[int, int]):
    name = "boom"

    async def _execute(self, payload: int) -> int:
        raise RuntimeError("nope")


@pytest.mark.asyncio
async def test_agent_returns_value_on_success():
    result = await _DoubleAgent().run(21)
    assert result.ok is True
    assert result.value == 42
    assert result.error is None
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_agent_contains_failure():
    result = await _BoomAgent().run(1)
    assert result.ok is False
    assert result.value is None
    assert "nope" in (result.error or "")
