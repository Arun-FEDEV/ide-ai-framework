#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "project"


def copy_tree(src: Path, dst: Path, *, dry_run: bool, force: bool) -> list[str]:
    actions: list[str] = []
    for path in sorted(src.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not force:
            actions.append(f"skip existing {target}")
            continue
        actions.append(f"copy {rel} -> {target}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Install IDE AI Framework into a project workspace.")
    parser.add_argument("--target", required=True, help="Project workspace path")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing installed files")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"target does not exist: {target}")
    if not target.is_dir():
        raise SystemExit(f"target is not a directory: {target}")

    actions = copy_tree(TEMPLATE, target, dry_run=args.dry_run, force=args.force)
    for action in actions:
        print(action)
    if args.dry_run:
        print("dry run complete")
    else:
        print(f"installed IDE AI Framework into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
