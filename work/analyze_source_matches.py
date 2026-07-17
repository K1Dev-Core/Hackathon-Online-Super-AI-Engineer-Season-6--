from pathlib import Path

import numpy as np
import pandas as pd

from submit_improved import attack_mask


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
SOURCE_DIR = ROOT / "work" / "external" / "source"
OUTPUT = ROOT / "work" / "source_match_candidates.csv"

TCP_SOURCE_COLUMNS = [
    "Frame length on the wire",
    "Stream index",
    "iRTT",
    "TCP Segment Len",
    "Calculated window size",
    "Syn",
    "Reset",
    "Acknowledgment",
]

TCP_TEST_COLUMNS = [
    "frame.len",
    "tcp.stream",
    "tcp.analysis.initial_rtt",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
]


def normalized_source_tcp(chunk: pd.DataFrame) -> pd.DataFrame:
    mapped = pd.DataFrame(index=chunk.index)
    mapped["frame.len"] = pd.to_numeric(chunk["Frame length on the wire"], errors="coerce")
    mapped["tcp.stream"] = pd.to_numeric(chunk["Stream index"], errors="coerce")
    mapped["tcp.analysis.initial_rtt"] = pd.to_numeric(chunk["iRTT"], errors="coerce")
    mapped["tcp.len"] = pd.to_numeric(chunk["TCP Segment Len"], errors="coerce")
    mapped["tcp.window_size"] = pd.to_numeric(chunk["Calculated window size"], errors="coerce")
    mapped["tcp.flags.syn"] = chunk["Syn"].eq("Set").astype("int8")
    mapped["tcp.flags.reset"] = chunk["Reset"].eq("Set").astype("int8")
    mapped["tcp.flags.ack"] = chunk["Acknowledgment"].eq("Set").astype("int8")
    return mapped


def hash_rows(frame: pd.DataFrame, columns: list[str], rtt_digits: int | None = None) -> pd.Series:
    values = frame[columns].copy()
    if rtt_digits is not None and "tcp.analysis.initial_rtt" in columns:
        values["tcp.analysis.initial_rtt"] = values["tcp.analysis.initial_rtt"].round(rtt_digits)
    return pd.util.hash_pandas_object(values, index=False)


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    baseline = attack_mask(train, test)

    key_specs = {
        "shape": ([column for column in TCP_TEST_COLUMNS if column not in {"tcp.stream", "tcp.analysis.initial_rtt"}], None),
        "stream_shape": ([column for column in TCP_TEST_COLUMNS if column != "tcp.analysis.initial_rtt"], None),
        "exact_rtt": (TCP_TEST_COLUMNS, None),
        "rtt_6": (TCP_TEST_COLUMNS, 6),
        "rtt_5": (TCP_TEST_COLUMNS, 5),
    }
    test_hashes = {
        name: hash_rows(test, columns, digits)
        for name, (columns, digits) in key_specs.items()
    }
    source_hash_sets: dict[str, set[int]] = {name: set() for name in key_specs}
    per_source_sets: dict[str, dict[str, set[int]]] = {}

    for source_path in sorted(SOURCE_DIR.glob("*.csv")):
        source_sets = {name: set() for name in key_specs}
        for chunk in pd.read_csv(
            source_path,
            usecols=TCP_SOURCE_COLUMNS,
            chunksize=100_000,
            low_memory=False,
        ):
            mapped = normalized_source_tcp(chunk)
            for name, (columns, digits) in key_specs.items():
                source_sets[name].update(hash_rows(mapped, columns, digits).astype("uint64").tolist())
        per_source_sets[source_path.stem] = source_sets
        for name in key_specs:
            source_hash_sets[name].update(source_sets[name])

    result = test[["Id"] + TCP_TEST_COLUMNS].copy()
    result["baseline"] = baseline.astype("int8")
    for name in key_specs:
        result[f"match_{name}"] = test_hashes[name].isin(source_hash_sets[name]).astype("int8")
    for source_name, source_sets in per_source_sets.items():
        result[f"source_{source_name}"] = test_hashes["rtt_6"].isin(source_sets["rtt_6"]).astype("int8")

    result.to_csv(OUTPUT, index=False)
    print(f"output={OUTPUT}")
    print(f"baseline_positive={int(baseline.sum())}")
    for name in key_specs:
        matched = result[f"match_{name}"].eq(1)
        print(
            f"{name}: matched={int(matched.sum())} "
            f"new={int((matched & ~baseline).sum())} "
            f"baseline_overlap={int((matched & baseline).sum())}"
        )
    for source_name in per_source_sets:
        matched = result[f"source_{source_name}"].eq(1)
        print(
            f"{source_name}: rtt_6={int(matched.sum())} "
            f"new={int((matched & ~baseline).sum())}"
        )


if __name__ == "__main__":
    main()
