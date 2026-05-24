# -*- coding: utf-8 -*-
from __future__ import annotations

from mcp_behavex.tools import _state


def stop_run() -> dict:
    """Stop the currently running test run.

    For parallel runs, shuts down the worker pool immediately — in-flight
    scenarios finish and then the run returns with partial results.
    For single-process runs, the current scenario completes before the run
    returns (BehaveX has no mid-step interruption mechanism).

    Returns a dict with:
    - status: 'stop_requested' | 'no_run'
    - run_id: session ID of the run that was stopped (if any)
    - message: human-readable explanation
    """
    if not _state.execution_lock.locked():
        return {
            "status": "no_run",
            "message": "No test run is currently in progress.",
        }

    _state.stop_event.set()

    runner = _state.active_runner
    parallel_stopped = False
    if runner is not None:
        runner.stop()
        parallel_stopped = True

    if parallel_stopped:
        detail = "Parallel worker pool shut down. In-flight scenarios will finish, then the run returns with partial results."
    else:
        detail = "Stop signal set. Single-process runs cannot be interrupted mid-scenario — the current scenario will complete before the run returns."

    return {
        "status": "stop_requested",
        "run_id": _state.active_run_id,
        "message": detail,
    }
