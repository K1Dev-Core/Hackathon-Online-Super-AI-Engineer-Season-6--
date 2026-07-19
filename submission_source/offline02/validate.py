"""Validate a generated submission against the test Id order and schema."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--submission", required=True, type=Path)
    args = parser.parse_args()

    test = pd.read_csv(args.test, usecols=["Id"])
    submission = pd.read_csv(args.submission)

    if list(submission.columns) != ["Id", "label"]:
        raise ValueError(f"Expected columns ['Id', 'label'], got {list(submission.columns)}")
    if len(submission) != len(test):
        raise ValueError(f"Expected {len(test)} rows, got {len(submission)}")
    if not submission["Id"].equals(test["Id"]):
        raise ValueError("Submission Id order does not match test Id order")
    if submission["label"].isna().any():
        raise ValueError("Submission contains missing labels")
    if not set(submission["label"].unique()) <= {0, 1}:
        raise ValueError("Labels must be 0 or 1")

    print("VALID")
    print(f"rows={len(submission)}")
    print(f"positive_labels={int(submission['label'].sum())}")


if __name__ == "__main__":
    main()
