# -*- coding: utf-8 -*-
from __future__ import annotations

import glob
import os
import re
from typing import Annotated, List, Optional

from mcp_behavex.tools._utils import default_paths

# Matches @given/@when/@then/@step with a single- or double-quoted string pattern.
# Handles optional u/r prefix (e.g. u"pattern").
_STEP_RE = re.compile(
    r'@(given|when|then|step)\s*\(\s*[ur]?["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def list_steps(
    paths: Annotated[
        Optional[List[str]],
        "Feature file or directory paths. Steps are discovered in 'steps/' subdirectories. Defaults to BEHAVEX_FEATURES_PATH env var.",
    ] = None,
) -> dict:
    """List all step definitions found in the test suite's steps/ directories.

    Returns a dict with:
    - steps: list of {type, pattern, file, line}, sorted by file then line
    - total_steps: int
    """
    resolved_paths = paths or default_paths()
    step_files = _find_step_files(resolved_paths)

    steps = []
    for filepath in sorted(step_files):
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        lines = content.splitlines()
        for match in _STEP_RE.finditer(content):
            line_number = content[: match.start()].count("\n") + 1
            steps.append({
                "type": match.group(1).lower(),
                "pattern": match.group(2),
                "file": filepath,
                "line": line_number,
            })

    steps.sort(key=lambda s: (s["file"], s["line"]))

    return {
        "steps": steps,
        "total_steps": len(steps),
    }


def _find_step_files(paths: List[str]) -> List[str]:
    files: List[str] = []
    for path in paths:
        if os.path.isfile(path):
            parent = os.path.dirname(path)
            files.extend(glob.glob(os.path.join(parent, "steps", "*.py")))
        elif os.path.isdir(path):
            files.extend(glob.glob(os.path.join(path, "**/steps/*.py"), recursive=True))
    return list(dict.fromkeys(files))
