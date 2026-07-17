"""Rank unseen test rows without changing the validated submission."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, IsolationForest
from sklearn.impute import SimpleImputer


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "X_train.csv"
TEST_PATH = ROOT / "data" / "X_test.csv"
MODEL_PATH = ROOT / "outputs" / "predict_final_model.py"
PAIR_PATH = ROOT / "outputs" / "submission_pair_novelty.csv"
CONTROL_PATH = ROOT / "outputs" / "submission_control_novelty.csv"
OUTPUT_PATH = ROOT / "work" / "deep_audit_candidates.csv"

CORE_FEATURES = [
    "frame.len",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
    "mqtt.msgtype",
    "mqtt.qos",
    "mqtt.conflag.qos",
    "mqtt.conflag.cleansess",
    "mqtt.kalive",
    "mqtt.username_len",
    "mqtt.passwd_len",
    "mqtt.retain",
    "mqtt.conflag.retain",
    "mqtt.conflag.willflag",
    "mqtt.topic_len",
    "mqtt.len",
    "mqtt.conack.val",
]

SOURCE_COLUMNS = [
    "Frame length on the wire",
    "TCP Segment Len",
    "Calculated window size",
    "Syn",
    "Reset",
    "Acknowledgment",
    "Message Type",
    "QoS Level",
    "QoS Level.1",
    "Clean Session Flag",
    "Keep Alive",
    "User Name Length",
    "Password Length",
    "Retain",
    "Will Retain",
    "Will Flag",
    "Topic Length",
    "Msg Len",
]

MESSAGE_TYPES = {
    "Connect Command": 1,
    "Connect Ack": 2,
    "Publish Message": 3,
    "Publish Ack": 4,
    "Publish Received": 5,
    "Publish Release": 6,
    "Publish Complete": 7,
    "Subscribe Request": 8,
    "Subscribe Ack": 9,
    "Ping Request": 12,
    "Ping Response": 13,
    "Disconnect Req": 14,
}

KEY_SETS = {
    "tcp": [
        "frame.len",
        "tcp.len",
        "tcp.window_size",
        "tcp.flags.syn",
        "tcp.flags.reset",
        "tcp.flags.ack",
    ],
    "mqtt": [
        "mqtt.msgtype",
        "mqtt.qos",
        "mqtt.conflag.qos",
        "mqtt.conflag.cleansess",
        "mqtt.kalive",
        "mqtt.username_len",
        "mqtt.passwd_len",
        "mqtt.retain",
        "mqtt.conflag.retain",
        "mqtt.conflag.willflag",
        "mqtt.topic_len",
        "mqtt.len",
    ],
    "hybrid": ["frame.len", "tcp.window_size", "mqtt.msgtype", "mqtt.len"],
    "core": CORE_FEATURES,
}


def first_value(series: pd.Series) -> pd.Series:
    return series.astype("string").str.split(",").str[0].str.strip()


def qos_value(series: pd.Series) -> pd.Series:
    values = first_value(series)
    result = pd.Series(np.nan, index=series.index, dtype="float64")
    result[values.str.startswith("At most", na=False)] = 0
    result[values.str.startswith("At least", na=False)] = 1
    result[values.str.startswith("Exactly", na=False)] = 2
    return result


def flag_value(series: pd.Series) -> pd.Series:
    values = first_value(series)
    result = pd.Series(np.nan, index=series.index, dtype="float64")
    result[values.eq("Not set")] = 0
    result[values.eq("Set")] = 1
    return result


def numeric_first(series: pd.Series) -> pd.Series:
    return pd.to_numeric(first_value(series), errors="coerce")


def normalize_source(frame: pd.DataFrame) -> pd.DataFrame:
    mapped = pd.DataFrame(index=frame.index)
    mapped["frame.len"] = pd.to_numeric(frame["Frame length on the wire"], errors="coerce")
    mapped["tcp.len"] = pd.to_numeric(frame["TCP Segment Len"], errors="coerce")
    mapped["tcp.window_size"] = pd.to_numeric(frame["Calculated window size"], errors="coerce")
    mapped["tcp.flags.syn"] = flag_value(frame["Syn"])
    mapped["tcp.flags.reset"] = flag_value(frame["Reset"])
    mapped["tcp.flags.ack"] = flag_value(frame["Acknowledgment"])
    mapped["mqtt.msgtype"] = first_value(frame["Message Type"]).map(MESSAGE_TYPES)
    mapped["mqtt.qos"] = qos_value(frame["QoS Level"])
    mapped["mqtt.conflag.qos"] = qos_value(frame["QoS Level.1"])
    mapped["mqtt.conflag.cleansess"] = flag_value(frame["Clean Session Flag"])
    mapped["mqtt.kalive"] = pd.to_numeric(frame["Keep Alive"], errors="coerce")
    mapped["mqtt.username_len"] = pd.to_numeric(frame["User Name Length"], errors="coerce")
    mapped["mqtt.passwd_len"] = pd.to_numeric(frame["Password Length"], errors="coerce")
    mapped["mqtt.retain"] = flag_value(frame["Retain"])
    mapped["mqtt.conflag.retain"] = flag_value(frame["Will Retain"])
    mapped["mqtt.conflag.willflag"] = flag_value(frame["Will Flag"])
    mapped["mqtt.topic_len"] = numeric_first(frame["Topic Length"])
    mapped["mqtt.len"] = numeric_first(frame["Msg Len"])
    mapped["mqtt.conack.val"] = np.where(mapped["mqtt.msgtype"].eq(2), 0.0, np.nan)
    return mapped[CORE_FEATURES]


def numeric_features(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[CORE_FEATURES].apply(pd.to_numeric, errors="coerce")


def row_hash(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    values = frame[columns].apply(pd.to_numeric, errors="coerce").round(6).fillna(-999_999.0)
    return pd.util.hash_pandas_object(values, index=False).astype("uint64")


def tail_probability(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    sorted_reference = np.sort(reference)
    return np.searchsorted(sorted_reference, values, side="right") / len(sorted_reference)


def load_final_labels(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    spec = importlib.util.spec_from_file_location("final_model", MODEL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load final model")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    return model.build_submission(train, test)["label"].astype(bool)


def load_source_samples() -> tuple[pd.DataFrame, pd.Series]:
    paths = sorted((ROOT / "work" / "external").glob("*.zip"))
    paths += sorted((ROOT / "work" / "external" / "raw").glob("*.zip"))
    samples: list[pd.DataFrame] = []
    names: list[pd.Series] = []
    for source_number, path in enumerate(paths):
        with zipfile.ZipFile(path) as archive:
            name = archive.namelist()[0]
            with archive.open(name) as stream:
                for chunk_number, chunk in enumerate(
                    pd.read_csv(stream, usecols=SOURCE_COLUMNS, chunksize=100_000, low_memory=False)
                ):
                    count = min(20_000, len(chunk))
                    sample = chunk.sample(n=count, random_state=20260717 + 1009 * source_number + chunk_number)
                    samples.append(normalize_source(sample))
                    names.append(pd.Series(path.stem, index=sample.index))
    source = pd.concat(samples, ignore_index=True)
    source_names = pd.concat(names, ignore_index=True)
    return source, source_names


def fit_extra_trees(
    normal_fit: pd.DataFrame,
    attack: pd.DataFrame,
    normal_validation: pd.DataFrame,
    test: pd.DataFrame,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    imputer = SimpleImputer(strategy="constant", fill_value=-1.0)
    fit_x = pd.concat([normal_fit, attack], ignore_index=True)
    fit_y = np.concatenate([np.zeros(len(normal_fit), dtype=np.int8), np.ones(len(attack), dtype=np.int8)])
    x_values = imputer.fit_transform(fit_x)
    model = ExtraTreesClassifier(
        n_estimators=350,
        max_features=0.9,
        min_samples_leaf=1,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=random_state,
    )
    model.fit(x_values, fit_y)
    validation_scores = model.predict_proba(imputer.transform(normal_validation))[:, 1]
    test_scores = model.predict_proba(imputer.transform(test))[:, 1]
    return validation_scores, test_scores


def source_file_support(
    test: pd.DataFrame,
    source: pd.DataFrame,
    source_names: pd.Series,
    columns: list[str],
) -> np.ndarray:
    test_hashes = row_hash(test, columns)
    support = np.zeros(len(test), dtype=np.int8)
    for source_name in source_names.unique():
        source_hashes = set(row_hash(source.loc[source_names.eq(source_name)], columns).tolist())
        support += test_hashes.isin(source_hashes).to_numpy(dtype=np.int8)
    return support


def main() -> None:
    train = pd.read_csv(TRAIN_PATH, low_memory=False)
    test = pd.read_csv(TEST_PATH, low_memory=False)
    labels = load_final_labels(train, test)
    normal = numeric_features(train)
    test_features = numeric_features(test)
    split = np.arange(len(normal)) % 5
    normal_fit = normal.loc[split != 0].reset_index(drop=True)
    normal_validation = normal.loc[split == 0].reset_index(drop=True)
    pseudo_attack = test_features.loc[labels].reset_index(drop=True)
    source, source_names = load_source_samples()
    source = numeric_features(source)

    pseudo_validation, pseudo_test = fit_extra_trees(
        normal_fit,
        pseudo_attack,
        normal_validation,
        test_features,
        random_state=20260717,
    )
    source_attack = source.sample(n=min(len(source), 120_000), random_state=20260717).reset_index(drop=True)
    external_validation, external_test = fit_extra_trees(
        normal_fit,
        source_attack,
        normal_validation,
        test_features,
        random_state=20260718,
    )

    imputer = SimpleImputer(strategy="constant", fill_value=-1.0)
    normal_fit_values = imputer.fit_transform(normal_fit)
    isolation = IsolationForest(
        n_estimators=350,
        max_samples=4096,
        contamination="auto",
        n_jobs=-1,
        random_state=20260719,
    )
    isolation.fit(normal_fit_values)
    isolation_validation = -isolation.score_samples(imputer.transform(normal_validation))
    isolation_test = -isolation.score_samples(imputer.transform(test_features))

    result = test.copy()
    result["current_positive"] = labels.astype("int8")
    result["pseudo_attack_score"] = pseudo_test
    result["external_attack_score"] = external_test
    result["isolation_score"] = isolation_test
    result["pseudo_normal_tail"] = tail_probability(pseudo_test, pseudo_validation)
    result["external_normal_tail"] = tail_probability(external_test, external_validation)
    result["isolation_normal_tail"] = tail_probability(isolation_test, isolation_validation)

    train_hashes = row_hash(normal, KEY_SETS["core"])
    test_hashes = row_hash(test_features, KEY_SETS["core"])
    result["normal_core_count"] = test_hashes.map(train_hashes.value_counts()).fillna(0).astype("int32")
    result["test_core_count"] = test_hashes.map(test_hashes.value_counts()).astype("int32")
    for name, columns in KEY_SETS.items():
        result[f"source_{name}_files"] = source_file_support(test_features, source, source_names, columns)

    historical_bad = pd.Series(False, index=test.index)
    if PAIR_PATH.exists() and CONTROL_PATH.exists():
        historical_bad = pd.read_csv(PAIR_PATH)["label"].astype(bool) & ~pd.read_csv(CONTROL_PATH)["label"].astype(bool)
    result["historical_pair_bad"] = historical_bad.astype("int8")
    result["source_support"] = result[[f"source_{name}_files" for name in KEY_SETS]].sum(axis=1)
    result["ensemble_score"] = (
        0.45 * result["pseudo_normal_tail"]
        + 0.45 * result["external_normal_tail"]
        + 0.10 * result["isolation_normal_tail"]
        + 0.05 * (result["source_support"] / len(source_names.unique()))
    )
    result["strict_gate"] = (
        result["pseudo_normal_tail"].ge(0.9995)
        & result["external_normal_tail"].ge(0.9995)
        & result["isolation_normal_tail"].ge(0.995)
        & result["source_support"].ge(1)
        & result["normal_core_count"].eq(0)
        & result["historical_pair_bad"].eq(0)
        & result["current_positive"].eq(0)
    ).astype("int8")

    candidates = result.loc[result["current_positive"].eq(0)].sort_values(
        ["strict_gate", "ensemble_score", "pseudo_attack_score", "external_attack_score"],
        ascending=False,
    )
    candidates.to_csv(OUTPUT_PATH, index=False)

    print(f"source_rows={len(source)}")
    print(f"source_files={source_names.nunique()}")
    print(f"current_positive={int(labels.sum())}")
    print(f"remaining_negative={len(candidates)}")
    for name, values in {
        "pseudo": pseudo_validation,
        "external": external_validation,
        "isolation": isolation_validation,
    }.items():
        print(f"{name}_normal_quantiles={np.quantile(values, [0.5, 0.95, 0.99, 0.999, 0.9995, 1]).round(6).tolist()}")
    print(f"strict_gate_count={int(candidates['strict_gate'].sum())}")
    display_columns = [
        "Id",
        "ensemble_score",
        "pseudo_attack_score",
        "external_attack_score",
        "isolation_score",
        "pseudo_normal_tail",
        "external_normal_tail",
        "isolation_normal_tail",
        "source_support",
        "normal_core_count",
        "test_core_count",
        "historical_pair_bad",
        "frame.len",
        "tcp.len",
        "tcp.window_size",
        "tcp.flags.syn",
        "tcp.flags.ack",
        "mqtt.msgtype",
        "mqtt.kalive",
        "mqtt.topic_len",
        "mqtt.len",
    ]
    print(candidates[display_columns].head(120).to_string(index=False))
    print(f"output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
