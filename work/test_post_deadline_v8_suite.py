"""Validate the post-deadline v8 candidate suite and evidence invariants."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_deadline_v8_candidates"
V8_SHA256 = "e72b0bf1f27e507c7e2bc8f350625f0d923e84ced87740ddcc027c7b874b7adb"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_ids(candidate: pd.DataFrame, baseline: pd.DataFrame) -> set[int]:
    return set(candidate.loc[candidate["label"].ne(baseline["label"]), "Id"])


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v8_scored_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V8_SHA256
    assert int(baseline["label"].sum()) == 2_810

    expected = {
        "submission_v9_pareto_confirmed.csv": ({1_145, 9_816}, 2_812),
        "submission_v10_pareto_plus_exact_twin.csv": ({1_145, 5_244, 9_816}, 2_813),
        "submission_v11_pareto_plus_payload150.csv": (
            {1_145, 5_244, 5_516, 9_816},
            2_814,
        ),
    }
    for filename, (ids, positive_count) in expected.items():
        candidate = pd.read_csv(CANDIDATES / filename)
        assert list(candidate.columns) == ["Id", "label"]
        assert len(candidate) == len(test) == 10_000
        assert candidate["Id"].equals(test["Id"])
        assert candidate["Id"].is_unique
        assert set(candidate["label"].unique()) <= {0, 1}
        assert not candidate["label"].isna().any()
        assert changed_ids(candidate, baseline) == ids
        assert int(candidate["label"].sum()) == positive_count
        assert int(candidate.loc[candidate["Id"].eq(4_456), "label"].iloc[0]) == 1

    test_features = test.drop(columns="Id")
    twin_rows = test.loc[test["Id"].isin([1_145, 5_244])]
    assert len(twin_rows) == 2
    assert twin_rows.drop(columns="Id").nunique(dropna=False).max() == 1
    assert test_features.shape[1] == 22

    manifest = pd.read_csv(OUTPUTS / "post_deadline_v8_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2, 3]
    assert manifest.iloc[0]["filename"] == "submission_v10_pareto_plus_exact_twin.csv"
    assert manifest.iloc[0]["role"] == "PRIMARY_RECOMMENDATION"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_deadline_v8_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54809564, 54809544, 54808754, 54794527, 54808193]
    assert scores["public_f1"].tolist() == [0.96267, 0.96304, 0.96193, 0.96230, 0.96267]
    assert scores["private_f1"].tolist() == [0.97232, 0.97232, 0.97232, 0.97198, 0.97198]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_deadline_v8_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    zip_path = OUTPUTS / "superai6_post_deadline_v8_bundle.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print("exact_twin_ids=1145,5244")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")
    print(f"bundle_sha256={digest(zip_path)}")


if __name__ == "__main__":
    main()
