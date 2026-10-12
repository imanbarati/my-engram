#!/usr/bin/env python3
"""
check_secrets.py - scan the repo for passwords, API keys, private keys, and card-like numbers.

  python scripts/check_secrets.py            # scan everything (except .git, index/)
  python scripts/check_secrets.py --staged   # scan only files staged for commit (used by the git hook)
  python scripts/check_secrets.py path ...   # scan specific files or folders

Prints file:line and the KIND of match, never the secret itself. Add "secrets-ok" to a line to skip it. Exit code 1 if anything is found.
This is a safety net, not a guarantee: still read what you commit.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from common import ROOT, SECRET_PATTERNS
import re

SKIP_DIRS = {".git", "index", "__pycache__", "node_modules"}
MAX_BYTES = 2_000_000


def iter_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not (set(f.relative_to(p).parts) & SKIP_DIRS):
                    yield f


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / line for line in out.splitlines() if line.strip()]


def scan(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return []
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []  # binary or unreadable: skip
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if "secrets-ok" in line:
            continue  # deliberate test data / false positive
        for name, pat in SECRET_PATTERNS.items():
            if re.search(pat, line):
                hits.append((n, name))
    return hits


def main():
    ap = argparse.ArgumentParser(description="Scan for secrets before committing.")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()

    if args.staged:
        files = staged_files()
    else:
        files = list(iter_files(args.paths or [ROOT]))

    found = 0
    for f in files:
        for n, name in scan(f):
            try:
                shown = f.resolve().relative_to(ROOT)
            except ValueError:
                shown = f
            print(f"{shown}:{n}: possible {name}")
            found += 1

    if found:
        print(f"\n{found} possible secret(s) found. Remove or redact them before committing.")
        sys.exit(1)
    print("No secrets found.")


if __name__ == "__main__":
    main()
