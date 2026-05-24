# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import contextlib
import os
import sys
import uuid
from typing import Annotated, List, Optional

from mcp_behavex.tools import _state


async def run_tests(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to run. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
    tags: Annotated[
        Optional[List[str]],
        "Tag filters. Each entry maps to one --tags argument (AND logic between entries, OR within an entry using commas).",
    ] = None,
    parallel_processes: Annotated[
        Optional[int],
        "Number of parallel worker processes. Omit for single-process execution.",
    ] = None,
    parallel_scheme: Annotated[
        Optional[str],
        "'scenario' (default) or 'feature'. Only relevant when parallel_processes > 1.",
    ] = None,
    output_folder: Annotated[
        Optional[str],
        "Output directory for HTML/JSON/XML reports. Defaults to BEHAVEX_OUTPUT_FOLDER env var. Omit to suppress all file output.",
    ] = None,
    no_report: Annotated[
        bool,
        "Set True to skip all file output. Faster for CI or agent use when you only need pass/fail.",
    ] = False,
    dry_run: Annotated[
        bool,
        "Set True to list matching scenarios without executing steps.",
    ] = False,
    stop: Annotated[
        bool,
        "Set True to stop execution after the first failure.",
    ] = False,
) -> dict:
    """Run BehaveX tests and return a structured result.

    Returns a dict with:
    - run_id: unique UUID for this run
    - exit_code: 0 = all passed, 1 = failures or errors
    - status: 'passed', 'failed', or 'stopped'
    - summary: {total, passed, failed, errored, skipped, manual} scenario counts
    - failed_scenarios: list of {name, feature, status, error_msg}
    - output_folder: path where reports were written (empty if no_report=True)
    """
    if not _state.execution_lock.acquire(blocking=False):
        return {
            "error": (
                "A test run is already in progress. BehaveX uses process-wide state "
                "and cannot run concurrently. Call stop_run to cancel it, or wait for "
                "it to finish."
            ),
            "status": "busy",
            "active_run_id": _state.active_run_id,
        }
    try:
        from behavex import BehaveXRunner

        resolved_paths = paths or _default_paths()
        resolved_output = output_folder or os.environ.get("BEHAVEX_OUTPUT_FOLDER", "")

        runner = BehaveXRunner(
            paths=resolved_paths,
            tags=tags or [],
            parallel_processes=parallel_processes,
            parallel_scheme=parallel_scheme,
            output_folder=resolved_output,
            no_report=no_report,
            dry_run=dry_run,
            stop=stop,
        )

        session_id = str(uuid.uuid4())
        _state.stop_event.clear()
        _state.active_run_id = session_id
        _state.active_runner = runner

        loop = asyncio.get_running_loop()

        def _run_sync():
            with contextlib.redirect_stdout(sys.stderr):
                return runner.run()

        # Run the blocking BehaveX call in a thread so the event loop stays
        # free to handle stop_run requests while tests are executing.
        future = loop.run_in_executor(None, _run_sync)

        try:
            # asyncio.shield keeps the thread future alive if the outer task is
            # cancelled (e.g. Claude Desktop closes mid-run), so we can still
            # signal a clean stop and let in-flight scenarios finish.
            result = await asyncio.shield(future)
        except asyncio.CancelledError:
            # Client disconnected — signal BehaveX to stop the worker pool.
            runner.stop()
            _state.stop_event.set()
            # Re-raise so FastMCP knows this task was cancelled. The thread
            # will complete on its own after runner.stop() drains in-flight work.
            raise
        except Exception:
            if _state.stop_event.is_set():
                # stop_run was called and caused the thread to raise.
                return {
                    "run_id": session_id,
                    "status": "stopped",
                    "message": "Run was cancelled via stop_run.",
                }
            raise
        finally:
            _state.active_runner = None
            _state.active_run_id = None
    finally:
        _state.execution_lock.release()

    if _state.stop_event.is_set():
        # stop_run was called but the thread returned cleanly (parallel
        # executor drained without raising). Return partial results.
        return {
            "status": "stopped",
            "message": "Run was cancelled via stop_run. Results below reflect partial execution.",
            **_build_result(result, dry_run),
        }

    return _build_result(result, dry_run)


def _build_result(result, dry_run: bool) -> dict:
    summary = result.summary
    out: dict = {
        "run_id": result.run_id,
        "exit_code": result.exit_code,
        "status": "passed" if result.passed else "failed",
        "output_folder": result.output_folder,
        "summary": {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "errored": summary.errored,
            "skipped": summary.skipped,
            "manual": summary.manual,
            "muted": summary.muted,
            "untested": summary.untested,
        },
        "failed_scenarios": [
            {
                "name": s.name,
                "feature": s.feature,
                "status": s.status,
                "error_msg": s.error_msg,
            }
            for s in result.failed_scenarios
        ],
        "errored_scenarios": [
            {
                "name": s.name,
                "feature": s.feature,
                "status": s.status,
                "error_msg": s.error_msg,
            }
            for s in result.errored_scenarios
        ],
        "muted_scenarios": [
            {
                "name": s.name,
                "feature": s.feature,
                "status": s.status,
                "error_msg": s.error_msg,
            }
            for s in result.muted_scenarios
        ],
    }
    if summary.total == 0 and not dry_run:
        out["no_scenarios_matched"] = True
        out["warning"] = (
            "No scenarios were executed. If you specified tags, verify they exist "
            "in the suite (use list_tags to check). A run with zero scenarios "
            "always exits with code 0 regardless of the tag filter."
        )
    return out


def _default_paths() -> List[str]:
    env = os.environ.get("BEHAVEX_FEATURES_PATH", "")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    return ["features"]
