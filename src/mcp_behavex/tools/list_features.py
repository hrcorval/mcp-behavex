# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import (
    default_paths,
    discover_feature_files,
    parse_feature_file,
    scan_files,
)


def list_features(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to scan. Defaults to BEHAVEX_FEATURES_PATH env var. Narrow this when the full suite times out.",
    ] = None,
    tags: Annotated[
        Optional[List[str]],
        "Only return features/scenarios that match these tags. Omit to return all.",
    ] = None,
) -> dict:
    """List all feature files and their scenarios without executing any tests.

    Results are mtime-cached — repeated calls are near-instant for unchanged files.
    Returns partial results with a warning if scanning exceeds the time limit.

    Returns a dict with:
    - features: list of {name, filename, tags, scenarios}
    - total_features: int
    - total_scenarios: int
    - partial: true if the scan was cut short by the time limit
    - warning: explanation when partial=true
    """
    resolved_paths = paths or default_paths()
    filepaths = sorted(discover_feature_files(resolved_paths))
    tag_filter = {t.lstrip("@") for t in tags} if tags else None

    parsed_features, partial, warning = scan_files(filepaths, parse_feature_file)

    features = []
    total_scenarios = 0
    for parsed in parsed_features:
        scenarios = parsed["scenarios"]
        if tag_filter:
            scenarios = [
                s for s in scenarios
                if tag_filter.intersection(t.lstrip("@") for t in s["tags"])
                or tag_filter.intersection(t.lstrip("@") for t in parsed["tags"])
            ]
            if not scenarios:
                continue
        features.append({
            "name": parsed["name"],
            "filename": parsed["filename"],
            "tags": parsed["tags"],
            "scenarios": scenarios,
        })
        total_scenarios += len(scenarios)

    out = {
        "features": features,
        "total_features": len(features),
        "total_scenarios": total_scenarios,
        "partial": partial,
    }
    if warning:
        out["warning"] = warning
    return out
