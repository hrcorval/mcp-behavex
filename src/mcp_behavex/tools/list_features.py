# -*- coding: utf-8 -*-
from __future__ import annotations

import glob
import os
from typing import Annotated, List, Optional


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
    resolved_paths = paths or _default_paths()
    feature_files = _discover_feature_files(resolved_paths)

    tag_filter = set(t.lstrip("@") for t in tags) if tags else None

    features = []
    total_scenarios = 0

    for filepath in sorted(feature_files):
        parsed = _parse_feature_file(filepath)
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


def _default_paths() -> List[str]:
    env = os.environ.get("BEHAVEX_FEATURES_PATH", "")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    return ["features"]


def _discover_feature_files(paths: List[str]) -> List[str]:
    files: List[str] = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".feature"):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(glob.glob(os.path.join(path, "**", "*.feature"), recursive=True))
        else:
            files.extend(glob.glob(path, recursive=True))
    return list(dict.fromkeys(files))  # deduplicate, preserve order


def _parse_feature_file(filepath: str) -> Optional[dict]:
    try:
        from behave.parser import Parser
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
        parser = Parser(language="en")
        feature = parser.parse(text, filename=filepath)
        if feature is None:
            return None
        scenarios = []
        for scenario in feature.scenarios:
            # ScenarioOutline expands into multiple examples — collect the outline itself
            scenarios.append({
                "name": scenario.name,
                "line": scenario.line,
                "tags": [str(t) for t in scenario.tags],
            })
        return {
            "name": feature.name,
            "filename": filepath,
            "tags": [str(t) for t in feature.tags],
            "scenarios": scenarios,
        }
    except Exception:
        return None
