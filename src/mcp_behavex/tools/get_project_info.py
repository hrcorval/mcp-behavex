# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths, discover_feature_files, parse_feature_file


def get_project_info(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to analyze. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
) -> dict:
    """Analyze the test suite and return configuration, counts, and run recommendations.

    Call this before run_tests when you are unsure how to run the suite — it tells
    you how many scenarios exist, what parallel settings to use, and what the current
    environment is configured to do.

    Returns a dict with:
    - config: current environment configuration (paths, output folder)
    - suite: {total_features, total_scenarios, total_tags}
    - recommendation: ready-to-use run_tests parameters based on suite size
    - guidance: human-readable explanation of the recommendation
    """
    resolved_paths = paths or default_paths()
    feature_files = discover_feature_files(resolved_paths)

    total_features = 0
    total_scenarios = 0
    all_tags: set[str] = set()

    for filepath in feature_files:
        parsed = parse_feature_file(filepath)
        if parsed is None:
            continue
        total_features += 1
        total_scenarios += len(parsed["scenarios"])
        for t in parsed["tags"]:
            all_tags.add(t.lstrip("@"))
        for s in parsed["scenarios"]:
            for t in s["tags"]:
                all_tags.add(t.lstrip("@"))

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
        params = {
            "parallel_processes": None,
            "parallel_scheme": None,
            "no_report": False,
        }
        guidance = (
            f"{total_scenarios} scenarios — run sequentially (no parallel). "
            "Parallel overhead is not worth it for small suites."
        )

    elif total_scenarios < 50:
        params = {
            "parallel_processes": 2,
            "parallel_scheme": "scenario",
            "no_report": False,
        }
        guidance = (
            f"{total_scenarios} scenarios — use parallel_processes=2, parallel_scheme='scenario'. "
            "Scenario-level parallelism distributes individual scenarios across workers."
        )

    elif total_features >= 10 and total_scenarios / total_features >= 5:
        params = {
            "parallel_processes": 4,
            "parallel_scheme": "feature",
            "no_report": False,
        }
        guidance = (
            f"{total_scenarios} scenarios across {total_features} features — "
            "use parallel_processes=4, parallel_scheme='feature'. "
            "Feature-level parallelism works well when features are large and numerous."
        )

    else:
        params = {
            "parallel_processes": 4,
            "parallel_scheme": "scenario",
            "no_report": False,
        }
        guidance = (
            f"{total_scenarios} scenarios — use parallel_processes=4, parallel_scheme='scenario'. "
            "Scenario-level parallelism gives the best distribution for large suites."
        )

    return params, guidance
