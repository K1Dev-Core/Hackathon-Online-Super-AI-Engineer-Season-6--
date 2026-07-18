"""Validate aggressive post-v11 candidate artifacts."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "post_v11_aggressive_candidates"
V11_SHA256 = "e83ea2ee73e8dcfdcd03dda4b5c95574fa8a5a87be3d243a4f441b41b5dd13cf"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    baseline_path = CANDIDATES / "submission_v11_confirmed_baseline.csv"
    baseline = pd.read_csv(baseline_path)
    assert digest(baseline_path) == V11_SHA256
    assert int(baseline["label"].sum()) == 2_814

    expected = {
        "submission_v12_plus_rare_ack.csv": ({6_011}, 2_815),
        "submission_v13_plus_stream5_ack.csv": ({4_057}, 2_815),
        "submission_v14_plus_dual_ack.csv": ({4_057, 6_011}, 2_816),
        "submission_v15_plus_stream2_ack_cluster.csv": ({1_223, 5_177, 5_850, 6_011, 9_757}, 2_819),
        "submission_v16_plus_residual_top7.csv": ({55, 1_805, 1_980, 4_057, 4_933, 5_475, 6_011}, 2_821),
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
        for confirmed_id in [4456, 1145, 5244, 5516, 9816]:
            assert int(candidate.loc[candidate["Id"].eq(confirmed_id), "label"].iloc[0]) == 1

    manifest = pd.read_csv(OUTPUTS / "post_v11_aggressive_manifest.csv")
    assert manifest["rank"].tolist() == [1, 2, 3, 4, 5]
    assert manifest.iloc[0]["filename"] == "submission_v12_plus_rare_ack.csv"
    for row in manifest.itertuples(index=False):
        assert digest(CANDIDATES / row.filename) == row.sha256

    scores = pd.read_csv(OUTPUTS / "post_v11_aggressive_observed_scores.csv")
    assert scores["kaggle_ref"].tolist() == [54809776, 54809544]
    assert scores["public_f1"].tolist() == [0.96304, 0.96304]
    assert scores["private_f1"].tolist() == [0.97266, 0.97232]

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "post_v11_aggressive_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    with zipfile.ZipFile(OUTPUTS / "superai6_post_v11_aggressive_bundle.zip") as archive:
        names = set(archive.namelist())
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(expected)}")
    print(f"primary_sha256={digest(CANDIDATES / manifest.iloc[0]['filename'])}")


if __name__ == "__main__":
    main()
