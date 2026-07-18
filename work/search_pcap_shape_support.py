"""Collect class-conditional PCAP support for competition packet shapes."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from kaggle import KaggleApi
from pandas.util import hash_pandas_object

from search_pcap_source_candidates import DATASET, list_pcaps, source_metadata


ROOT = Path(__file__).resolve().parents[1]
FEATURE_COLUMNS = [
    "frame.len",
    "frame.protocols",
    "tcp.stream",
    "tcp.analysis.initial_rtt",
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
TCP_SHAPE_COLUMNS = [
    "frame.len",
    "frame.protocols",
    "tcp.len",
    "tcp.window_size",
    "tcp.flags.syn",
    "tcp.flags.reset",
    "tcp.flags.ack",
]
PACKET_COLUMNS = [
    column
    for column in FEATURE_COLUMNS
    if column not in {"tcp.stream", "tcp.analysis.initial_rtt"}
]
HASH_SPECS = {
    "tcp_shape": TCP_SHAPE_COLUMNS,
    "packet": PACKET_COLUMNS,
    "packet_stream": [
        column for column in FEATURE_COLUMNS if column != "tcp.analysis.initial_rtt"
    ],
    "packet_rtt": [column for column in FEATURE_COLUMNS if column != "tcp.stream"],
    "packet_full": FEATURE_COLUMNS,
}
BASE_COLUMNS = [
    "source_pcap",
    "family",
    "traffic_mode",
    "pcap_bytes",
    "tcp_rows",
    "status",
    "attempts",
    "error",
]


def normalize(frame: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    for column in FEATURE_COLUMNS:
        if column == "frame.protocols":
            result[column] = frame[column].fillna("").astype("string")
        else:
            result[column] = pd.to_numeric(frame[column], errors="coerce").astype("float64")
    result["tcp.analysis.initial_rtt"] = result["tcp.analysis.initial_rtt"].round(6)
    return result


def row_hashes(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    values = frame[columns].copy()
    numeric = [column for column in columns if column != "frame.protocols"]
    values[numeric] = values[numeric].fillna(-999_999.0)
    if "frame.protocols" in columns:
        values["frame.protocols"] = values["frame.protocols"].fillna("")
    return hash_pandas_object(values, index=False).to_numpy(dtype="uint64")


def extract_support(
    pcap_path: Path,
    tshark: str,
    test_hash_sets: dict[str, set[int]],
) -> tuple[dict[str, set[int]], int]:
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
        "-E",
        "occurrence=f",
    ]
    for column in FEATURE_COLUMNS:
        command.extend(["-e", column])

    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".csv") as extracted:
        result = subprocess.run(command, stdout=extracted, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"tshark exited {result.returncode}: {error}")
        extracted.flush()
        extracted.seek(0)
        matched = {name: set() for name in HASH_SPECS}
        row_count = 0
        for chunk in pd.read_csv(extracted.name, chunksize=100_000, low_memory=False):
            row_count += len(chunk)
            normalized = normalize(chunk)
            for name, columns in HASH_SPECS.items():
                source_hashes = set(row_hashes(normalized, columns).tolist())
                matched[name].update(source_hashes.intersection(test_hash_sets[name]))
    return matched, row_count


def scan_source(
    source_name: str,
    expected_bytes: int,
    tshark: str,
    test_hash_sets: dict[str, set[int]],
    retries: int,
) -> dict[str, int | str]:
    family, traffic_mode = source_metadata(source_name)
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            with tempfile.TemporaryDirectory(prefix="superai6-pcap-shape-") as temporary:
                temporary_path = Path(temporary)
                api = KaggleApi()
                api.authenticate()
                api.dataset_download_file(
                    DATASET,
                    source_name,
                    path=temporary_path,
                    force=True,
                    quiet=True,
                )
                archives = list(temporary_path.glob("*.zip"))
                if len(archives) != 1:
                    raise RuntimeError(f"expected one zip, found {len(archives)}")
                with zipfile.ZipFile(archives[0]) as archive:
                    bad_member = archive.testzip()
                    if bad_member is not None:
                        raise RuntimeError(f"corrupt zip member: {bad_member}")
                    members = [name for name in archive.namelist() if name.lower().endswith(".pcap")]
                    if len(members) != 1:
                        raise RuntimeError(f"expected one PCAP member, found {len(members)}")
                    archive.extract(members[0], path=temporary_path)
                    pcap_path = temporary_path / members[0]
                if expected_bytes and pcap_path.stat().st_size != expected_bytes:
                    raise RuntimeError(
                        f"PCAP size {pcap_path.stat().st_size} != manifest {expected_bytes}"
                    )
                matched, tcp_rows = extract_support(pcap_path, tshark, test_hash_sets)
                row: dict[str, int | str] = {
                    "source_pcap": source_name,
                    "family": family,
                    "traffic_mode": traffic_mode,
                    "pcap_bytes": pcap_path.stat().st_size,
                    "tcp_rows": tcp_rows,
                    "status": "OK",
                    "attempts": attempt,
                    "error": "",
                }
                for name in HASH_SPECS:
                    row[f"matched_{name}_hashes"] = "|".join(
                        str(value) for value in sorted(matched[name])
                    )
                    row[f"matched_{name}"] = len(matched[name])
                return row
        except Exception as error:  # noqa: BLE001 - source failures are retried and recorded.
            last_error = str(error)
            if attempt < retries:
                time.sleep(2**attempt)

    row = {
        "source_pcap": source_name,
        "family": family,
        "traffic_mode": traffic_mode,
        "pcap_bytes": expected_bytes,
        "tcp_rows": 0,
        "status": "ERROR",
        "attempts": retries,
        "error": last_error,
    }
    for name in HASH_SPECS:
        row[f"matched_{name}_hashes"] = ""
        row[f"matched_{name}"] = 0
    return row


def output_columns() -> list[str]:
    columns = BASE_COLUMNS.copy()
    for name in HASH_SPECS:
        columns.extend([f"matched_{name}_hashes", f"matched_{name}"])
    return columns


def write_results(frame: pd.DataFrame, output: Path) -> None:
    ordered = frame[output_columns()].copy()
    ordered["_status_rank"] = ordered["status"].eq("OK").astype("int8")
    ordered = (
        ordered.sort_values(["source_pcap", "_status_rank"])
        .drop_duplicates("source_pcap", keep="last")
        .drop(columns="_status_rank")
        .reset_index(drop=True)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    ordered.to_csv(output, index=False)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["attack", "normal"], required=True)
    parser.add_argument("--test", default=ROOT / "data" / "X_test.csv", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tshark", default="tshark")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    test = normalize(pd.read_csv(args.test, low_memory=False))
    test_hash_sets = {
        name: set(row_hashes(test, columns).tolist())
        for name, columns in HASH_SPECS.items()
    }

    existing = pd.DataFrame(columns=output_columns())
    processed: set[str] = set()
    if args.output.exists():
        existing = pd.read_csv(args.output, low_memory=False)
        missing = set(output_columns()).difference(existing.columns)
        if missing:
            raise RuntimeError(f"Existing output is missing columns: {sorted(missing)}")
        processed = set(existing.loc[existing["status"].eq("OK"), "source_pcap"])

    manifest = list_pcaps(args.mode)
    selected = manifest[args.start :]
    if args.limit is not None:
        selected = selected[: args.limit]
    pending = [(name, size) for name, size in selected if name not in processed]
    print(
        f"mode={args.mode} manifest={len(manifest)} processed={len(processed)} "
        f"pending={len(pending)} test_rows={len(test)}",
        flush=True,
    )

    rows: list[dict[str, int | str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                scan_source,
                source_name,
                expected_bytes,
                args.tshark,
                test_hash_sets,
                args.retries,
            ): source_name
            for source_name, expected_bytes in pending
        }
        for number, future in enumerate(as_completed(futures), start=1):
            row = future.result()
            rows.append(row)
            current = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
            write_results(current, args.output)
            match_summary = ",".join(
                f"{name}={row[f'matched_{name}']}" for name in HASH_SPECS
            )
            print(
                f"progress={number}/{len(pending)} status={row['status']} "
                f"{match_summary} source={row['source_pcap']}",
                flush=True,
            )

    final = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    if final.empty:
        final = pd.DataFrame(columns=output_columns())
    write_results(final, args.output)
    print(f"output_sha256={digest(args.output)}", flush=True)


if __name__ == "__main__":
    main()
