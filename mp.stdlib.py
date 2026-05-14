"""
mp.stdlib.py — Miniphone 1.2 Standard Library
Author:    KielSir
AI Assist: Claude (Anthropic)

Exposes Python's os, sys, time, and shutil modules to the MP interpreter
under the std/ namespace. Import in your script with:

    #import std/os
    #import std/sys
    #import std/time
    #import std/files

All callables bind directly to the underlying CPython C-implemented
functions where possible, avoiding Python-level wrapper overhead.
"""

import os as _os
import sys as _sys
import time as _time
import platform as _plt
import shutil as _sh

# ─────────────────────────────────────────────
#  std/os
# ─────────────────────────────────────────────
STD_OS: dict = {
    "mkdir": _os.mkdir,
    "rm": _os.remove,
    "rename": _os.rename,
    "path": _os.path.exists,
    "env": _os.environ.get
}

# ─────────────────────────────────────────────
#  std/sys
# ─────────────────────────────────────────────
STD_SYS: dict = {
    "args": _sys.argv,
    "version": _sys.version,
    "platform": _sys.platform,
    "exit": _sys.exit
}

# ─────────────────────────────────────────────
#  std/time
# ─────────────────────────────────────────────
STD_TIME: dict = {
    "sleep": _time.sleep,
    "now": _time.time,
    "stamp": _time.ctime
}

# ─────────────────────────────────────────────
#  std/files
# ─────────────────────────────────────────────
STD_FILES: dict = {
    "copy": _sh.copy,
    "move": _sh.move,
    "disk": _sh.disk_usage
}

# ─────────────────────────────────────────────
#  Registry — maps "std/X" module names to dicts
# ─────────────────────────────────────────────
_STD_REGISTRY: dict[str, dict] = {
    "std/os": STD_OS,
    "std/sys": STD_SYS,
    "std/time": STD_TIME,
    "std/files": STD_FILES,
}


def load_std_module(name: str) -> dict | None:
    """Called by the MP interpreter when it encounters '#import std/X'."""
    return _STD_REGISTRY.get(name)


def patch_interpreter(modules_dict: dict) -> None:
    """Drop-in patch for a Miniphone interpreter module registry."""
    modules_dict.update(_STD_REGISTRY)
