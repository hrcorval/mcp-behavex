# -*- coding: utf-8 -*-
"""mcp-behavex: MCP server for BehaveX."""
from __future__ import annotations

from fastmcp import FastMCP

from mcp_behavex.tools.coverage_by_tag import coverage_by_tag
from mcp_behavex.tools.list_features import list_features
from mcp_behavex.tools.list_steps import list_steps
from mcp_behavex.tools.list_tags import list_tags
from mcp_behavex.tools.run_tests import run_tests

mcp = FastMCP(
    name="mcp-behavex",
    instructions=(
        "BehaveX MCP server. Use run_tests to execute BDD scenarios and get structured "
        "pass/fail results. Use list_features to inspect available feature files and "
        "scenarios. Use list_tags to see all tags with scenario counts. Use list_steps "
        "to see all available step definitions. Use coverage_by_tag to analyze pass/fail "
        "rates per tag from the last test run. Configure default paths via "
        "BEHAVEX_FEATURES_PATH and BEHAVEX_OUTPUT_FOLDER environment variables."
    ),
)

mcp.tool()(run_tests)
mcp.tool()(list_features)
mcp.tool()(list_tags)
mcp.tool()(list_steps)
mcp.tool()(coverage_by_tag)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
