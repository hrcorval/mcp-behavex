# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths, discover_feature_files, parse_feature_file


def list_features(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths to scan. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
    tags: Annotated[
        Optional[List[str]],
        "Only return features/scenarios that match these tags. Omit to return all.",
    ] = None,
) -> dict:
    """List all feature files and their scenarios without executing any tests.

    Returns a dict with:
    - features: list of {name, filename, tags, scenarios}
      - scenarios: list of {name, line, tags}
    - total_features: int
    - total_scenarios: int
    """
    resolved_paths = paths or default_paths()
    feature_files = discover_feature_files(resolved_paths)

    tag_filter = set(t.lstrip("@") for t in tags) if tags else None

    features = []
    total_scenarios = 0

    for filepath in sorted(feature_files):
        parsed = parse_feature_file(filepath)
        if parsed is None:
            continue

        scenarios = parsed["scenarios"]
        if tag_filter:
            scenarios = [
                s for s in scenarios
                if tag_filter.intersection(t.lstrip("@") for t in s["tags"])
                or tag_filter.intersection(t.lstrip("@") for t in parsed["tags"])
            ]

        if tag_filter and not scenarios:
            continue

        features.append({
            "name": parsed["name"],
            "filename": parsed["filename"],
            "tags": parsed["tags"],
            "scenarios": scenarios,
        })
        total_scenarios += len(scenarios)

    return {
        "features": features,
        "total_features": len(features),
        "total_scenarios": total_scenarios,
    }
