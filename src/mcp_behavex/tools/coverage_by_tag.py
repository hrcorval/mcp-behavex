# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths, discover_feature_files, parse_feature_file


def coverage_by_tag(
    output_folder: Annotated[
        Optional[str],
        "Folder containing report.json from a previous run. Defaults to BEHAVEX_OUTPUT_FOLDER env var. If omitted or no report exists, falls back to static analysis.",
    ] = None,
    paths: Annotated[
        Optional[List[str]],
        "Feature paths for static fallback when no report is available. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
) -> dict:
    """Show scenario counts per tag, with pass/fail breakdown when a report is available.

    When report.json exists in output_folder, returns actual pass/fail/skipped counts
    from the last run. Otherwise returns a static count with status 'untested'.

    Returns a dict with:
    - source: 'report' or 'static'
    - coverage: list of {tag, total, passed, failed, skipped}, sorted by total desc
    - total_tags: int
    """
    resolved_output = output_folder or os.environ.get("BEHAVEX_OUTPUT_FOLDER", "")
    if resolved_output:
        report_path = os.path.join(resolved_output, "report.json")
        if os.path.exists(report_path):
            return _from_report(report_path)

    return _from_features(paths)


def _from_report(report_path: str) -> dict:
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    tag_data: dict[str, dict] = {}

    for feature in data.get("features", []):
        feature_tags = {t.lstrip("@") for t in feature.get("tags", [])}
        for scenario in feature.get("scenarios", []):
            scenario_tags = {t.lstrip("@") for t in scenario.get("tags", [])}
            effective_tags = feature_tags | scenario_tags
            status = scenario.get("status", "skipped")

            for tag in effective_tags:
                if tag not in tag_data:
                    tag_data[tag] = {"tag": f"@{tag}", "total": 0, "passed": 0, "failed": 0, "skipped": 0}
                tag_data[tag]["total"] += 1
                if status == "passed":
                    tag_data[tag]["passed"] += 1
                elif status in ("failed", "error"):
                    tag_data[tag]["failed"] += 1
                else:
                    tag_data[tag]["skipped"] += 1

    coverage = sorted(tag_data.values(), key=lambda t: (-t["total"], t["tag"]))
    return {"source": "report", "coverage": coverage, "total_tags": len(coverage)}


def _from_features(paths: Optional[List[str]]) -> dict:
    resolved_paths = paths or default_paths()
    feature_files = discover_feature_files(resolved_paths)

    tag_data: dict[str, dict] = {}

    for filepath in feature_files:
        parsed = parse_feature_file(filepath)
        if parsed is None:
            continue

        feature_tags = {t.lstrip("@") for t in parsed["tags"]}
        for scenario in parsed["scenarios"]:
            scenario_tags = {t.lstrip("@") for t in scenario["tags"]}
            effective_tags = feature_tags | scenario_tags

            for tag in effective_tags:
                if tag not in tag_data:
                    tag_data[tag] = {"tag": f"@{tag}", "total": 0, "passed": 0, "failed": 0, "skipped": 0}
                tag_data[tag]["total"] += 1

    coverage = sorted(tag_data.values(), key=lambda t: (-t["total"], t["tag"]))
    return {"source": "static", "coverage": coverage, "total_tags": len(coverage)}
