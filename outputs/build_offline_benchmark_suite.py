"""Build and score offline SuperAI6 submission variants without Kaggle uploads."""

from __future__ import annotations

import hashlib
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TEST_PATH = ROOT / "data" / "X_test.csv"
CHAMPION_PATH = OUTPUTS / "submission_rank1_best_publish_complete.csv"
STRUCTURAL_PATH = OUTPUTS / "submission_rank1_structural_plus1.csv"
SOURCE_CANDIDATES = OUTPUTS / "submission_candidates"
CANDIDATE_DIR = OUTPUTS / "offline_benchmark_candidates"
RESULTS_PATH = OUTPUTS / "offline_benchmark_results.csv"
WINNERS_PATH = OUTPUTS / "offline_benchmark_winners.csv"
SENSITIVITY_PATH = OUTPUTS / "offline_benchmark_sensitivity.csv"
REPORT_PATH = OUTPUTS / "offline_benchmark_report.md"
CHECKSUM_PATH = OUTPUTS / "offline_benchmark_checksums.sha256"
ZIP_PATH = OUTPUTS / "superai6_offline_benchmark_bundle.zip"

TOTAL_ATTACKS = 3_000
CHAMPION_POSITIVES = 2_809
PUBLIC_CHAMPION_SCORE = 0.96193
STRUCTURAL_ID = 9_816
STRUCTURAL_PROBABILITY = 214 / 215
MONTE_CARLO_RUNS = 20_000
MONTE_CARLO_SEED = 20_260_717
ATTACK_TOTAL_SCENARIOS = (2_900, 3_000, 3_100)
STRUCTURAL_PROBABILITY_SCENARIOS = (0.50, 0.75, 0.90, 0.98, STRUCTURAL_PROBABILITY)


