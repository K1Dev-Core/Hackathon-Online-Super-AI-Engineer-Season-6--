"""Validate refined candidates after v20 score audit."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_v20_refined_candidates"
V16_SHA256 = "a1a58ab8547655d0fff22a07cedd8a2f93a0ee6edb92297f5cae3404fca42702"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v16_confirmed_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V16_SHA256
    assert int(baseline["label"].sum()) == 2_821

    expected = {
        "submission_v21_high_context.csv": ({592, 1_223, 4_394, 5_177, 5_850, 6_644, 7_235, 8_362, 8_832, 9_757}, 2_831),
        "submission_v22_high_novelty_4082.csv": ({4_082}, 2_822),
        "submission_v23_context_plus_novelty.csv": ({592, 1_223, 4_082, 4_394, 5_177, 5_850, 6_644, 7_235, 8_362, 8_832, 9_757}, 2_832),
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
        for confirmed_id in [4456, 5516, 6011, 4057, 4933, 1980, 5475, 1805, 55]:
            assert int(candidate.loc[candidate["Id"].eq(confirmed_id), "label"].iloc[0]) == 1

    manifest = pd.read_csv(OUTPUTS / "post_v20_refined_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2, 3]
    assert manifest.iloc[0]["filename"] == "submission_v21_high_context.csv"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_v20_refined_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54809954, 54809890]
    assert scores["public_f1"].tolist() == [0.96461, 0.96414]
    assert scores["private_f1"].tolist() == [0.97412, 0.97403]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_v20_refined_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    with zipfile.ZipFile(OUTPUTS / "superai6_post_v20_refined_bundle.zip") as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")


if __name__ == "__main__":
    main()
