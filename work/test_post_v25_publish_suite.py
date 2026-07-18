"""Validate high-positive-stream payload candidates."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_v25_publish_candidates"
V25_SHA256 = "e01a93fc5e28f093bd91a39dd6a9f384151d618c632b58396cbd987fb2626655"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v25_confirmed_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V25_SHA256
    assert int(baseline["label"].sum()) == 2_844

    stream3_5 = {7, 1_342, 1_958, 4_799, 7_998, 8_480, 9_453, 1_655, 3_255, 8_258}
    all_payload = {1_893, 8_671, 8_364, 6_765, 7_641, 4_891, 9_504, 790, 5_944, 3_740, 997, 9_977, 975, 2_483, 2_372, 5_370, 2_787, 8_831, 8_739, 9_148, 9_677, 2_135, 1_269, 1_655, 3_255, 8_258, 5_069, 641, 7, 1_342, 1_958, 4_799, 7_998, 8_480, 9_453, 9_260, 9_439}
    expected = {
        "submission_v27_stream3_5_payload.csv": (stream3_5, 2_854),
        "submission_v28_publish_payload_cluster.csv": (all_payload - stream3_5, 2_871),
        "submission_v29_all_high_fraction_payload.csv": (all_payload, 2_881),
    }
    for filename, (ids, positives) in expected.items():
        candidate = pd.read_csv(CANDIDATES / filename)
        assert list(candidate.columns) == ["Id", "label"]
        assert len(candidate) == len(test) == 10_000
        assert candidate["Id"].equals(test["Id"])
        assert candidate["Id"].is_unique
        assert set(candidate["label"].unique()) <= {0, 1}
        assert not candidate["label"].isna().any()
        changed = set(candidate.loc[candidate["label"].ne(baseline["label"]), "Id"])
        assert changed == ids
        assert int(candidate["label"].sum()) == positives
        assert int(candidate.loc[candidate["Id"].eq(4_550), "label"].iloc[0]) == 0

    manifest = pd.read_csv(OUTPUTS / "post_v25_publish_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2, 3]
    assert manifest.iloc[0]["filename"] == "submission_v27_stream3_5_payload.csv"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_v25_publish_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54810114, 54810130, 54810019]
    assert scores["public_f1"].tolist() == [0.96749, 0.96749, 0.96598]
    assert scores["private_f1"].tolist() == [0.97611, 0.97578, 0.97541]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_v25_publish_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    with zipfile.ZipFile(OUTPUTS / "superai6_post_v25_publish_bundle.zip") as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")


if __name__ == "__main__":
    main()
