#!/usr/bin/env python3
"""Export the Chapter 4 Dstat measurements to the CSVs in data/dstat/.

Provenance script. The original experiment folder keeps the cleaned
Dstat recordings and the 80/20 split as Excel workbooks (about 1.5 GB as
.xlsx), which is too large to ship. This script converts the workbooks
that the dissertation's tables were computed from into gzip-compressed
CSVs, value for value: same rows, same order, same columns.

Source layout (the author's archive, not redistributed):

  <src>/normal/80_20/data/{Client1,Client2,Client3,Controller,Dbserver}.xlsx
      20 hours of normal operation per machine (72,000 one-second samples)
  <src>/normal/80_20/train/{Client,Controller,Dbserver}.xlsx
      normal sample used to derive the thresholds
  <src>/normal/80_20/test/{Client,Controller,Dbserver}.xlsx
      unseen normal test sample
  <src>/attack/80_20/test/{Client,Controller,Dbserver}.xlsx
      attack test sample
  <src>/attack/80_20/data/{Fast,Slow}_{Client,Controller,Dbserver}.xlsx
      every attack-period sample of the 40 fast (PyCrypto) and 40 slow
      (PyAES) ransomware runs on each component

The only thing added is a `run` column (1..40) in the attack recordings.
The workbooks hold the runs back to back without a run identifier, so
the runs are told apart by their timestamps: a new run starts where the
clock steps backwards or jumps ahead by more than 10 seconds. The DB
server VM was restored from a snapshot before each run, so its clock
restarts from the snapshot's time and later steps forward to the
current time; in 16 of the 40 slow runs that step falls inside the
attack, and there the forward step belongs to the same run (see
SYNC_JOIN). The resulting 40 runs per
file were checked against the per-run results of the original analysis
(data/results/): the detection delays of all seven parameters agree for
every run.

Usage:
  python export_dstat_csv.py <src> [--out ../data/dstat]
"""

import argparse
import gzip
import io
import sys
from pathlib import Path

import pandas as pd

COMPONENTS = {"Client": "client", "Controller": "controller",
              "Dbserver": "dbserver"}
NORMAL_MACHINES = {"Client1": "client1", "Client2": "client2",
                   "Client3": "client3", "Controller": "controller",
                   "Dbserver": "dbserver"}
RUNS_PER_FILE = 40
GAP = 10            # seconds; a larger forward step starts a new run
SYNC_JOIN = {"Slow_Dbserver"}   # files with in-run clock corrections
MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}


def clock_seconds(df):
    """Seconds on the guest clock (day of month + time of day).

    Dates are dd-mm. A few rows carry the date as Excel rewrote it
    (10-02 shown as 2-Oct); both spellings are read as the same day.
    """
    out = []
    for date, time in zip(df["date"].astype(str), df["time"].astype(str)):
        a, b = date.split("-")
        if b.lower() in MONTHS:
            day, month = MONTHS[b.lower()], int(a)
        else:
            day, month = int(a), int(b)
        h, m, s = (int(x) for x in time.split(":"))
        out.append(((month * 31 + day) * 24 + h) * 3600 + m * 60 + s)
    return out


def number_runs(df, join_sync):
    t = clock_seconds(df)
    starts = [0] + [i for i in range(1, len(t))
                    if t[i] <= t[i - 1] or t[i] - t[i - 1] > GAP]
    segments = list(zip(starts, starts[1:] + [len(t)]))
    runs, i = [], 0
    while i < len(segments):
        s, e = segments[i]
        reset = s == 0 or t[s] <= t[s - 1]       # clock set back
        if (join_sync and reset and i + 1 < len(segments)
                and t[segments[i + 1][0]] - t[e - 1] > 3600):
            e = segments[i + 1][1]               # clock stepped mid-run
            i += 1
        runs.append((s, e))
        i += 1
    labels = [0] * len(t)
    for n, (s, e) in enumerate(runs, 1):
        labels[s:e] = [n] * (e - s)
    return labels, len(runs)


def write_csv_gz(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = df.to_csv(index=False, lineterminator="\n")
    with open(path, "wb") as raw:
        # fixed mtime and no file name: re-exporting gives identical bytes
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                           compresslevel=9, mtime=0) as gz:
            gz.write(text.encode("utf-8"))
    print(f"  {path.as_posix():58s} {len(df):>8,} rows "
          f"{path.stat().st_size / 1e6:6.2f} MB")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", type=Path,
                    help="folder holding normal/ and attack/ (see above)")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "data" / "dstat")
    args = ap.parse_args()
    src, out = args.src, args.out

    def read(rel):
        return pd.read_excel(src / rel)

    print("normal recordings (20 h per machine)")
    for name, low in NORMAL_MACHINES.items():
        write_csv_gz(read(f"normal/80_20/data/{name}.xlsx"),
                     out / "normal" / f"{low}.csv.gz")

    print("80/20 split behind Tables II-VII")
    for name, low in COMPONENTS.items():
        for part, folder in (("normal_sample", "normal/80_20/train"),
                             ("normal_test", "normal/80_20/test"),
                             ("attack_test", "attack/80_20/test")):
            write_csv_gz(read(f"{folder}/{name}.xlsx"),
                         out / "split" / low / f"{part}.csv.gz")

    print("attack recordings (40 fast + 40 slow runs per component)")
    for name, low in COMPONENTS.items():
        for speed in ("Fast", "Slow"):
            key = f"{speed}_{name}"
            df = read(f"attack/80_20/data/{key}.xlsx")
            labels, n = number_runs(df, key in SYNC_JOIN)
            if n != RUNS_PER_FILE:
                sys.exit(f"{key}: found {n} runs, expected {RUNS_PER_FILE}")
            df.insert(0, "run", labels)
            write_csv_gz(df, out / "attack" / f"{low}_{speed.lower()}.csv.gz")


if __name__ == "__main__":
    main()
