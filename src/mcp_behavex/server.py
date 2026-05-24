# -*- coding: utf-8 -*-
"""mcp-behavex: MCP server for BehaveX."""
from __future__ import annotations

from fastmcp import FastMCP

from mcp_behavex.tools.coverage_by_tag import coverage_by_tag
from mcp_behavex.tools.get_project_info import get_project_info
from mcp_behavex.tools.list_features import list_features
from mcp_behavex.tools.list_steps import list_steps
from mcp_behavex.tools.list_tags import list_tags
from mcp_behavex.tools.run_tests import run_tests
from mcp_behavex.tools.stop_run import stop_run

mcp = FastMCP(
    name="mcp-behavex",
    instructions="""
BehaveX MCP server for running and inspecting BDD test suites.

## Decision flow

1. **Before running tests for the first time**, call get_project_info. It returns the
   scenario count, feature count, and a ready-to-use recommendation for parallel settings.
   Never guess parallel_processes or parallel_scheme — let get_project_info tell you.

2. **To run tests**, call run_tests with the parameters from get_project_info. Always pass
   output_folder so results are persisted and coverage_by_tag can read them afterward.
   Use tags to scope the run when the user asks for a subset.

3. **To inspect the suite without running**, use list_features (see scenarios and their tags),
   list_tags (see all tags with counts), or list_steps (see available step definitions).

4. **After a run**, call coverage_by_tag to show pass/fail breakdown per tag. It reads the
   last report.json automatically from BEHAVEX_OUTPUT_FOLDER.

5. **To cancel an in-progress run**, call stop_run. For parallel runs it shuts down the
   worker pool immediately; for single-process runs it signals after the current scenario.

## Parallel execution rules

- parallel_scheme='scenario' distributes individual scenarios across workers — use when
  scenarios are independent and the suite is mixed in size.
- parallel_scheme='feature' distributes whole feature files — use when features are large
  and numerous (10+ features, 5+ scenarios each).
- Never use parallel_processes > 1 without also setting parallel_scheme.
- For < 10 scenarios, skip parallel entirely (overhead exceeds benefit).

## run_tests summary fields

The summary dict returned by run_tests contains all scenario outcome counts.
Always report ALL of them — never omit a field even if it is zero:

- **passed** — scenario completed without errors
- **failed** — assertion failure (step raised AssertionError)
- **error** — unexpected exception during execution (not an assertion)
- **skipped** — scenario was not executed (conditional skip, --stop, undefined step)
- **untested** — scenario was collected but never reached execution
- **manual** — scenario tagged @MANUAL or @WIP; not automated, never executes

Invariant: passed + failed + error + skipped + untested + manual == total

@MUTE scenarios are automatically excluded from every run — they will never
appear in results.

## Tag syntax

- Single tag: tags=["@smoke"]
- OR (either tag): tags=["@smoke,@regression"]  ← comma inside one string
- AND (both tags): tags=["@smoke", "@regression"]  ← two separate strings
""",
)

mcp.tool()(get_project_info)
mcp.tool()(run_tests)
mcp.tool()(stop_run)
mcp.tool()(list_features)
mcp.tool()(list_tags)
mcp.tool()(list_steps)
mcp.tool()(coverage_by_tag)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
