"""Validate stream-threshold probes built from v27."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_v27_threshold_candidates"
V27_SHA256 = "6cca99ca5f6147f6d4865e87908a5fd88313faf2bf596d56f8eb1972a1ac0d02"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v27_confirmed_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V27_SHA256
    assert int(baseline["label"].sum()) == 2_854

    ids_085 = {790, 975, 997, 1_893, 3_740, 4_891, 5_944, 6_765, 7_641, 8_364, 8_671, 9_504, 9_977}
    ids_080 = ids_085 | {1_269, 2_135, 2_372, 2_483, 2_787, 5_370, 8_739, 8_831, 9_148, 9_677}
    expected = {
        "submission_v30_stream_fraction_085.csv": (ids_085, 2_867),
        "submission_v31_stream_fraction_080.csv": (ids_080, 2_877),
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

    manifest = pd.read_csv(OUTPUTS / "post_v27_threshold_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2]
    assert manifest.iloc[0]["filename"] == "submission_v30_stream_fraction_085.csv"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_v27_threshold_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54810185, 54810175, 54810114]
    assert scores["public_f1"].tolist() == [0.96824, 0.96348, 0.96749]
    assert scores["private_f1"].tolist() == [0.97748, 0.97329, 0.97611]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_v27_threshold_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    with zipfile.ZipFile(OUTPUTS / "superai6_post_v27_threshold_bundle.zip") as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")


if __name__ == "__main__":
    main()
