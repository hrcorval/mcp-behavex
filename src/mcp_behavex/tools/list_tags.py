# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths, discover_feature_files, parse_feature_file


def list_tags(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to scan. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
) -> dict:
    """List all tags used across feature files with scenario and feature counts.

    Feature-level tags are counted against every scenario in that feature.

    Returns a dict with:
    - tags: list of {tag, scenario_count, feature_count}, sorted by scenario_count desc
    - total_tags: int
    """
    resolved_paths = paths or default_paths()
    feature_files = discover_feature_files(resolved_paths)

    tag_data: dict[str, dict] = {}

    for filepath in feature_files:
        parsed = parse_feature_file(filepath)
        if parsed is None:
            continue

        feature_tags = {t.lstrip("@") for t in parsed["tags"]}
        feature_name = parsed["name"]

        for scenario in parsed["scenarios"]:
            scenario_tags = {t.lstrip("@") for t in scenario["tags"]}
            effective_tags = feature_tags | scenario_tags

            for tag in effective_tags:
                if tag not in tag_data:
                    tag_data[tag] = {"tag": f"@{tag}", "scenario_count": 0, "features": set()}
                tag_data[tag]["scenario_count"] += 1
                tag_data[tag]["features"].add(feature_name)

    tags = [
        {
            "tag": d["tag"],
            "scenario_count": d["scenario_count"],
            "feature_count": len(d["features"]),
        }
        for d in tag_data.values()
    ]
    tags.sort(key=lambda t: (-t["scenario_count"], t["tag"]))

    return {
        "tags": tags,
        "total_tags": len(tags),
    }
