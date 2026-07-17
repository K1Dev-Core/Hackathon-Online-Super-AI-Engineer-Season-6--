"""Validate offline benchmark submissions, rankings, checksums, and bundle."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "offline_benchmark_candidates"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    champion = pd.read_csv(OUTPUTS / "submission_rank1_best_publish_complete.csv")
    files = sorted(CANDIDATES.glob("*.csv"))
    assert len(files) == 11

    additions: dict[str, set[int]] = {}
    for path in files:
        submission = pd.read_csv(path)
        assert list(submission.columns) == ["Id", "label"]
        assert len(submission) == len(test) == 10_000
        assert submission["Id"].equals(test["Id"])
        assert submission["Id"].is_unique
        assert not submission["label"].isna().any()
        assert set(submission["label"].unique()) <= {0, 1}
        mask = submission["label"].eq(1) & champion["label"].eq(0)
        additions[path.name] = set(submission.loc[mask, "Id"].astype(int))

    scoremax = "submission_offline_01_scoremax_structural.csv"
    assert additions[scoremax] == {9_816}
    assert additions["submission_offline_02_hedge_payload132.csv"] == {1_145, 9_816}
    assert additions["submission_offline_03_hedge_payload150.csv"] == {5_516, 9_816}
    assert additions["submission_offline_04_hedge_rare_ack.csv"] == {6_011, 9_816}
    assert additions["submission_offline_05_hedge_stream5_ack.csv"] == {4_057, 9_816}
    assert len(additions["submission_offline_10_target3000.csv"]) == 191

    results = pd.read_csv(OUTPUTS / "offline_benchmark_results.csv")
    winners = pd.read_csv(OUTPUTS / "offline_benchmark_winners.csv")
    assert results["offline_rank"].tolist() == list(range(1, 12))
    assert results.iloc[0]["filename"] == scoremax
    assert results.iloc[0]["verdict"] == "SCORE_MAX_WINNER"
    assert set(winners["verdict"]) <= {"SCORE_MAX_WINNER", "CHAMPION_BEATING_BACKUP"}
    assert scoremax in set(winners["filename"])
    assert (winners["offline_mean_f1"] > results.loc[results["verdict"].eq("CONTROL"), "offline_mean_f1"].iloc[0]).all()
    assert results.iloc[0]["public_delta_proxy"] > 0.96193

    sensitivity = pd.read_csv(OUTPUTS / "offline_benchmark_sensitivity.csv")
    assert len(sensitivity) == 90
    scoremax_stress = sensitivity.loc[sensitivity["filename"].eq(scoremax)]
    assert len(scoremax_stress) == 15
    assert scoremax_stress["beats_champion"].all()
    assert (scoremax_stress["nonstructural_additions_assumed_true"] == 0).all()

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "offline_benchmark_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    zip_path = OUTPUTS / "superai6_offline_benchmark_bundle.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "offline_benchmark_results.csv" in names
        assert "offline_benchmark_winners.csv" in names
        assert "offline_benchmark_sensitivity.csv" in names
        assert "offline_benchmark_report.md" in names
        assert f"offline_benchmark_candidates/{scoremax}" in names
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_offline_candidates={len(files)}")
    print(f"winner_files={len(winners)}")
    print(f"scoremax_sha256={digest(CANDIDATES / scoremax)}")
    print(f"bundle_sha256={digest(zip_path)}")


if __name__ == "__main__":
    main()
