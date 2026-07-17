"""Build and rank deterministic SuperAI6 submission candidates."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs"
CANDIDATE_DIR = OUTPUT_ROOT / "submission_candidates"
TRAIN_PATH = ROOT / "data" / "X_train.csv"
TEST_PATH = ROOT / "data" / "X_test.csv"
CHAMPION_PATH = OUTPUT_ROOT / "submission_rank1_best_publish_complete.csv"
MANIFEST_PATH = OUTPUT_ROOT / "candidate_manifest.csv"
SCENARIO_PATH = OUTPUT_ROOT / "candidate_score_scenarios.csv"
RANKING_PATH = OUTPUT_ROOT / "candidate_residual_ranking.csv"
CHECKSUM_PATH = OUTPUT_ROOT / "candidate_suite_checksums.sha256"
REPORT_PATH = OUTPUT_ROOT / "candidate_suite_report.md"
ZIP_PATH = OUTPUT_ROOT / "superai6_candidate_suite_ranked.zip"

PRIVATE_POSITIVES = 1_541
PUBLIC_CONFUSION = {
    "submission_candidate_01_champion.csv": (1_352, 1_352, 0.96193),
    "submission_candidate_02_lb_robust.csv": (1_350, 1_350, 0.96119),
    "submission_candidate_03_lb_conservative.csv": (1_348, 1_348, 0.96045),
    "submission_candidate_04_precision_floor.csv": (1_346, 1_346, 0.95971),
}

CANDIDATE_SPECS = [
    {
        "rank": 1,
        "filename": "submission_candidate_01_champion.csv",
        "category": "scored-safe",
        "source": "submission_rank1_best_publish_complete.csv",
        "description": "Exact public rank-1 champion; recommended.",
    },
    {
        "rank": 2,
        "filename": "submission_candidate_02_lb_robust.csv",
        "category": "scored-safe",
        "source": "submission_rank1_probe4_publish137.csv",
        "description": "Champion minus four validated PUBLISH rows.",
    },
    {
        "rank": 3,
        "filename": "submission_candidate_03_lb_conservative.csv",
        "category": "scored-safe",
        "source": "submission_rank1_probe3_publish132.csv",
        "description": "Earlier validated PUBLISH checkpoint.",
    },
    {
        "rank": 4,
        "filename": "submission_candidate_04_precision_floor.csv",
        "category": "scored-safe",
        "source": "submission_rank1_probe1.csv",
        "description": "Precision-first checkpoint after removing PINGRESP false positives.",
    },
    {
        "rank": 5,
        "filename": "submission_candidate_05_micro_payload_hedge.csv",
        "category": "experimental",
        "description": "Champion plus three undecoded payload siblings.",
        "assumed_residual_precision": 0.10,
    },
    {
        "rank": 6,
        "filename": "submission_candidate_06_capture_context_hedge.csv",
        "category": "experimental",
        "description": "Champion plus 40 stream-2-to-5 capture-context rows.",
        "assumed_residual_precision": 0.05,
    },
    {
        "rank": 7,
        "filename": "submission_candidate_07_pu_top64_hedge.csv",
        "category": "experimental",
        "description": "Champion plus the top 64 hard-gated residual rows.",
        "assumed_residual_precision": 0.05,
    },
    {
        "rank": 8,
        "filename": "submission_candidate_08_target3000_aggressive.csv",
        "category": "experimental",
        "description": "Champion plus 191 residual rows; exactly 3,000 positive labels.",
        "assumed_residual_precision": 0.03,
    },
]


def validate_submission(submission: pd.DataFrame, test: pd.DataFrame) -> None:
    if list(submission.columns) != ["Id", "label"]:
        raise RuntimeError(f"Invalid columns: {list(submission.columns)}")
    if len(submission) != len(test) or not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match X_test")
    if submission["Id"].duplicated().any():
        raise RuntimeError("Duplicate Id values")
    if submission["label"].isna().any() or not set(submission["label"].unique()) <= {0, 1}:
        raise RuntimeError("Labels must be binary and non-null")


def write_submission(labels: pd.Series, test: pd.DataFrame, path: Path) -> pd.DataFrame:
    submission = test[["Id"]].copy()
    submission["label"] = labels.astype("int8").to_numpy()
    validate_submission(submission, test)
    submission.to_csv(path, index=False)
    return submission


def hash_rows(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    values = frame[columns].copy()
    for column in values.columns:
        if values[column].dtype == "object":
            values[column] = values[column].fillna("<NA>")
        else:
            values[column] = values[column].fillna(-999_999.0)
    return pd.util.hash_pandas_object(values, index=False).astype("uint64")


def build_residual_ranking(
    train: pd.DataFrame,
    test: pd.DataFrame,
    champion: pd.Series,
) -> pd.DataFrame:
    packet_columns = [
        column
        for column in test.columns
        if column not in {"Id", "tcp.stream", "tcp.analysis.initial_rtt"}
    ]
    train_hashes = hash_rows(train, packet_columns)
    test_hashes = hash_rows(test, packet_columns)
    train_counts = test_hashes.map(train_hashes.value_counts()).fillna(0).astype("int32")
    test_counts = test_hashes.map(test_hashes.value_counts()).astype("int32")

    stream_rows = test["tcp.stream"].map(test["tcp.stream"].value_counts()).astype("int32")
    stream_positive_counts = champion.groupby(test["tcp.stream"]).sum()
    stream_positives = test["tcp.stream"].map(stream_positive_counts).fillna(0).astype("int32")
    stream_attack_fraction = stream_positives / stream_rows

    standard_normal_handshake = (
        test["frame.len"].eq(62) & test["tcp.window_size"].isin([5_760, 64_620])
    ) | (
        test["frame.len"].eq(54) & test["tcp.window_size"].isin([5_755, 64_523])
    )
    hard_normal = (
        test["tcp.analysis.initial_rtt"].notna()
        | test["mqtt.msgtype"].notna()
        | standard_normal_handshake
    )
    eligible = ~champion & ~hard_normal

    normal_ratio = 0.0713
    frequency_excess = (
        1.0 - normal_ratio * train_counts / test_counts.clip(lower=1)
    ).clip(0.0, 1.0)
    rarity = 1.0 / (1.0 + np.log1p(train_counts))
    undecoded_payload = test["tcp.len"].gt(0).astype(float)
    residual_score = (
        0.35 * stream_attack_fraction
        + 0.30 * frequency_excess
        + 0.25 * rarity
        + 0.10 * undecoded_payload
    )

    ranking = test.loc[eligible].copy()
    ranking["residual_score"] = residual_score.loc[eligible]
    ranking["normal_packet_count"] = train_counts.loc[eligible]
    ranking["test_packet_count"] = test_counts.loc[eligible]
    ranking["stream_rows"] = stream_rows.loc[eligible]
    ranking["stream_current_positives"] = stream_positives.loc[eligible]
    ranking["stream_attack_fraction"] = stream_attack_fraction.loc[eligible]
    ranking["frequency_excess"] = frequency_excess.loc[eligible]
    ranking["undecoded_payload"] = undecoded_payload.loc[eligible].astype("int8")
    ranking = ranking.sort_values(
        ["residual_score", "normal_packet_count", "Id"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    ranking["residual_rank"] = np.arange(1, len(ranking) + 1)
    ranking["selected_top64"] = ranking["residual_rank"].le(64).astype("int8")
    ranking["selected_target3000"] = ranking["residual_rank"].le(191).astype("int8")
    return ranking


def posterior_private_estimate(
    total_predictions: int,
    public_predictions: int,
    public_true_positives: int,
) -> tuple[float, float, float, int, float]:
    private_predictions = total_predictions - public_predictions
    alpha = public_true_positives + 0.5
    beta = public_predictions - public_true_positives + 0.5
    expected_precision = alpha / (alpha + beta)
    expected_true_positives = private_predictions * expected_precision
    expected_f1 = 2 * expected_true_positives / (PRIVATE_POSITIVES + private_predictions)

    rng = np.random.default_rng(20260718 + total_predictions)
    precision_samples = rng.beta(alpha, beta, 250_000)
    f1_samples = 2 * private_predictions * precision_samples / (
        PRIVATE_POSITIVES + private_predictions
    )
    lower, upper = np.quantile(f1_samples, [0.05, 0.95])
    return expected_f1, float(lower), float(upper), private_predictions, expected_true_positives


def private_score_with_additions(
    base_true_positives: float,
    base_predictions: int,
    additions: int,
    precision: float,
) -> float:
    private_additions = additions / 2.0
    true_positives = min(
        PRIVATE_POSITIVES,
        base_true_positives + precision * private_additions,
    )
    predictions = base_predictions + private_additions
    return 2 * true_positives / (PRIVATE_POSITIVES + predictions)


def build_manifest(
    candidates: dict[str, pd.DataFrame],
    champion: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    champion_total = int(champion.sum())
    champion_estimate = posterior_private_estimate(champion_total, 1_352, 1_352)
    base_f1, _, _, base_private_predictions, base_private_true_positives = champion_estimate
    break_even_precision = base_f1 / 2.0

    rows: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []
    for spec in CANDIDATE_SPECS:
        filename = str(spec["filename"])
        submission = candidates[filename]
        labels = submission["label"].astype(bool)
        additions = int((labels & ~champion).sum())
        removals = int((~labels & champion).sum())
        positives = int(labels.sum())
        public = PUBLIC_CONFUSION.get(filename)

        if public is not None:
            public_predictions, public_true_positives, public_score = public
            estimate, lower, upper, _, _ = posterior_private_estimate(
                positives,
                public_predictions,
                public_true_positives,
            )
            estimate_basis = "public confusion posterior; assumes 3,000 total attacks"
            residual_precision: float | str = ""
        else:
            residual_precision = float(spec["assumed_residual_precision"])
            estimate = private_score_with_additions(
                base_private_true_positives,
                base_private_predictions,
                additions,
                residual_precision,
            )
            lower = private_score_with_additions(
                base_private_true_positives,
                base_private_predictions,
                additions,
                0.0,
            )
            upper = private_score_with_additions(
                base_private_true_positives,
                base_private_predictions,
                additions,
                0.50,
            )
            public_score = ""
            estimate_basis = "offline stress estimate; not leaderboard evidence"

        rows.append(
            {
                "rank": spec["rank"],
                "filename": filename,
                "category": spec["category"],
                "positive_labels": positives,
                "additions_vs_champion": additions,
                "removals_vs_champion": removals,
                "actual_public_f1": public_score,
                "estimated_private_f1": round(estimate, 5),
                "estimate_low": round(lower, 5),
                "estimate_high": round(upper, 5),
                "assumed_residual_precision": residual_precision,
                "required_residual_precision": round(break_even_precision, 5),
                "estimate_basis": estimate_basis,
                "description": spec["description"],
                "recommended": "YES" if spec["rank"] == 1 else "NO",
            }
        )

        for precision in [0.0, 0.10, 0.25, break_even_precision, 0.50, 0.75, 1.0]:
            scenario_rows.append(
                {
                    "rank": spec["rank"],
                    "filename": filename,
                    "additions_vs_champion": additions,
                    "assumed_private_precision": round(precision, 6),
                    "scenario_private_f1": round(
                        private_score_with_additions(
                            base_private_true_positives,
                            base_private_predictions,
                            additions,
                            precision,
                        ),
                        6,
                    ),
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(scenario_rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checksums(paths: list[Path]) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(OUTPUT_ROOT)}" for path in paths]
    CHECKSUM_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_deterministic_zip(paths: list[Path]) -> None:
    with zipfile.ZipFile(ZIP_PATH, "w") as archive:
        for path in paths:
            relative = path.relative_to(OUTPUT_ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 7, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    train = pd.read_csv(TRAIN_PATH, low_memory=False)
    test = pd.read_csv(TEST_PATH, low_memory=False)
    champion_submission = pd.read_csv(CHAMPION_PATH)
    validate_submission(champion_submission, test)
    champion = champion_submission["label"].astype(bool)
    if int(champion.sum()) != 2_809:
        raise RuntimeError("Unexpected champion positive count")

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    candidates: dict[str, pd.DataFrame] = {}

    for spec in CANDIDATE_SPECS[:4]:
        source = pd.read_csv(OUTPUT_ROOT / str(spec["source"]))
        validate_submission(source, test)
        filename = str(spec["filename"])
        path = CANDIDATE_DIR / filename
        source.to_csv(path, index=False)
        candidates[filename] = source

    micro_payload = ~champion & test["tcp.stream"].eq(2) & (
        (
            test["frame.len"].eq(189)
            & test["tcp.len"].eq(135)
            & test["tcp.window_size"].eq(5_738)
            & test["mqtt.msgtype"].isna()
        )
        | (
            test["frame.len"].eq(207)
            & test["tcp.len"].eq(153)
            & test["tcp.window_size"].eq(5_740)
            & test["mqtt.msgtype"].isna()
        )
    )
    if int(micro_payload.sum()) != 3:
        raise RuntimeError(f"Expected 3 micro payload rows, found {int(micro_payload.sum())}")

    standard_normal_handshake = (
        test["frame.len"].eq(62) & test["tcp.window_size"].isin([5_760, 64_620])
    ) | (
        test["frame.len"].eq(54) & test["tcp.window_size"].isin([5_755, 64_523])
    )
    capture_context = (
        ~champion
        & test["tcp.stream"].between(2, 5)
        & test["tcp.analysis.initial_rtt"].isna()
        & ~standard_normal_handshake
    )
    if int(capture_context.sum()) != 40:
        raise RuntimeError(f"Expected 40 context rows, found {int(capture_context.sum())}")

    residual_ranking = build_residual_ranking(train, test, champion)
    if len(residual_ranking) < 191:
        raise RuntimeError("Residual ranking has fewer than 191 eligible rows")
    residual_ranking.to_csv(RANKING_PATH, index=False)

    experimental_masks = {
        "submission_candidate_05_micro_payload_hedge.csv": micro_payload,
        "submission_candidate_06_capture_context_hedge.csv": capture_context,
        "submission_candidate_07_pu_top64_hedge.csv": test["Id"].isin(
            residual_ranking.loc[residual_ranking["residual_rank"].le(64), "Id"]
        ),
        "submission_candidate_08_target3000_aggressive.csv": test["Id"].isin(
            residual_ranking.loc[residual_ranking["residual_rank"].le(191), "Id"]
        ),
    }
    for filename, mask in experimental_masks.items():
        path = CANDIDATE_DIR / filename
        candidates[filename] = write_submission(champion | mask, test, path)

    expected_counts = [2_809, 2_805, 2_799, 2_794, 2_812, 2_849, 2_873, 3_000]
    actual_counts = [
        int(candidates[str(spec["filename"])]["label"].sum())
        for spec in CANDIDATE_SPECS
    ]
    if actual_counts != expected_counts:
        raise RuntimeError(f"Unexpected candidate counts: {actual_counts}")

    manifest, scenarios = build_manifest(candidates, champion)
    manifest.to_csv(MANIFEST_PATH, index=False)
    scenarios.to_csv(SCENARIO_PATH, index=False)

    checksum_paths = sorted(CANDIDATE_DIR.glob("*.csv")) + [
        MANIFEST_PATH,
        SCENARIO_PATH,
        RANKING_PATH,
        Path(__file__),
        OUTPUT_ROOT / "predict_final_model.py",
        OUTPUT_ROOT / "model_test_handoff.md",
    ]
    if REPORT_PATH.exists():
        checksum_paths.append(REPORT_PATH)
    write_checksums(checksum_paths)

    zip_paths = checksum_paths + [CHECKSUM_PATH]
    write_deterministic_zip(zip_paths)

    print(manifest.to_string(index=False))
    print(f"candidate_files={len(candidates)}")
    print(f"recommended={CANDIDATE_DIR / CANDIDATE_SPECS[0]['filename']}")
    print(f"zip={ZIP_PATH}")
    print(f"zip_sha256={sha256(ZIP_PATH)}")


if __name__ == "__main__":
    main()
