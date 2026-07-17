"""Validate every generated submission candidate and the ranked bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "submission_candidates"
EXPECTED_COUNTS = {
    "submission_candidate_00_structural_challenger.csv": 2_810,
    "submission_candidate_01_champion.csv": 2_809,
    "submission_candidate_02_lb_robust.csv": 2_805,
    "submission_candidate_03_lb_conservative.csv": 2_799,
    "submission_candidate_04_precision_floor.csv": 2_794,
    "submission_candidate_05_micro_payload_hedge.csv": 2_812,
    "submission_candidate_06_capture_context_hedge.csv": 2_849,
    "submission_candidate_07_pu_top64_hedge.csv": 2_873,
    "submission_candidate_08_target3000_aggressive.csv": 3_000,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model() -> object:
    path = OUTPUTS / "predict_final_model.py"
    spec = importlib.util.spec_from_file_location("predict_final_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import predictor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    train = pd.read_csv(ROOT / "data" / "X_train.csv", low_memory=False)
    test = pd.read_csv(ROOT / "data" / "X_test.csv", low_memory=False)
    champion_source = pd.read_csv(OUTPUTS / "submission_rank1_best_publish_complete.csv")
    champion = pd.read_csv(CANDIDATES / "submission_candidate_01_champion.csv")
    structural = pd.read_csv(CANDIDATES / "submission_candidate_00_structural_challenger.csv")

    assert champion.equals(champion_source)
    rebuilt = load_model().build_submission(train, test)
    assert rebuilt["Id"].equals(champion["Id"])
    assert rebuilt["label"].astype("int8").equals(champion["label"].astype("int8"))
    assert structural.equals(pd.read_csv(OUTPUTS / "submission_rank1_structural_plus1.csv"))
    structural_additions = structural["label"].eq(1) & champion["label"].eq(0)
    assert structural.loc[structural_additions, "Id"].tolist() == [9_816]

    syn_capture = (
        test["tcp.window_size"].eq(512) & test["tcp.flags.syn"].eq(1)
    ) | (
        test["frame.len"].eq(58)
        & test["tcp.window_size"].eq(65_392)
        & test["tcp.flags.syn"].eq(1)
        & test["tcp.flags.ack"].eq(1)
    )
    assert int(syn_capture.sum()) == 599
    assert set(range(600)) - set(test.loc[syn_capture, "tcp.stream"]) == {194}

    submissions: dict[str, pd.DataFrame] = {}
    for filename, expected_count in EXPECTED_COUNTS.items():
        submission = pd.read_csv(CANDIDATES / filename)
        assert list(submission.columns) == ["Id", "label"]
        assert len(submission) == len(test) == 10_000
        assert submission["Id"].equals(test["Id"])
        assert submission["Id"].is_unique
        assert not submission["label"].isna().any()
        assert set(submission["label"].unique()) <= {0, 1}
        assert int(submission["label"].sum()) == expected_count
        submissions[filename] = submission

    micro = submissions["submission_candidate_05_micro_payload_hedge.csv"]
    micro_additions = micro["label"].eq(1) & champion["label"].eq(0)
    assert set(micro.loc[micro_additions, "Id"]) == {1_145, 5_244, 5_516}

    context = submissions["submission_candidate_06_capture_context_hedge.csv"]
    context_additions = context["label"].eq(1) & champion["label"].eq(0)
    assert int(context_additions.sum()) == 40
    assert set(micro.loc[micro_additions, "Id"]) <= set(context.loc[context_additions, "Id"])

    pu64 = submissions["submission_candidate_07_pu_top64_hedge.csv"]
    target = submissions["submission_candidate_08_target3000_aggressive.csv"]
    pu_additions = set(pu64.loc[pu64["label"].eq(1) & champion["label"].eq(0), "Id"])
    target_additions = set(target.loc[target["label"].eq(1) & champion["label"].eq(0), "Id"])
    assert len(pu_additions) == 64
    assert len(target_additions) == 191
    assert pu_additions <= target_additions

    manifest = pd.read_csv(OUTPUTS / "candidate_manifest.csv")
    assert manifest["rank"].tolist() == list(range(1, 10))
    assert manifest.loc[manifest["recommended"].eq("YES"), "rank"].tolist() == [1]
    assert manifest["positive_labels"].tolist() == list(EXPECTED_COUNTS.values())
    champion_row = manifest.loc[manifest["filename"].eq("submission_candidate_01_champion.csv")]
    assert champion_row["actual_public_f1"].iloc[0] == 0.96193

    checksums: dict[str, str] = {}
    for line in (OUTPUTS / "candidate_suite_checksums.sha256").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        checksums[relative] = checksum
        assert digest(OUTPUTS / relative) == checksum

    zip_path = OUTPUTS / "superai6_candidate_suite_ranked.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "submission_candidates/submission_candidate_00_structural_challenger.csv" in names
        assert "submission_rank1_structural_plus1.csv" in names
        assert "submission_candidates/submission_candidate_01_champion.csv" in names
        assert "candidate_manifest.csv" in names
        assert "candidate_suite_checksums.sha256" in names
        for relative, checksum in checksums.items():
            assert relative in names
            assert hashlib.sha256(archive.read(relative)).hexdigest() == checksum

    print(f"validated_candidates={len(submissions)}")
    print(f"champion_sha256={digest(CANDIDATES / 'submission_candidate_01_champion.csv')}")
    print(f"bundle_sha256={digest(zip_path)}")


if __name__ == "__main__":
    main()
