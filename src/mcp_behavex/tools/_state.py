# -*- coding: utf-8 -*-
"""Shared mutable state for the mcp-behavex server process.

Keeping this in one place lets run_tests and stop_run coordinate without
circular imports. All fields are module-level so mutations are visible
across the process.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from behavex import BehaveXRunner

execution_lock = threading.Lock()
stop_event = threading.Event()
active_run_id: Optional[str] = None
active_runner: Optional["BehaveXRunner"] = None
