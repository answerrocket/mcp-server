"""Concurrent list_tools() for different copilots must not cross-contaminate."""
import asyncio

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.tool_registry import ToolRegistry

TOOLS = {
    "copilot-A": ["a_trend", "a_breakout"],
    "copilot-B": ["b_kpi"],
}


def _make_registry():
    mcp = FastMCP("test")
    reg = ToolRegistry(mcp=mcp, ar_url=None, ar_token=None, copilot_id=None)
    reg.setup_dynamic_registration()

    async def fake_register(copilot_id):
        # Sleep mid-registration to widen the interleaving window.
        await asyncio.sleep(0.05)
        for name in TOOLS[copilot_id]:
            async def _noop():
                return "ok"
            mcp.add_tool(_noop, name=name, description=name)

    reg._register_dynamic_tools = fake_register
    return reg


@pytest.mark.asyncio
async def test_concurrent_lists_do_not_cross_contaminate():
    reg = _make_registry()

    a, b = await asyncio.gather(
        reg._locked_list_tools("copilot-A"),
        reg._locked_list_tools("copilot-B"),
    )

    assert sorted(t.name for t in a) == sorted(TOOLS["copilot-A"])
    assert sorted(t.name for t in b) == sorted(TOOLS["copilot-B"])


@pytest.mark.asyncio
async def test_repeated_same_copilot_is_consistent():
    reg = _make_registry()
    results = await asyncio.gather(*[reg._locked_list_tools("copilot-A") for _ in range(5)])
    for r in results:
        assert sorted(t.name for t in r) == sorted(TOOLS["copilot-A"])
