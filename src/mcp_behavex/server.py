# -*- coding: utf-8 -*-
"""mcp-behavex: MCP server for BehaveX."""
from __future__ import annotations

from fastmcp import FastMCP

from mcp_behavex.tools.list_features import list_features
from mcp_behavex.tools.run_tests import run_tests

mcp = FastMCP(
    name="mcp-behavex",
    instructions=(
        "BehaveX MCP server. Use run_tests to execute BDD scenarios and get structured "
        "pass/fail results. Use list_features to inspect available feature files and "
        "scenarios before deciding what to run. Configure default paths via "
        "BEHAVEX_FEATURES_PATH and BEHAVEX_OUTPUT_FOLDER environment variables."
    ),
)

mcp.tool()(run_tests)
mcp.tool()(list_features)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
