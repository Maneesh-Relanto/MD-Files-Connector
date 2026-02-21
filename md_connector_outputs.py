#!/usr/bin/env python3
"""
md_connector_outputs.py
-----------------------
Companion script used by the GitHub Action to emit
structured outputs (total, linked, isolated, coverage)
to $GITHUB_OUTPUT. Kept separate so the main script
stays clean and human-readable.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from md_connector import (
    find_all_md_files,
    find_all_readmes,
    classify_files,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build"],
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_md = find_all_md_files(root, args.exclude)
    all_readmes = find_all_readmes(all_md)
    root_readme = next((rp for rp in all_readmes if rp.parent.resolve() == root.resolve()), None)

    linked, isolated, _ = classify_files(all_md, root_readme, root)

    # Count consistent with main(): exclude only the root README, not all READMEs
    total = len(all_md) - (1 if root_readme else 0)
    coverage = (len(linked) / total * 100) if total > 0 else 0

    print(f"total={total}")
    print(f"linked={len(linked)}")
    print(f"isolated={len(isolated)}")
    print(f"coverage={coverage:.1f}")
    print(f"readmes={len(all_readmes)}")


if __name__ == "__main__":
    main()
