# -*- coding: utf-8 -*-
from __future__ import annotations

import contextlib
import os
import sys
import threading
from typing import Annotated, List, Optional

# BehaveX uses process-wide globals — only one run at a time is safe.
_execution_lock = threading.Lock()


def run_tests(
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
    - status: 'passed' or 'failed'
    - summary: {total, passed, failed, skipped} scenario counts
    - failed_scenarios: list of {name, feature, status, error_msg}
    - output_folder: path where reports were written (empty if no_report=True)
    """
    if not _execution_lock.acquire(blocking=False):
        return {
            "error": "A test run is already in progress. BehaveX uses process-wide state and cannot run concurrently. Wait for the current run to finish before calling run_tests again.",
            "status": "busy",
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
        # Redirect stdout to stderr during the run: BehaveX prints progress/env tables
        # to stdout, which would corrupt the MCP stdio JSON-RPC stream.
        with contextlib.redirect_stdout(sys.stderr):
            result = runner.run()
    finally:
        _execution_lock.release()

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
