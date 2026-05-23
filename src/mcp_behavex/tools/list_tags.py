# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import (
    default_paths,
    discover_feature_files,
    parse_feature_file,
    scan_files,
)


def list_tags(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to scan. Defaults to BEHAVEX_FEATURES_PATH env var. Narrow this when the full suite times out.",
    ] = None,
) -> dict:
    """List all tags used across feature files with scenario and feature counts.

    Results are mtime-cached — repeated calls are near-instant for unchanged files.
    Returns partial results with a warning if scanning exceeds the time limit.

    Returns a dict with:
    - tags: list of {tag, scenario_count, feature_count}, sorted by scenario_count desc
    - total_tags: int
    - partial: true if the scan was cut short by the time limit
    - warning: explanation when partial=true
    """
    resolved_paths = paths or default_paths()
    filepaths = discover_feature_files(resolved_paths)

    parsed_features, partial, warning = scan_files(filepaths, parse_feature_file)

    tag_data: dict[str, dict] = {}
    for parsed in parsed_features:
        feature_tags = {t.lstrip("@") for t in parsed["tags"]}
        feature_name = parsed["name"]
        for scenario in parsed["scenarios"]:
            scenario_tags = {t.lstrip("@") for t in scenario["tags"]}
            for tag in feature_tags | scenario_tags:
                if tag not in tag_data:
                    tag_data[tag] = {"tag": f"@{tag}", "scenario_count": 0, "features": set()}
                tag_data[tag]["scenario_count"] += 1
                tag_data[tag]["features"].add(feature_name)

    tags = [
        {"tag": d["tag"], "scenario_count": d["scenario_count"], "feature_count": len(d["features"])}
        for d in tag_data.values()
    ]
    tags.sort(key=lambda t: (-t["scenario_count"], t["tag"]))

    out = {"tags": tags, "total_tags": len(tags), "partial": partial}
    if warning:
        out["warning"] = warning
    return out
