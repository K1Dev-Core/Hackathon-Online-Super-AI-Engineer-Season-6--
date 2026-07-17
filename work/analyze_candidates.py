from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
CURRENT = ROOT / "outputs" / "submission_final_probe.csv"
OUTPUT = ROOT / "work" / "ranked_candidates.csv"


def add_frequency_features(
    train: pd.DataFrame,
    test: pd.DataFrame,
    columns: list[str],
    prefix: str,
) -> None:
    train_hash = pd.util.hash_pandas_object(train[columns], index=False)
    test_hash = pd.util.hash_pandas_object(test[columns], index=False)
    train_counts = train_hash.value_counts()
    test_counts = test_hash.value_counts()
    test[f"{prefix}_train_count"] = test_hash.map(train_counts).fillna(0).astype("int32")
    test[f"{prefix}_test_count"] = test_hash.map(test_counts).astype("int32")


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    current = pd.read_csv(CURRENT)["label"].astype(bool)

    packet_columns = [
        column
        for column in test.columns
        if column not in {"Id", "tcp.stream", "tcp.analysis.initial_rtt"}
    ]
    tcp_shape_columns = [
        "frame.len",
        "frame.protocols",
        "tcp.len",
        "tcp.window_size",
        "tcp.flags.syn",
        "tcp.flags.reset",
        "tcp.flags.ack",
    ]
    mqtt_shape_columns = packet_columns
    stream_packet_columns = ["tcp.stream"] + tcp_shape_columns

    add_frequency_features(train, test, packet_columns, "packet")
    add_frequency_features(train, test, tcp_shape_columns, "tcp")
    add_frequency_features(train, test, mqtt_shape_columns, "mqtt")
    add_frequency_features(train, test, stream_packet_columns, "stream_packet")

    normal_ratio = 0.07138
    for prefix in ["packet", "tcp", "mqtt", "stream_packet"]:
        train_count = test[f"{prefix}_train_count"]
        test_count = test[f"{prefix}_test_count"]
        test[f"{prefix}_excess"] = (
            1 - normal_ratio * train_count / test_count
        ).clip(0, 1)

    normal_windows = set(train["tcp.window_size"].unique())
    test["window_novel"] = ~test["tcp.window_size"].isin(normal_windows)
    test["rtt_novel"] = (
        test["tcp.analysis.initial_rtt"].notna()
        & ~test["tcp.analysis.initial_rtt"].isin(set(train["tcp.analysis.initial_rtt"].dropna()))
    )
    test["current"] = current.astype("int8")
    test["candidate_score"] = (
        0.45 * test["packet_excess"]
        + 0.25 * test["tcp_excess"]
        + 0.20 * test["stream_packet_excess"]
        + 0.10 * test["rtt_novel"].astype(float)
    )

    ranked = test.loc[~current].sort_values(
        ["candidate_score", "packet_excess", "stream_packet_excess"],
        ascending=False,
    )
    ranked.to_csv(OUTPUT, index=False)

    print(f"output={OUTPUT}")
    print(f"current_positive={int(current.sum())}")
    print(f"remaining={len(ranked)}")
    print("candidate score bands")
    print(pd.cut(ranked["candidate_score"], [-0.001, 0.25, 0.5, 0.75, 0.9, 1.001]).value_counts().sort_index())
    print("novel packet negatives", int(ranked["packet_train_count"].eq(0).sum()))
    print("novel rtt negatives", int(ranked["rtt_novel"].sum()))
    display_columns = [
        "Id",
        "candidate_score",
        "packet_train_count",
        "packet_test_count",
        "packet_excess",
        "tcp_train_count",
        "tcp_test_count",
        "tcp_excess",
        "stream_packet_train_count",
        "stream_packet_test_count",
        "stream_packet_excess",
        "rtt_novel",
        "frame.len",
        "frame.protocols",
        "tcp.stream",
        "tcp.analysis.initial_rtt",
        "tcp.len",
        "tcp.window_size",
        "tcp.flags.syn",
        "tcp.flags.ack",
        "mqtt.msgtype",
        "mqtt.kalive",
        "mqtt.topic_len",
        "mqtt.len",
    ]
    print(ranked[display_columns].head(120).to_string(index=False))


if __name__ == "__main__":
    main()
