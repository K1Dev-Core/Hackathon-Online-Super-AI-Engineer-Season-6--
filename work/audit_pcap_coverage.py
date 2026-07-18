"""Check whether labeled external attack PCAPs expose missed test rows."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
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


def key_hashes(frame: pd.DataFrame) -> np.ndarray:
    values = frame[KEY_COLUMNS].apply(pd.to_numeric, errors="coerce").astype("float64")
    values["tcp.analysis.initial_rtt"] = values["tcp.analysis.initial_rtt"].round(6)
    return hash_pandas_object(values.fillna(-999_999.0), index=False).to_numpy(dtype="uint64")


def extract_tcp_hashes(pcap_path: Path, tshark: str) -> tuple[set[int], int]:
    command = [
        tshark,
        "-r",
        str(pcap_path),
        "-Y",
        "tcp",
        "-T",
        "fields",
        "-E",
        "header=y",
        "-E",
        "separator=,",
    ]
    for column in KEY_COLUMNS:
        command.extend(["-e", column])

    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".csv") as extracted:
        subprocess.run(command, check=True, stdout=extracted, stderr=subprocess.PIPE)
        extracted.flush()
        extracted.seek(0)
        hashes: set[int] = set()
        row_count = 0
        for chunk in pd.read_csv(extracted.name, chunksize=100_000, low_memory=False):
            row_count += len(chunk)
            hashes.update(key_hashes(chunk).tolist())
    return hashes, row_count


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
    parser.add_argument("--source-pcap", action="append", required=True, type=Path)
    parser.add_argument("--test", default=ROOT / "data" / "X_test.csv", type=Path)
    parser.add_argument(
        "--submission",
        default=ROOT / "outputs" / "submission_rank1_structural_plus1.csv",
        type=Path,
    )
    parser.add_argument("--tshark", default="tshark")
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
    for pcap_path in args.source_pcap:
        source_hashes, tcp_rows = extract_tcp_hashes(pcap_path, args.tshark)
        matches = np.isin(test_hashes, list(source_hashes))
        union |= matches
        rows.append(
            {
                "source_pcap": pcap_path.name,
                "pcap_bytes": pcap_path.stat().st_size,
                "tcp_rows": tcp_rows,
                "exact_test_matches": int(matches.sum()),
                "matched_current_attack": int(labels[matches].sum()),
                "matched_current_normal": int((1 - labels[matches]).sum()),
            }
        )

    result = pd.DataFrame(rows).sort_values("source_pcap").reset_index(drop=True)
    result.loc[len(result)] = {
        "source_pcap": "UNION",
        "pcap_bytes": int(result["pcap_bytes"].sum()),
        "tcp_rows": int(result["tcp_rows"].sum()),
        "exact_test_matches": int(union.sum()),
        "matched_current_attack": int(labels[union].sum()),
        "matched_current_normal": int((1 - labels[union]).sum()),
    }

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output_csv, index=False)
    union_row = result.iloc[-1]
    additions = int(union_row["matched_current_normal"])
    decision = "No source-supported additions were found." if additions == 0 else "Review source-supported additions."
    args.output_report.write_text(
        "\n".join(
            [
                "# PCAP Coverage Audit",
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
                f"- Exact PCAP/test union: `{int(union_row['exact_test_matches'])}` rows.",
                f"- Already labeled attack: `{int(union_row['matched_current_attack'])}` rows.",
                f"- Candidate additions: `{additions}` rows.",
                f"- Decision: {decision}",
                "",
                "## Per Source",
                "",
                markdown_table(result),
                "",
                "This audit does not estimate Kaggle score and does not upload a submission.",
                "",
            ]
        ),
        encoding="ascii",
    )
    print(f"output_csv={args.output_csv}")
    print(f"output_report={args.output_report}")
    print(f"candidate_additions={additions}")


if __name__ == "__main__":
    main()