SPECS = [
    {
        "filename": "submission_offline_01_scoremax_structural.csv",
        "description": "Champion plus structural stream-completion row.",
        "ids": [STRUCTURAL_ID],
    },
    {
        "filename": "submission_offline_02_hedge_payload132.csv",
        "description": "Structural row plus one undecoded 132-byte payload hedge.",
        "ids": [STRUCTURAL_ID, 1_145],
    },
    {
        "filename": "submission_offline_03_hedge_payload150.csv",
        "description": "Structural row plus one undecoded 150-byte payload hedge.",
        "ids": [STRUCTURAL_ID, 5_516],
    },
    {
        "filename": "submission_offline_04_hedge_rare_ack.csv",
        "description": "Structural row plus one rare stream-2 ACK hedge.",
        "ids": [STRUCTURAL_ID, 6_011],
    },
    {
        "filename": "submission_offline_05_hedge_stream5_ack.csv",
        "description": "Structural row plus one stream-5 ACK hedge.",
        "ids": [STRUCTURAL_ID, 4_057],
    },
    {
        "filename": "submission_offline_06_plus_micro3.csv",
        "description": "Structural row plus all three undecoded payload candidates.",
        "ids": [STRUCTURAL_ID, 1_145, 5_244, 5_516],
    },
    {
        "filename": "submission_offline_07_plus_top10.csv",
        "description": "Structural row plus top ten residual-ranked rows.",
        "source": "top10",
    },
    {
        "filename": "submission_offline_08_plus_context40.csv",
        "description": "Structural row plus 40 capture-context rows.",
        "source": "context40",
    },
    {
        "filename": "submission_offline_09_plus_pu64.csv",
        "description": "Structural row plus 64 PU-ranked rows.",
        "source": "pu64",
    },
    {
        "filename": "submission_offline_10_target3000.csv",
        "description": "Structural row plus 190 residual rows; 3,000 positives.",
        "source": "target3000",
    },
    {
        "filename": "submission_offline_11_champion_control.csv",
        "description": "Exact scored champion control.",
        "ids": [],
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


def addition_ids(source: pd.DataFrame, champion: pd.DataFrame) -> set[int]:
    mask = source["label"].eq(1) & champion["label"].eq(0)
    return set(source.loc[mask, "Id"].astype(int))


def build_id_sets(champion: pd.DataFrame) -> dict[str, set[int]]:
    ranking = pd.read_csv(OUTPUTS / "candidate_residual_ranking.csv")
    context = pd.read_csv(SOURCE_CANDIDATES / "submission_candidate_06_capture_context_hedge.csv")
    pu64 = pd.read_csv(SOURCE_CANDIDATES / "submission_candidate_07_pu_top64_hedge.csv")
    target = pd.read_csv(SOURCE_CANDIDATES / "submission_candidate_08_target3000_aggressive.csv")

    rank_by_id = ranking.set_index("Id")["residual_rank"].to_dict()
    context_ids = addition_ids(context, champion)
    pu64_ids = addition_ids(pu64, champion)
    target_ids = addition_ids(target, champion)
    top10_ids = set(ranking.loc[ranking["residual_rank"].le(10), "Id"].astype(int))

    weakest_target = max(target_ids, key=lambda row_id: rank_by_id.get(row_id, math.inf))
    structural_target = (target_ids - {weakest_target}) | {STRUCTURAL_ID}
    if len(structural_target) != 191:
        raise RuntimeError("Target-3000 structural swap failed")

    return {
        "top10": top10_ids | {STRUCTURAL_ID},
        "context40": context_ids | {STRUCTURAL_ID},
        "pu64": pu64_ids | {STRUCTURAL_ID},
        "target3000": structural_target,
    }


def build_candidates(
    test: pd.DataFrame,
    champion: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[str, set[int]]]:
    source_sets = build_id_sets(champion)
    candidates: dict[str, pd.DataFrame] = {}
    candidate_additions: dict[str, set[int]] = {}
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    for spec in SPECS:
        ids = set(spec.get("ids", source_sets.get(str(spec.get("source")), set())))
        labels = champion["label"].astype(bool) | test["Id"].isin(ids)
        submission = test[["Id"]].copy()
        submission["label"] = labels.astype("int8")
        validate_submission(submission, test)
        filename = str(spec["filename"])
        submission.to_csv(CANDIDATE_DIR / filename, index=False)
        candidates[filename] = submission
        candidate_additions[filename] = addition_ids(submission, champion)

    return candidates, candidate_additions


def residual_weights(
    test: pd.DataFrame,
    champion: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    pool_mask = champion["label"].eq(0) & test["Id"].ne(STRUCTURAL_ID)
    pool_ids = test.loc[pool_mask, "Id"].to_numpy(dtype="int32")
    pool = test.loc[pool_mask].copy()
    weights = np.where(pool["tcp.stream"].le(5), 1.0, 0.01)
    weights *= np.where(pool["tcp.analysis.initial_rtt"].notna(), 0.03, 1.0)

    ranking = pd.read_csv(OUTPUTS / "candidate_residual_ranking.csv")
    score_by_id = ranking.set_index("Id")["residual_score"]
    residual_score = pool["Id"].map(score_by_id).fillna(0.0).to_numpy()
    weights *= 1.0 + residual_score

    control = pd.read_csv(OUTPUTS / "submission_control_novelty.csv")["label"].astype(bool)
    pair = pd.read_csv(OUTPUTS / "submission_pair_novelty.csv")["label"].astype(bool)
    pair_bad_ids = set(test.loc[pair & ~control, "Id"].astype(int))
    weights *= np.where(pool["Id"].isin(pair_bad_ids), 0.20, 1.0)
    ping = (
        pool["frame.len"].eq(56)
        & pool["tcp.window_size"].eq(253)
        & pool["mqtt.msgtype"].eq(13)
    )
    weights[ping.to_numpy()] = 1e-9
    weights = np.maximum(weights, 1e-12)
    weights /= weights.sum()
    return pool_ids, weights


def f1_score(
    true_positives: np.ndarray | float,
    predicted_positives: int,
    total_attacks: int = TOTAL_ATTACKS,
) -> np.ndarray:
    return 2.0 * np.asarray(true_positives) / (total_attacks + predicted_positives)


def required_structural_probability(additions: int, total_attacks: int = TOTAL_ATTACKS) -> float:
    champion_f1 = float(f1_score(CHAMPION_POSITIVES, CHAMPION_POSITIVES, total_attacks))
    false_score = float(
        f1_score(CHAMPION_POSITIVES, CHAMPION_POSITIVES + additions, total_attacks)
    )
    true_score = float(
        f1_score(CHAMPION_POSITIVES + 1, CHAMPION_POSITIVES + additions, total_attacks)
    )
    if true_score <= champion_f1:
        return math.inf
    return (champion_f1 - false_score) / (true_score - false_score)


def run_benchmark(
    test: pd.DataFrame,
    champion: pd.DataFrame,
    candidates: dict[str, pd.DataFrame],
    candidate_additions: dict[str, set[int]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    pool_ids, weights = residual_weights(test, champion)
    rng = np.random.default_rng(MONTE_CARLO_SEED)
    scores = {filename: np.empty(MONTE_CARLO_RUNS) for filename in candidates}
    added_tp = {filename: np.empty(MONTE_CARLO_RUNS, dtype="int16") for filename in candidates}

    structural_truth = rng.random(MONTE_CARLO_RUNS) < STRUCTURAL_PROBABILITY
    for run in range(MONTE_CARLO_RUNS):
        sample_size = TOTAL_ATTACKS - CHAMPION_POSITIVES - int(structural_truth[run])
        sampled = set(rng.choice(pool_ids, size=sample_size, replace=False, p=weights).tolist())
        if structural_truth[run]:
            sampled.add(STRUCTURAL_ID)
        for filename, additions in candidate_additions.items():
            tp_add = len(additions & sampled)
            added_tp[filename][run] = tp_add
            submission = candidates[filename]
            removals = int((champion["label"].eq(1) & submission["label"].eq(0)).sum())
            tp = CHAMPION_POSITIVES - removals + tp_add
            scores[filename][run] = f1_score(tp, int(submission["label"].sum()))

    champion_filename = "submission_offline_11_champion_control.csv"
    structural_filename = "submission_offline_01_scoremax_structural.csv"
    champion_scores = scores[champion_filename]
    structural_scores = scores[structural_filename]
    spec_by_filename = {str(spec["filename"]): spec for spec in SPECS}
    rows = []

    for filename, values in scores.items():
        additions = len(candidate_additions[filename])
        threshold = required_structural_probability(additions)
        mean_f1 = float(values.mean())
        win_rate = float((values > champion_scores).mean())
        win_structural = float((values > structural_scores).mean())
        if filename == structural_filename:
            verdict = "SCORE_MAX_WINNER"
        elif (
            additions == 2
            and threshold <= STRUCTURAL_PROBABILITY
            and mean_f1 > float(champion_scores.mean())
            and win_rate >= 0.95
        ):
            verdict = "CHAMPION_BEATING_BACKUP"
        elif filename == champion_filename:
            verdict = "CONTROL"
        else:
            verdict = "LOSES_OFFLINE"
        rows.append(
            {
                "filename": filename,
                "description": spec_by_filename[filename]["description"],
                "positive_labels": int(candidates[filename]["label"].sum()),
                "additions_vs_champion": additions,
                "mean_added_true_positives": round(float(added_tp[filename].mean()), 6),
                "offline_mean_f1": round(mean_f1, 8),
                "offline_f1_p05": round(float(np.quantile(values, 0.05)), 8),
                "offline_f1_p95": round(float(np.quantile(values, 0.95)), 8),
                "win_rate_vs_champion": round(win_rate, 6),
                "win_rate_vs_structural": round(win_structural, 6),
                "required_structural_probability_if_other_additions_false": (
                    "" if math.isinf(threshold) else round(threshold, 6)
                ),
                "verdict": verdict,
            }
        )

    results = pd.DataFrame(rows).sort_values(
        ["offline_mean_f1", "win_rate_vs_champion"],
        ascending=[False, False],
    ).reset_index(drop=True)
    results.insert(0, "offline_rank", np.arange(1, len(results) + 1))
    champion_mean = float(
        results.loc[results["verdict"].eq("CONTROL"), "offline_mean_f1"].iloc[0]
    )
    results["offline_f1_gain_vs_champion"] = (
        results["offline_mean_f1"] - champion_mean
    ).round(8)
    results["public_delta_proxy"] = (
        PUBLIC_CHAMPION_SCORE + results["offline_f1_gain_vs_champion"]
    ).round(8)
    winners = results.loc[
        results["verdict"].isin(["SCORE_MAX_WINNER", "CHAMPION_BEATING_BACKUP"])
    ].copy()
    return results, winners


def build_sensitivity(candidate_additions: dict[str, set[int]]) -> pd.DataFrame:
    selected = [
        "submission_offline_01_scoremax_structural.csv",
        "submission_offline_02_hedge_payload132.csv",
        "submission_offline_03_hedge_payload150.csv",
        "submission_offline_04_hedge_rare_ack.csv",
        "submission_offline_05_hedge_stream5_ack.csv",
        "submission_offline_11_champion_control.csv",
    ]
    rows = []
    for total_attacks in ATTACK_TOTAL_SCENARIOS:
        champion_f1 = float(f1_score(CHAMPION_POSITIVES, CHAMPION_POSITIVES, total_attacks))
        for structural_probability in STRUCTURAL_PROBABILITY_SCENARIOS:
            for filename in selected:
                additions = candidate_additions[filename]
                expected_tp = CHAMPION_POSITIVES
                if STRUCTURAL_ID in additions:
                    expected_tp += structural_probability
                expected_f1 = float(
                    f1_score(
                        expected_tp,
                        CHAMPION_POSITIVES + len(additions),
                        total_attacks,
                    )
                )
                rows.append(
                    {
                        "total_attacks": total_attacks,
                        "structural_probability": round(structural_probability, 8),
                        "filename": filename,
                        "nonstructural_additions_assumed_true": 0,
                        "conservative_expected_f1": round(expected_f1, 8),
                        "f1_gain_vs_champion": round(expected_f1 - champion_f1, 8),
                        "beats_champion": expected_f1 > champion_f1,
                        "required_structural_probability": round(
                            required_structural_probability(len(additions), total_attacks),
                            8,
                        ),
                    }
                )
    return pd.DataFrame(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(
    results: pd.DataFrame,
    winners: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> None:
    champion_f1 = float(f1_score(CHAMPION_POSITIVES, CHAMPION_POSITIVES))
    structural_true = float(f1_score(CHAMPION_POSITIVES + 1, CHAMPION_POSITIVES + 1))
    structural_false = float(f1_score(CHAMPION_POSITIVES, CHAMPION_POSITIVES + 1))
    structural_mean = float(
        results.loc[
            results["filename"].eq("submission_offline_01_scoremax_structural.csv"),
            "offline_mean_f1",
        ].iloc[0]
    )
    champion_mean = float(
        results.loc[results["filename"].eq("submission_offline_11_champion_control.csv"), "offline_mean_f1"].iloc[0]
    )
    structural_delta = structural_mean - champion_mean
    scoremax_sensitivity = sensitivity.loc[
        sensitivity["filename"].eq("submission_offline_01_scoremax_structural.csv")
    ]
    sensitivity_wins = int(scoremax_sensitivity["beats_champion"].sum())
    sensitivity_total = len(scoremax_sensitivity)
    lines = [
        "# Offline Benchmark Report",
        "",
        "## Winner",
        "",
        "`submission_offline_01_scoremax_structural.csv` ranks first. Same labels as "
        "`submission_rank1_structural_plus1.csv`: champion plus `Id=9816`.",
        "",
        f"Structural probability stress value: `{STRUCTURAL_PROBABILITY:.6f}`. "
        "Null coincidence rate comes from one extra standard stream among 215 candidates matching "
        "the only missing SYN stream.",
        "",
        "## Score Scenarios",
        "",
        f"- Recorded public champion baseline: `{PUBLIC_CHAMPION_SCORE:.5f}`",
        f"- Champion full-test F1 under 3,000 attacks and zero champion false positives: `{champion_f1:.6f}`",
        f"- Structural file if `Id=9816` is attack: `{structural_true:.6f}`",
        f"- Structural file if `Id=9816` is normal: `{structural_false:.6f}`",
        f"- Monte Carlo expected gain over champion: `{structural_delta:+.8f}`",
        f"- Public-delta proxy: `{PUBLIC_CHAMPION_SCORE + structural_delta:.8f}`; decision heuristic only",
        f"- Monte Carlo runs: `{MONTE_CARLO_RUNS:,}`; fixed attack count: `{TOTAL_ATTACKS:,}`",
        f"- Conservative sensitivity: score-max wins `{sensitivity_wins}/{sensitivity_total}` scenarios "
        "across 2,900-3,100 attacks and structural probability 0.50-0.995349",
        "",
        "## Ranked Results",
        "",
        "| Rank | File | Positive | Mean F1 | Public proxy | Win vs champion | Win vs score-max | Verdict |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in results.itertuples(index=False):
        lines.append(
            f"| {row.offline_rank} | `{row.filename}` | {row.positive_labels} | "
            f"{row.offline_mean_f1:.8f} | {row.public_delta_proxy:.8f} | "
            f"{row.win_rate_vs_champion:.4f} | {row.win_rate_vs_structural:.4f} | `{row.verdict}` |"
        )
    lines += [
        "",
        "## Winner Files",
        "",
    ]
    for row in winners.itertuples(index=False):
        role = "primary" if row.verdict == "SCORE_MAX_WINNER" else "backup only"
        lines.append(
            f"- `{row.filename}`: `{row.verdict}`; {role}; mean F1 `{row.offline_mean_f1:.8f}`"
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- Semi-supervised model rejected: it assigned about 0.99 attack probability to known hard-negative PUBLISH window-253 rows.",
        "- Large residual additions lose because required added precision is about 0.486 and observed residual evidence remains far lower.",
        "- Public-delta proxy transfers only the modeled score difference onto 0.96193; it is not a Kaggle prediction.",
        "- Backup hedges beat the champion expectation but lose to score-max in about 89-91% of simulations.",
        "- Benchmark is offline inference, not Kaggle ground truth.",
        "- No Kaggle submission performed.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checksums(paths: list[Path]) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(OUTPUTS)}" for path in paths]
    CHECKSUM_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_zip(paths: list[Path]) -> None:
    with zipfile.ZipFile(ZIP_PATH, "w") as archive:
        for path in paths:
            relative = path.relative_to(OUTPUTS).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 7, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    test = pd.read_csv(TEST_PATH, low_memory=False)
    champion = pd.read_csv(CHAMPION_PATH)
    structural = pd.read_csv(STRUCTURAL_PATH)
    validate_submission(champion, test)
    validate_submission(structural, test)
    if int(champion["label"].sum()) != CHAMPION_POSITIVES:
        raise RuntimeError("Unexpected champion positive count")
    if addition_ids(structural, champion) != {STRUCTURAL_ID}:
        raise RuntimeError("Structural source does not add only Id=9816")

    candidates, candidate_additions = build_candidates(test, champion)
    results, winners = run_benchmark(test, champion, candidates, candidate_additions)
    sensitivity = build_sensitivity(candidate_additions)
    results.to_csv(RESULTS_PATH, index=False)
    winners.to_csv(WINNERS_PATH, index=False)
    sensitivity.to_csv(SENSITIVITY_PATH, index=False)
    write_report(results, winners, sensitivity)

    paths = sorted(CANDIDATE_DIR.glob("*.csv")) + [
        RESULTS_PATH,
        WINNERS_PATH,
        SENSITIVITY_PATH,
        REPORT_PATH,
        Path(__file__),
    ]
    write_checksums(paths)
    write_zip(paths + [CHECKSUM_PATH])

    print(results.to_string(index=False))
    print(f"winner_files={len(winners)}")
    print(f"scoremax={CANDIDATE_DIR / 'submission_offline_01_scoremax_structural.csv'}")
    print(f"bundle_sha256={sha256(ZIP_PATH)}")


if __name__ == "__main__":
    main()
