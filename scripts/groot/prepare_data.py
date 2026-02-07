#!/usr/bin/env python3
"""Prepare a LeRobot dataset for GR00T N1.6 fine-tuning.

Adds modality.json and validates the dataset format.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# SO-ARM100 dual-camera modality configuration for GR00T N1.6.
SO100_DUALCAM_MODALITY = {
    "state": {
        "joint_positions": {
            "start": 0,
            "end": 6,
            "semantic": "joint_position",
        },
        "gripper_position": {
            "start": 6,
            "end": 7,
            "semantic": "gripper_position",
        },
    },
    "action": {
        "joint_positions": {
            "start": 0,
            "end": 6,
            "semantic": "joint_position",
        },
        "gripper_position": {
            "start": 6,
            "end": 7,
            "semantic": "gripper_position",
        },
    },
}


def validate_dataset(dataset_dir: Path) -> list[str]:
    """Return a list of validation warnings (empty = OK)."""
    warnings: list[str] = []

    meta_dir = dataset_dir / "meta"
    if not meta_dir.exists():
        warnings.append(f"Missing meta/ directory at {meta_dir}")
        return warnings

    for required in ("info.json", "episodes.jsonl", "tasks.jsonl"):
        if not (meta_dir / required).exists():
            warnings.append(f"Missing {required} in meta/")

    data_dir = dataset_dir / "data"
    if not data_dir.exists():
        warnings.append("Missing data/ directory")
    else:
        parquets = list(data_dir.rglob("*.parquet"))
        if not parquets:
            warnings.append("No .parquet files found in data/")

    videos_dir = dataset_dir / "videos"
    if videos_dir.exists():
        mp4s = list(videos_dir.rglob("*.mp4"))
        if not mp4s:
            warnings.append("videos/ directory exists but contains no .mp4 files")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, help="Path to LeRobot dataset")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    if not dataset_dir.exists():
        print(f"ERROR: dataset directory does not exist: {dataset_dir}", file=sys.stderr)
        return 1

    print(f"Preparing dataset: {dataset_dir}")

    # Validate structure.
    warnings = validate_dataset(dataset_dir)
    for w in warnings:
        print(f"  WARNING: {w}")

    # Write modality.json.
    meta_dir = dataset_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    modality_path = meta_dir / "modality.json"

    with open(modality_path, "w") as fh:
        json.dump(SO100_DUALCAM_MODALITY, fh, indent=2)
    print(f"  Created {modality_path}")

    if not warnings:
        print("\nDataset is ready for GR00T fine-tuning!")
    else:
        print(f"\nDataset has {len(warnings)} warning(s) — review above.")

    print(f"\nNext step:")
    print(f"  ./scripts/groot/finetune.sh {dataset_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
