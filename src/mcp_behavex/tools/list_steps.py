# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths, discover_step_files, scan_files

# Matches @given/@when/@then/@step with a single- or double-quoted string pattern.
# Handles optional u/r prefix (e.g. u"pattern").
_STEP_RE = re.compile(
    r'@(given|when|then|step)\s*\(\s*[ur]?["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _parse_step_file(filepath: str) -> Optional[list]:
    """Extract step definitions from a Python step file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    steps = []
    for match in _STEP_RE.finditer(content):
        steps.append({
            "type": match.group(1).lower(),
            "pattern": match.group(2),
            "file": filepath,
            "line": content[: match.start()].count("\n") + 1,
        })
    return steps or None


def list_steps(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths. Steps are discovered in 'steps/' subdirectories. Defaults to BEHAVEX_FEATURES_PATH env var. Narrow this when the full suite times out.",
    ] = None,
) -> dict:
    """List all step definitions found in the test suite's steps/ directories.

    Results are mtime-cached — repeated calls are near-instant for unchanged files.
    Returns partial results with a warning if scanning exceeds the time limit.

    Returns a dict with:
    - steps: list of {type, pattern, file, line}, sorted by file then line
    - total_steps: int
    - partial: true if the scan was cut short by the time limit
    - warning: explanation when partial=true
    """
    resolved_paths = paths or default_paths()
    step_files = sorted(discover_step_files(resolved_paths))

    file_results, partial, warning = scan_files(step_files, _parse_step_file)

    steps = [step for file_steps in file_results for step in file_steps]
    steps.sort(key=lambda s: (s["file"], s["line"]))

    out = {"steps": steps, "total_steps": len(steps), "partial": partial}
    if warning:
        out["warning"] = warning
    return out
