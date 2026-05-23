# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import (
    default_paths,
    discover_feature_files,
    parse_feature_file,
    scan_files,
)


def get_project_info(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to analyze. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
) -> dict:
    """Analyze the test suite and return configuration, counts, and run recommendations.

    Call this before run_tests when you are unsure how to run the suite — it tells
    you how many scenarios exist, what parallel settings to use, and what the current
    environment is configured to do. Results are mtime-cached for fast repeated calls.

    Returns a dict with:
    - config: current environment configuration (paths, output folder)
    - suite: {total_features, total_scenarios, total_tags}
    - recommendation: ready-to-use run_tests parameters based on suite size
    - guidance: human-readable explanation of the recommendation
    """
    resolved_paths = paths or default_paths()
    filepaths = discover_feature_files(resolved_paths)

    parsed_features, _, _ = scan_files(filepaths, parse_feature_file)

    total_features = len(parsed_features)
    total_scenarios = sum(len(p["scenarios"]) for p in parsed_features)
    all_tags: set[str] = set()
    for p in parsed_features:
        all_tags.update(t.lstrip("@") for t in p["tags"])
        for s in p["scenarios"]:
            all_tags.update(t.lstrip("@") for t in s["tags"])

    recommendation, guidance = _recommend(total_scenarios, total_features)
    recommendation["paths"] = resolved_paths
    recommendation["output_folder"] = os.environ.get("BEHAVEX_OUTPUT_FOLDER", "")

    return {
        "config": {
            "features_path": os.environ.get("BEHAVEX_FEATURES_PATH", ""),
            "output_folder": os.environ.get("BEHAVEX_OUTPUT_FOLDER", ""),
        },
        "suite": {
            "total_features": total_features,
            "total_scenarios": total_scenarios,
            "total_tags": len(all_tags),
        },
        "recommendation": recommendation,
        "guidance": guidance,
    }


def _recommend(total_scenarios: int, total_features: int) -> tuple[dict, str]:
    if total_scenarios == 0:
        return (
            {"no_report": True},
            "No scenarios found. Check that BEHAVEX_FEATURES_PATH points to the correct directory.",
        )
    if total_scenarios < 10:
        return (
            {"parallel_processes": None, "parallel_scheme": None, "no_report": False},
            f"{total_scenarios} scenarios — run sequentially (no parallel). Overhead not worth it for small suites.",
        )
    if total_scenarios < 50:
        return (
            {"parallel_processes": 2, "parallel_scheme": "scenario", "no_report": False},
            f"{total_scenarios} scenarios — use parallel_processes=2, parallel_scheme='scenario'.",
        )
    if total_features >= 10 and total_scenarios / total_features >= 5:
        return (
            {"parallel_processes": 4, "parallel_scheme": "feature", "no_report": False},
            f"{total_scenarios} scenarios across {total_features} features — "
            "use parallel_processes=4, parallel_scheme='feature'.",
        )
    return (
        {"parallel_processes": 4, "parallel_scheme": "scenario", "no_report": False},
        f"{total_scenarios} scenarios — use parallel_processes=4, parallel_scheme='scenario'.",
    )
