"""Live local/stdio e2e against a real Max; gated by MCP_E2E + AR_URL/AR_TOKEN/COPILOT_ID."""
import os
import sys

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

pytestmark = pytest.mark.skipif(
    os.getenv("MCP_E2E") != "1"
    or not all(os.getenv(k) for k in ("AR_URL", "AR_TOKEN", "COPILOT_ID")),
    reason="set MCP_E2E=1 + AR_URL/AR_TOKEN/COPILOT_ID to run the live e2e test",
)


def _server_params():
    env = {
        **os.environ,
        "MCP_MODE": "local",
        "MCP_TRANSPORT": "stdio",
    }
    return StdioServerParameters(command=sys.executable, args=["-m", "mcp_server"], env=env)


@pytest.mark.asyncio
async def test_list_and_call_trend_analysis():
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names, "expected the copilot's skills as tools"
            assert "trend_analysis" in names, f"trend_analysis not in {names}"

            res = await session.call_tool(
                "trend_analysis",
                {
                    "metrics": ["sales"],
                    "breakouts": ["brand"],
                    "time_granularity": "month",
                    "periods": [f"2022-{m:02d}" for m in range(1, 13)],
                },
            )
            text = "\n".join(c.text for c in res.content if hasattr(c, "text"))
            assert res.isError is False
            assert "fail" not in text.lower(), f"skill execution failed: {text[:300]}"
            assert text.strip(), "expected non-empty skill result"
