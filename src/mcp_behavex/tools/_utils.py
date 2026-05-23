# -*- coding: utf-8 -*-
"""Shared utilities: file discovery, feature parsing, mtime cache, timed scan."""
from __future__ import annotations

import glob
import os
import time
from typing import Any, Callable, List, Optional, Tuple

_SCAN_TIMEOUT = 25  # seconds before returning partial results

# mtime-based parse cache: filepath → (mtime, parsed_result)
# Lives for the lifetime of the MCP server process — warm after first scan.
_cache: dict[str, Tuple[float, Any]] = {}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

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


def discover_step_files(paths: List[str]) -> List[str]:
    files: List[str] = []
    for path in paths:
        if os.path.isfile(path):
            files.extend(glob.glob(os.path.join(os.path.dirname(path), "steps", "*.py")))
        elif os.path.isdir(path):
            files.extend(glob.glob(os.path.join(path, "**/steps/*.py"), recursive=True))
    return list(dict.fromkeys(files))


# ---------------------------------------------------------------------------
# Generic cached + timed scanner
# ---------------------------------------------------------------------------

def scan_files(
    filepaths: List[str],
    parse_fn: Callable[[str], Any],
    timeout: float = _SCAN_TIMEOUT,
) -> Tuple[List[Any], bool, Optional[str]]:
    """Parse files using mtime caching and a hard timeout.

    Returns (results, partial, warning):
    - results: list of parse_fn outputs (None entries skipped)
    - partial: True when the timeout was hit before all files were processed
    - warning: human-readable explanation when partial=True, else None

    The first call warms the cache; subsequent calls skip unchanged files via
    a single os.stat() per file, making repeated scans near-instant.
    """
    results: List[Any] = []
    total = len(filepaths)
    start = time.monotonic()

    for i, filepath in enumerate(filepaths):
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            return results, True, (
                f"Scan stopped after {elapsed:.0f}s — processed {i} of {total} files. "
                "Pass 'paths' to scope the scan to a specific file or subdirectory."
            )
        result = _cached(filepath, parse_fn)
        if result is not None:
            results.append(result)

    return results, False, None


def _cached(filepath: str, parse_fn: Callable[[str], Any]) -> Any:
    """Return cached result if the file's mtime is unchanged, else re-parse."""
    try:
        mtime = os.stat(filepath).st_mtime
    except OSError:
        return None
    entry = _cache.get(filepath)
    if entry is not None and entry[0] == mtime:
        return entry[1]
    result = parse_fn(filepath)
    _cache[filepath] = (mtime, result)
    return result


# ---------------------------------------------------------------------------
# Feature file parser (parse_fn for feature tools)
# ---------------------------------------------------------------------------

def parse_feature_file(filepath: str) -> Optional[dict]:
    try:
        from behave.parser import Parser
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
        parser = Parser(language="en")
        feature = parser.parse(text, filename=filepath)
        if feature is None:
            return None
        return {
            "name": feature.name,
            "filename": filepath,
            "tags": [str(t) for t in feature.tags],
            "scenarios": [
                {
                    "name": s.name,
                    "line": s.line,
                    "tags": [str(t) for t in s.tags],
                }
                for s in feature.scenarios
            ],
        }
    except Exception:
        return None
