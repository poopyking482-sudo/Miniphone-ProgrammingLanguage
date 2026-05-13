#!/usr/bin/env python3
"""MiniPhone alias entrypoint for the Miniphone interpreter."""

from MiniPhone import run_mp, repl
import sys

if __name__ == "__main__":
    if len(sys.argv) == 2:
        run_mp(sys.argv[1])
    else:
        repl()
