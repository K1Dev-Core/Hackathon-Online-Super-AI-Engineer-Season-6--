"""Audit whether external MQTT attack captures justify new test labels."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.util import hash_pandas_object


ROOT = Path(__file__).resolve().parents[1]
KEY_COLUMNS = [
    "frame.len",
    "tcp.stream",
    "tcp.analysis.initial_rtt",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
]


def first_value(series: pd.Series) -> pd.Series:
    return series.astype("string").str.split(",").str[0].str.strip()


def flag_value(series: pd.Series) -> pd.Series:
    return first_value(series).map({"Set": 1, "Not set": 0})


def normalize_source(frame: pd.DataFrame) -> pd.DataFrame:
    frame_length = next(
        column
        for column in frame.columns
        if column.startswith("Frame length on the wire") or column.startswith("Frame length on wire")
    )
    return pd.DataFrame(
        {
            "frame.len": pd.to_numeric(frame[frame_length], errors="coerce"),
            "tcp.stream": pd.to_numeric(frame["Stream index"], errors="coerce"),
            "tcp.analysis.initial_rtt": pd.to_numeric(frame["iRTT"], errors="coerce"),
            "tcp.len": pd.to_numeric(frame["TCP Segment Len"], errors="coerce"),
            "tcp.window_size": pd.to_numeric(frame["Calculated window size"], errors="coerce"),
            "tcp.flags.syn": flag_value(frame["Syn"]),
            "tcp.flags.reset": flag_value(frame["Reset"]),
            "tcp.flags.ack": flag_value(frame["Acknowledgment"]),
        }
    )


def key_hashes(frame: pd.DataFrame) -> np.ndarray:
    values = frame[KEY_COLUMNS].apply(pd.to_numeric, errors="coerce").astype("float64")
    values["tcp.analysis.initial_rtt"] = values["tcp.analysis.initial_rtt"].round(6)
    return hash_pandas_object(values.fillna(-999_999.0), index=False).to_numpy()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", action="append", required=True, type=Path)
    parser.add_argument("--test", default=ROOT / "data" / "X_test.csv", type=Path)
    parser.add_argument(
        "--submission",
        default=ROOT / "outputs" / "submission_rank1_structural_plus1.csv",
        type=Path,
    )
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    args = parser.parse_args()

    test = pd.read_csv(args.test, low_memory=False)
    submission = pd.read_csv(args.submission)
    if not submission["Id"].equals(test["Id"]):
        raise RuntimeError("Submission Id order does not match test data")

    labels = submission["label"].to_numpy(dtype=np.int8)
    test_hashes = key_hashes(test)
    union = np.zeros(len(test), dtype=bool)
    rows: list[dict[str, int | str]] = []

    for source_path in args.source_csv:
        source = pd.read_csv(source_path, low_memory=False)
        source_hashes = set(key_hashes(normalize_source(source)).tolist())
        matches = np.isin(test_hashes, list(source_hashes))
        union |= matches
        rows.append(
            {
                "source_csv": source_path.name,
                "source_rows": len(source),
                "exact_test_matches": int(matches.sum()),
                "matched_current_attack": int(labels[matches].sum()),
                "matched_current_normal": int((1 - labels[matches]).sum()),
            }
        )

    result = pd.DataFrame(rows).sort_values("source_csv").reset_index(drop=True)
    result.loc[len(result)] = {
        "source_csv": "UNION",
        "source_rows": int(result.loc[result["source_csv"].ne("UNION"), "source_rows"].sum()),
        "exact_test_matches": int(union.sum()),
        "matched_current_attack": int(labels[union].sum()),
        "matched_current_normal": int((1 - labels[union]).sum()),
    }

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output_csv, index=False)

    union_row = result.iloc[-1]
    decision = (
        "No source-supported additions were found."
        if int(union_row["matched_current_normal"]) == 0
        else "Source-supported additions require review."
    )
    report = "\n".join(
        [
            "# Source Coverage Audit",
            "",
            "## Input",
            "",
            f"- Submission: `{args.submission.name}`",
            f"- Submission SHA256: `{digest(args.submission)}`",
            f"- Positive labels: `{int(labels.sum())}`",
            "- Match key: frame length, TCP stream, RTT rounded to 6 decimals, TCP length, window, SYN, RST, ACK.",
            "",
            "## Result",
            "",
            f"- Exact source/test union: `{int(union_row['exact_test_matches'])}` rows.",
            f"- Already labeled attack: `{int(union_row['matched_current_attack'])}` rows.",
            f"- Candidate additions: `{int(union_row['matched_current_normal'])}` rows.",
            f"- Decision: {decision}",
            "",
            "## Per Source",
            "",
            markdown_table(result),
            "",
            "This audit is evidence for precision only. It does not estimate Kaggle score and does not upload a submission.",
            "",
        ]
    )
    args.output_report.write_text(report, encoding="ascii")
    print(f"output_csv={args.output_csv}")
    print(f"output_report={args.output_report}")
    print(f"candidate_additions={int(union_row['matched_current_normal'])}")


if __name__ == "__main__":
    main()
