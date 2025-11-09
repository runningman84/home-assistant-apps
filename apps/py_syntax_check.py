#!/usr/bin/env python3
"""Syntax check staged or provided Python files.

This script is intended to be executed by pre-commit inside its venv so
dependencies (python) are the venv's interpreter and no system-wide tools
are required.
"""
import sys
import subprocess
from pathlib import Path


def get_staged_py_files():
    # get staged python files
    try:
        out = subprocess.check_output([
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACM",
        ], text=True)
    except subprocess.CalledProcessError:
        return []

    files = [p for p in out.splitlines() if p.endswith('.py')]
    return files


def main():
    files = sys.argv[1:]
    if not files:
        files = get_staged_py_files()

    if not files:
        return 0

    errors = 0
    for f in files:
        p = Path(f)
        if not p.exists():
            # skip deleted files
            continue
        print(f"Checking {f}")
        try:
            # use built-in py_compile via subprocess to mirror previous behavior
            subprocess.check_call([sys.executable, "-m", "py_compile", str(p)])
        except subprocess.CalledProcessError:
            print(f"Syntax error in {f}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"Commit aborted: {errors} file(s) have syntax errors.", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
