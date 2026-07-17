from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "X_train.csv"
TEST = ROOT / "data" / "X_test.csv"
CURRENT = ROOT / "outputs" / "submission_final_probe.csv"
CONTROL = ROOT / "outputs" / "submission_control_novelty.csv"
PAIR = ROOT / "outputs" / "submission_pair_novelty.csv"
SOURCE_DIR = ROOT / "work" / "external" / "source"
OUTPUT = ROOT / "work" / "external_model_scores.csv"

FEATURES = [
    "frame.len",
    "frame.protocols",
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
    "Protocol",
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


def first_value(series: pd.Series) -> pd.Series:
    return series.astype("string").str.split(",").str[0]


def qos_value(series: pd.Series) -> pd.Series:
    first = first_value(series)
    result = pd.Series(np.nan, index=series.index, dtype="float64")
    result[first.str.startswith("At most", na=False)] = 0
    result[first.str.startswith("At least", na=False)] = 1
    result[first.str.startswith("Exactly", na=False)] = 2
    return result


def flag_value(series: pd.Series) -> pd.Series:
    first = first_value(series)
    result = pd.Series(np.nan, index=series.index, dtype="float64")
    result[first.eq("Not set")] = 0
    result[first.eq("Set")] = 1
    return result


def numeric_first(series: pd.Series) -> pd.Series:
    return pd.to_numeric(first_value(series), errors="coerce")


def normalize_source(chunk: pd.DataFrame) -> pd.DataFrame:
    mapped = pd.DataFrame(index=chunk.index)
    mapped["frame.len"] = pd.to_numeric(chunk["Frame length on the wire"], errors="coerce")
    mapped["frame.protocols"] = chunk["Protocol"].eq("MQTT").astype("int8")
    mapped["tcp.len"] = pd.to_numeric(chunk["TCP Segment Len"], errors="coerce")
    mapped["tcp.window_size"] = pd.to_numeric(chunk["Calculated window size"], errors="coerce")
    mapped["tcp.flags.syn"] = flag_value(chunk["Syn"])
    mapped["tcp.flags.reset"] = flag_value(chunk["Reset"])
    mapped["tcp.flags.ack"] = flag_value(chunk["Acknowledgment"])
    mapped["mqtt.msgtype"] = first_value(chunk["Message Type"]).map(MESSAGE_TYPES)
    mapped["mqtt.qos"] = qos_value(chunk["QoS Level"])
    mapped["mqtt.conflag.qos"] = qos_value(chunk["QoS Level.1"])
    mapped["mqtt.conflag.cleansess"] = flag_value(chunk["Clean Session Flag"])
    mapped["mqtt.kalive"] = pd.to_numeric(chunk["Keep Alive"], errors="coerce")
    mapped["mqtt.username_len"] = pd.to_numeric(chunk["User Name Length"], errors="coerce")
    mapped["mqtt.passwd_len"] = pd.to_numeric(chunk["Password Length"], errors="coerce")
    mapped["mqtt.retain"] = flag_value(chunk["Retain"])
    mapped["mqtt.conflag.retain"] = flag_value(chunk["Will Retain"])
    mapped["mqtt.conflag.willflag"] = flag_value(chunk["Will Flag"])
    mapped["mqtt.topic_len"] = numeric_first(chunk["Topic Length"])
    mapped["mqtt.len"] = numeric_first(chunk["Msg Len"])
    mapped["mqtt.conack.val"] = np.where(mapped["mqtt.msgtype"].eq(2), 0.0, np.nan)
    return mapped[FEATURES]


def normalize_competition(frame: pd.DataFrame) -> pd.DataFrame:
    mapped = frame[FEATURES].copy()
    mapped["frame.protocols"] = mapped["frame.protocols"].str.endswith(":mqtt").astype("int8")
    return mapped


def load_attack_reference() -> pd.DataFrame:
    samples = []
    for source_path in sorted(SOURCE_DIR.glob("*.csv")):
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                source_path,
                usecols=SOURCE_COLUMNS,
                chunksize=100_000,
                low_memory=False,
            )
        ):
            sample = chunk.sample(frac=0.12, random_state=20260717 + chunk_number)
            samples.append(normalize_source(sample))
    return pd.concat(samples, ignore_index=True)


def main() -> None:
    train = pd.read_csv(TRAIN, low_memory=False)
    test = pd.read_csv(TEST, low_memory=False)
    current = pd.read_csv(CURRENT)["label"].astype(bool)
    control = pd.read_csv(CONTROL)["label"].astype(bool)
    pair = pd.read_csv(PAIR)["label"].astype(bool)
    attack = load_attack_reference()

    normal_x = normalize_competition(train)
    test_x = normalize_competition(test)
    train_x = pd.concat([normal_x, attack], ignore_index=True)
    train_y = np.concatenate(
        [np.zeros(len(normal_x), dtype="int8"), np.ones(len(attack), dtype="int8")]
    )
    imputer = SimpleImputer(strategy="constant", fill_value=-1)
    train_values = imputer.fit_transform(train_x)
    test_values = imputer.transform(test_x)

    models = {
        "extra": ExtraTreesClassifier(
            n_estimators=350,
            min_samples_leaf=3,
            max_features=0.9,
            class_weight="balanced",
            n_jobs=-1,
            random_state=20260717,
        ),
        "forest": RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=3,
            max_features=0.8,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=20260717,
        ),
        "hist": HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=250,
            max_leaf_nodes=31,
            l2_regularization=1.0,
            class_weight="balanced",
            random_state=20260717,
        ),
    }

    result = test[["Id"] + FEATURES].copy()
    for name, model in models.items():
        model.fit(train_values, train_y)
        result[name] = model.predict_proba(test_values)[:, 1]
    result["ensemble"] = result[["extra", "forest", "hist"]].mean(axis=1)
    result["current"] = current.astype("int8")
    result["final_added"] = (current & ~control).astype("int8")
    result["pair_bad"] = (pair & ~control).astype("int8")
    result.to_csv(OUTPUT, index=False)

    print(f"attack_reference={len(attack)}")
    print(f"output={OUTPUT}")
    for group_name, mask in {
        "current": current,
        "remaining": ~current,
        "final_added": current & ~control,
        "pair_bad": pair & ~control,
    }.items():
        print(group_name, result.loc[mask, ["extra", "forest", "hist", "ensemble"]].describe().to_string())
    columns = ["Id", "ensemble", "extra", "forest", "hist"] + FEATURES
    print(result.loc[~current, columns].sort_values("ensemble", ascending=False).head(150).to_string(index=False))


if __name__ == "__main__":
    main()
