#!/usr/bin/env python3
"""
One-off migration tool to unify results directory layout.
- From legacy double-layer paths (experiments/experiments/<id>/...) to unified (experiments/<id>/...)
- Safe by default: dry-run prints planned moves; use --apply to execute
- Creates backups by copying before move if --backup is set

Usage:
  python backend/scripts/migrate_results_root.py --root <RESULTS_ROOT> [--apply] [--backup]

Notes:
  - Windows-friendly (uses shutil and Path)
  - Idempotent: re-running will skip already migrated entries
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def find_double_layer(root: Path) -> list[tuple[Path, Path]]:
    legacy_base = root / "experiments" / "experiments"
    unified_base = root / "experiments"
    moves: list[tuple[Path, Path]] = []
    if not legacy_base.exists() or not legacy_base.is_dir():
        return moves
    for exp_dir in legacy_base.iterdir():
        if exp_dir.is_dir():
            target = unified_base / exp_dir.name
            if target.exists():
                # Already migrated or conflict: skip
                continue
            moves.append((exp_dir, target))
    return moves


def migrate(root: Path, apply: bool, backup: bool) -> int:
    moves = find_double_layer(root)
    if not moves:
        print("No legacy double-layer directories found.")
        return 0

    print(f"Found {len(moves)} experiment directories to migrate:")
    for src, dst in moves:
        print(f"  {src} -> {dst}")

    if not apply:
        print("Dry-run complete. Re-run with --apply to execute.")
        return len(moves)

    for src, dst in moves:
        dst_parent = dst.parent
        dst_parent.mkdir(parents=True, exist_ok=True)
        if backup:
            backup_path = src.with_name(src.name + ".backup")
            if not backup_path.exists():
                print(f"  Creating backup: {backup_path}")
                shutil.copytree(src, backup_path)
        print(f"  Moving {src} -> {dst}")
        shutil.move(str(src), str(dst))

    # Optionally remove empty legacy base if no children remain
    legacy_base = root / "experiments" / "experiments"
    try:
        if legacy_base.exists() and not any(legacy_base.iterdir()):
            legacy_base.rmdir()
            # also remove parent 'experiments' if it only contained the legacy folder and is now empty? No, keep.
    except Exception:
        pass

    print("Migration complete.")
    return len(moves)


def main():
    parser = argparse.ArgumentParser(description="Unify results directory layout")
    parser.add_argument("--root", required=True, help="RESULTS_ROOT (absolute or relative)")
    parser.add_argument("--apply", action="store_true", help="Execute migration (default: dry-run)")
    parser.add_argument("--backup", action="store_true", help="Backup each experiment directory before moving")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root does not exist: {root}")
        raise SystemExit(2)

    migrate(root, apply=args.apply, backup=args.backup)


if __name__ == "__main__":
    main()

