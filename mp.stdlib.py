"""
mp.stdlib.py — Miniphone 1.2 Standard Library
Author:    KielSir
AI Assist: Claude (Anthropic)

Exposes Python's os, sys, time, shutil, math, json, and random modules to the MP interpreter
under the std/ namespace. Import in your script with:

    #import std/os
    #import std/sys
    #import std/time
    #import std/files
    #import std/math
    #import std/json
    #import std/random

All callables bind directly to the underlying CPython C-implemented
functions where possible, avoiding Python-level wrapper overhead.
"""

import os as _os
import sys as _sys
import time as _time
import platform as _plt
import shutil as _sh
import math as _math
import json as _json
import random as _random

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
#  std/math
# ─────────────────────────────────────────────
STD_MATH: dict = {
    # ── Trig ──────────────────────────────────
    "sin":      _math.sin,
    "cos":      _math.cos,
    "tan":      _math.tan,
    "asin":     _math.asin,
    "acos":     _math.acos,
    "atan":     _math.atan,
    "atan2":    _math.atan2,
    "sinh":     _math.sinh,
    "cosh":     _math.cosh,
    "tanh":     _math.tanh,
    "degrees":  _math.degrees,
    "radians":  _math.radians,
    # ── Rounding ──────────────────────────────
    "round":    round,
    "floor":    _math.floor,
    "ceil":     _math.ceil,
    "trunc":    _math.trunc,
    # ── Clamp ─────────────────────────────────
    "clamp":    lambda x, lo, hi: lo if x < lo else (hi if x > hi else x),
    # ── Roots / Power ─────────────────────────
    "sqrt":     _math.sqrt,
    "cbrt":     _math.cbrt,
    "pow":      _math.pow,
    "exp":      _math.exp,
    "exp2":     _math.exp2,
    # ── Logarithms ────────────────────────────
    "log":      _math.log,
    "log2":     _math.log2,
    "log10":    _math.log10,
    # ── Misc ──────────────────────────────────
    "abs":      abs,
    "fabs":     _math.fabs,
    "gcd":      _math.gcd,
    "lcm":      _math.lcm,
    "factorial": _math.factorial,
    "isnan":    _math.isnan,
    "isinf":    _math.isinf,
    "copysign": _math.copysign,
    "hypot":    _math.hypot,
    "dist":     _math.dist,
    # ── Constants ─────────────────────────────
    "PI":       _math.pi,
    "E":        _math.e,
    "TAU":      _math.tau,
    "INF":      _math.inf,
    "NAN":      _math.nan,
}

# ─────────────────────────────────────────────
#  std/json
# ─────────────────────────────────────────────

def _json_parse(text: str):
    """Parse a JSON string → Python object."""
    return _json.loads(text)


def _json_stringify(obj, *, indent=None) -> str:
    """Serialize a Python object → JSON string."""
    return _json.dumps(obj, indent=indent)


def _json_load(path: str):
    """Read a JSON file from disk → Python object."""
    with open(path, "r", encoding="utf-8") as _f:
        return _json.load(_f)


def _json_save(obj, path: str, *, indent=2) -> None:
    """Write a Python object → JSON file on disk."""
    with open(path, "w", encoding="utf-8") as _f:
        _json.dump(obj, _f, indent=indent)


def _json_keys(obj) -> list:
    """Return the keys of a JSON object (dict)."""
    if not isinstance(obj, dict):
        raise TypeError("json.keys() requires a JSON object (dict)")
    return list(obj.keys())


def _json_get(obj, key, default=None):
    """Safely get a value from a JSON object by key."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    raise TypeError("json.get() requires a JSON object (dict)")

STD_JSON: dict = {
    "parse":     _json_parse,
    "stringify": _json_stringify,
    "load":      _json_load,
    "save":      _json_save,
    "keys":      _json_keys,
    "get":       _json_get,
}

# ─────────────────────────────────────────────
#  std/random
# ─────────────────────────────────────────────
# Bind directly to the shared Random instance methods (C-level Mersenne Twister).
_rng = _random.Random()   # isolated instance — doesn't pollute global state

STD_RANDOM: dict = {
    "rand":      _rng.random,
    "randint":   _rng.randint,
    "randfloat": _rng.uniform,
    "randrange": _rng.randrange,
    "choice":    _rng.choice,
    "choices":   _rng.choices,
    "sample":    _rng.sample,
    "shuffle":   _rng.shuffle,
    "gauss":     _rng.gauss,
    "normalvariate": _rng.normalvariate,
    "expovariate":   _rng.expovariate,
    "triangular":    _rng.triangular,
    "seed":      _rng.seed,
    "getstate":  _rng.getstate,
    "setstate":  _rng.setstate,
}

# ─────────────────────────────────────────────
#  Registry — maps "std/X" module names to dicts
# ─────────────────────────────────────────────
_STD_REGISTRY: dict[str, dict] = {
    "std/os": STD_OS,
    "std/sys": STD_SYS,
    "std/time": STD_TIME,
    "std/files": STD_FILES,
    "std/math": STD_MATH,
    "std/json": STD_JSON,
    "std/random": STD_RANDOM,
}


def load_std_module(name: str) -> dict | None:
    """Called by the MP interpreter when it encounters '#import std/X'."""
    return _STD_REGISTRY.get(name)


def patch_interpreter(modules_dict: dict) -> None:
    """Drop-in patch for a Miniphone interpreter module registry."""
    modules_dict.update(_STD_REGISTRY)
