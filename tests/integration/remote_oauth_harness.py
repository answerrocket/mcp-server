"""Manual remote-mode (OAuth) check: run with BASE, COPILOT_ID and a Bearer ACCESS_TOKEN."""
import os
import sys
import anyio
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

BASE = os.environ.get("BASE", "http://localhost:1234")
COPILOT_ID = os.environ.get("COPILOT_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")


async def main():
    if not (COPILOT_ID and ACCESS_TOKEN):
        sys.exit("Set BASE, COPILOT_ID and ACCESS_TOKEN (see module docstring).")
    url = f"{BASE}/mcp/agent/{COPILOT_ID}/"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools/list ->", [t.name for t in tools.tools])
            res = await session.call_tool("trend_analysis", {
                "metrics": ["sales"], "breakouts": ["brand"], "time_granularity": "month",
                "periods": [f"2022-{m:02d}" for m in range(1, 13)],
            })
            text = "\n".join(c.text for c in res.content if hasattr(c, "text"))
            print("trend_analysis isError:", res.isError)
            print("result (first 300):\n", text[:300])
            print("\nREMOTE E2E:", "PASS" if (not res.isError and "fail" not in text.lower()) else "FAIL")


if __name__ == "__main__":
    anyio.run(main)
