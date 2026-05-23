# -*- coding: utf-8 -*-
"""Shared utilities for feature file discovery and parsing."""
from __future__ import annotations

import glob
import os
from typing import List, Optional


def default_paths() -> List[str]:
    env = os.environ.get("BEHAVEX_FEATURES_PATH", "")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    return ["features"]


def discover_feature_files(paths: List[str]) -> List[str]:
    files: List[str] = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".feature"):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(glob.glob(os.path.join(path, "**", "*.feature"), recursive=True))
        else:
            files.extend(glob.glob(path, recursive=True))
    return list(dict.fromkeys(files))


def parse_feature_file(filepath: str) -> Optional[dict]:
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
