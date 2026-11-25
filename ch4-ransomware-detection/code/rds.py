#!/usr/bin/env python3
"""Ransomware Detection System (RDS) - threshold-based detection.

Implements Algorithm Building-RDS from Chapter 4 (published in
P. Roemsri, S. Puangpontip, R. Hewett, "On Detecting Crypto Ransomware
Attacks: Can Simple Strategies be Effective?", ICICT 2023,
DOI 10.1109/ICICT58900.2023.00030, Fig. 1):

  1. collect performance data of each component under normal operations
     (N) and under ransomware attacks (A),
  2. Threshold(C, p) = average of parameter p over the normal sample
     (lines 16-17),
  3. evaluate every parameter's threshold on an unseen test sample T of
     normal + attack instances and select the parameter with the best
     result as the component's indicator (line 20),
  4. detect: alert attack when an incoming value exceeds the selected
     parameter's threshold (lines 26-28).

Performance parameters are the Dstat attributes of the paper's Table I:
cpu.usr (%), mem.used (bytes), dsk.read / dsk.writ (bytes), io.read /
io.writ (#requests); a power estimate column is used as a seventh
parameter when the file has one. Input files are CSVs with those
columns, plain or gzip-compressed (a raw Dstat --output CSV is accepted:
its preamble and two-row header are detected and flattened; the column
names of the recordings in ../data/dstat are accepted as they are).
Preprocessing follows the paper: leading (and for attack data, trailing)
rows can be trimmed and missing values are filled with the most recent
preceding value.

As in the paper's Tables IV-VI, TN/FP/FN/TP are reported as fractions
of the whole test sample, ACC = TN + TP, and AUC is the area under the
ROC curve of the single-threshold classifier, i.e. balanced accuracy
(TPR + TNR) / 2 (with the paper's balanced test sets, ACC = AUC).
The --three-sigma option reproduces the Table VII baseline instead:
Threshold(C, p) = mean + 3 * std over the normal sample (population
standard deviation), with CPU capped at 100.

The timing command reproduces the Time Computation table: for every
attack run it reports how long after the first attack sample the
parameter first exceeds its threshold, and how long the attack lasted.
Both are differences of the samples' time-of-day stamps, as in the
original analysis; the attack length is also given as a sample count
(one sample per second), which does not depend on the clock.

Usage:
  rds.py build  --normal normal.csv --attack attack.csv
                [--normal-test unseen_normal.csv]
                [--component NAME] [--test-rows K] [--three-sigma]
                [--trim-head N] [--trim-tail N] [--out thresholds.json]
  rds.py detect --config ../config/thresholds.json --component Client
                --input monitoring.csv [--parameter "DISK Read"]
  rds.py timing --config ../config/thresholds.json --component Client
                --attack runs.csv [more.csv ...]
                [--parameter "DISK Read"] [--all-parameters]
"""

import argparse
import csv
import gzip
import json
import math
import sys
from pathlib import Path

PARAMS = {  # report name -> Dstat column (aliases accepted)
    "CPU Usage": ("cpu.usr", "usr"),
    "MEMORY Usage": ("mem.used", "memory.used", "used"),
    "DISK Read": ("dsk.read", "dsk/total.read", "read"),
    "DISK Write": ("dsk.writ", "dsk.write", "dsk/total.writ",
                   "dsk/total.write", "writ"),
    "I/O Read": ("io.read", "io/total.read"),
    "I/O Write": ("io.writ", "io.write", "io/total.writ", "io/total.write"),
}
OPTIONAL_PARAMS = {  # used only when the file has the column
    "Power Consumption": ("power est.", "power"),
}
DAY = 86400


def load_rows(path):
    """Read a CSV of Dstat samples -> list of {param: float}.

    Accepts a plain CSV whose header holds the Table I column names, or
    a raw `dstat --output` CSV, whose preamble lines and group-header
    row are skipped and whose group row + column row are flattened
    (e.g. groups "dsk/total" + column "read" -> "dsk.read"). A file
    ending in .gz is read through gzip. When the file has `time` and
    `run` columns they are kept under the keys "_time" and "_run".
    """
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as fh:
        raw = [r for r in csv.reader(fh)]
    known = {a for names in (*PARAMS.values(), *OPTIONAL_PARAMS.values())
             for a in names}
    header_i = None
    for i, row in enumerate(raw):
        cells = [c.strip().strip('"').lower() for c in row]
        if len(row) > 2 and (
                any(c in ("date", "time", "epoch", "system") for c in cells)
                or any(c in known for c in cells)):
            header_i = i
            break
    if header_i is None:
        sys.exit(f"{path}: no header row with date/time columns found")
    header = [c.strip().strip('"').lower() for c in raw[header_i]]
    body = raw[header_i + 1:]
    if body and not any(_is_num(c) for c in body[0]):
        # dstat layout: raw[header_i] is the group row, body[0] the
        # column row -> flatten "dsk/total"+"read" into "dsk.read"
        groups, cols = header, [c.strip().lower() for c in body[0]]
        header, last = [], ""
        for g, c in zip(groups, cols):
            last = (g or last).split("/")[0].replace("total ", "") \
                             .replace(" usage", "").replace("memory", "mem")
            header.append(f"{last}.{c}" if c not in ("date", "time", "epoch")
                          else c)
        body = body[1:]

    idx = {}
    for name, aliases in PARAMS.items():
        for a in aliases:
            if a in header:
                idx[name] = header.index(a)
                break
        else:
            sys.exit(f"{path}: column for '{name}' not found "
                     f"(looked for {aliases}) in {header}")
    for name, aliases in OPTIONAL_PARAMS.items():
        for a in aliases:
            if a in header:
                idx[name] = header.index(a)
                break
    extra = {key: header.index(col)
             for key, col in (("_time", "time"), ("_run", "run"))
             if col in header}

    rows, prev = [], None
    for r in body:
        if len(r) < len(header) or not any(c.strip() for c in r):
            continue
        rec = {}
        for name, i in idx.items():
            cell = r[i].strip()
            if _is_num(cell):
                rec[name] = float(cell)
            elif prev is not None:          # fill with adjacent recent value
                rec[name] = prev[name]
            else:
                rec = None
                break
        if rec:
            for key, i in extra.items():
                rec[key] = r[i].strip()
            rows.append(rec)
            prev = rec
    return rows


def _is_num(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def params_of(rows):
    """Parameters present in loaded rows, in report order."""
    return [p for p in (*PARAMS, *OPTIONAL_PARAMS) if p in rows[0]]


def mean(xs):
    return math.fsum(xs) / len(xs)


def std(xs):
    m = mean(xs)
    return (math.fsum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


def threshold_of(sample, param, three_sigma=False):
    """Threshold(C, p): normal average, or mean + 3 std for the baseline."""
    xs = [r[param] for r in sample]
    t = mean(xs)
    if three_sigma:
        t += 3 * std(xs)
        if param == "CPU Usage":
            t = min(t, 100.0)
    return t


def evaluate(threshold, normal_test, attack_test, param):
    total = len(normal_test) + len(attack_test)
    tp = sum(1 for r in attack_test if r[param] > threshold)
    tn = sum(1 for r in normal_test if r[param] <= threshold)
    fn, fp = len(attack_test) - tp, len(normal_test) - tn
    tpr = tp / len(attack_test) if attack_test else 0.0
    tnr = tn / len(normal_test) if normal_test else 0.0
    return {"ACC": (tp + tn) / total, "AUC": (tpr + tnr) / 2,
            "TN": tn / total, "FP": fp / total,
            "FN": fn / total, "TP": tp / total}


def build_rds(sample, normal_test, attack_test, three_sigma=False):
    """Thresholds, per-parameter results and the indicator(s) by AUC."""
    thresholds, results = {}, {}
    for p in params_of(sample):
        thresholds[p] = threshold_of(sample, p, three_sigma)
        results[p] = evaluate(thresholds[p], normal_test, attack_test, p)
    paper = [p for p in results if p in PARAMS]     # Table III parameters
    # AUC is compared as the tables report it, to two decimals, so
    # parameters that tie there are all returned (e.g. the Controller's
    # DISK Read and I/O Read, both 0.99)
    best_auc = max(round(results[p]["AUC"], 2) for p in paper)
    indicators = [p for p in paper
                  if round(results[p]["AUC"], 2) == best_auc]
    return thresholds, results, indicators


def build(args):
    normal = load_rows(args.normal)[args.trim_head:]
    attack = load_rows(args.attack)[args.trim_head:]
    if args.trim_tail:
        attack = attack[:-args.trim_tail]
    if len(normal) < 2 or not attack:
        sys.exit("not enough data after trimming")

    if args.normal_test:
        # the split is given: --normal is the sample the thresholds are
        # derived from, --normal-test the unseen normal instances
        sample, normal_test = normal, load_rows(args.normal_test)
    else:
        # split normal into sample (threshold derivation) and unseen
        # test; per the paper's Table II the normal test set matches the
        # attack set in size
        k = args.test_rows or min(len(attack), len(normal) // 2)
        sample, normal_test = normal[:-k], normal[-k:]

    thresholds, results, indicators = build_rds(
        sample, normal_test, attack, args.three_sigma)

    comp = args.component
    kind = "three-sigma" if args.three_sigma else "normal-average"
    print(f"component: {comp}   thresholds: {kind}")
    print(f"normal sample {len(sample)}, normal test {len(normal_test)}, "
          f"attack test {len(attack)}")
    print(f"{'Parameter':<18}{'Threshold':>18}{'ACC':>6}{'AUC':>6}"
          f"{'TN':>6}{'FP':>6}{'FN':>6}{'TP':>6}")
    for p, m in results.items():
        print(f"{p:<18}{thresholds[p]:>18,.2f}{m['ACC']:>6.2f}"
              f"{m['AUC']:>6.2f}{m['TN']:>6.2f}{m['FP']:>6.2f}"
              f"{m['FN']:>6.2f}{m['TP']:>6.2f}")
    print(f"selected indicator(s) by AUC: {', '.join(indicators)}")

    if args.out:
        out = {"_selected_indicators": {comp: indicators},
               "thresholds": {comp: thresholds}}
        Path(args.out).write_text(json.dumps(out, indent=2))
        print(f"wrote {args.out}")


def detect(args):
    cfg = json.loads(Path(args.config).read_text())
    thresholds = cfg["thresholds"][args.component]
    params = [args.parameter] if args.parameter else \
        cfg.get("_selected_indicators", {}).get(args.component,
                                                list(thresholds))
    rows = load_rows(args.input)
    alerts = 0
    for i, r in enumerate(rows, 1):
        over = [p for p in params
                if p in r and r[p] > thresholds[p]]
        if over:
            alerts += 1
            detail = ", ".join(f"{p}={r[p]:,.2f}>" f"{thresholds[p]:,.2f}"
                               for p in over)
            print(f"row {i}: ATTACK ({detail})")
    print(f"{alerts}/{len(rows)} samples flagged as attack "
          f"({args.component}, indicator(s): {', '.join(params)})")


def _clock(row):
    h, m, s = row["_time"].split(":")
    return int(h) * 3600 + int(m) * 60 + int(float(s))


def split_runs(rows):
    """Group attack samples into runs by their `run` column.

    A file without that column is taken as one run, so the samples of a
    single attack (from its first to its last attack sample) can be
    passed as they are.
    """
    runs = {}
    for r in rows:
        runs.setdefault(r.get("_run", ""), []).append(r)
    return list(runs.values())


def time_runs(runs, threshold, param):
    """Per run: seconds until `param` first exceeds `threshold`
    (None if it never does), attack length by the time stamps, and
    attack length by sample count.

    Time differences are taken between time-of-day stamps and wrap at
    midnight, as in the original analysis. When the machine's clock is
    set during a run the stamped length is off by the size of that
    step; the sample count is not.
    """
    out = []
    for run in runs:
        t0 = _clock(run[0])
        delay = next(((_clock(r) - t0) % DAY for r in run
                      if r[param] > threshold), None)
        out.append((delay, (_clock(run[-1]) - t0) % DAY, len(run) - 1))
    return out


def timing(args):
    cfg = json.loads(Path(args.config).read_text())
    thresholds = cfg["thresholds"][args.component]
    runs = [run for path in args.attack
            for run in split_runs(load_rows(path))]
    if not runs or "_time" not in runs[0][0]:
        sys.exit("timing needs attack samples with a time column")
    if args.parameter:
        params = [args.parameter]
    elif args.all_parameters:
        params = [p for p in params_of(runs[0]) if p in thresholds]
    else:
        params = cfg.get("_selected_indicators", {}).get(
            args.component, list(thresholds))

    first = time_runs(runs, thresholds[params[0]], params[0])
    print(f"component: {args.component}   attack runs: {len(runs)}")
    print(f"avg attack duration: {mean([d for _, d, _ in first]):,.2f} s "
          f"by time stamps, {mean([n for _, _, n in first]):,.2f} s "
          f"by sample count")
    print(f"{'Parameter':<18}{'Threshold':>18}{'Detected':>10}"
          f"{'Avg. time to detect (s)':>25}")
    for p in params:
        delays = [d for d, _, _ in time_runs(runs, thresholds[p], p)
                  if d is not None]
        avg = f"{mean(delays):.3f}" if delays else "-"
        print(f"{p:<18}{thresholds[p]:>18,.2f}"
              f"{f'{len(delays)}/{len(runs)}':>10}{avg:>25}")


def main():
    ap = argparse.ArgumentParser(
        description="Threshold-based Ransomware Detection System")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="derive thresholds and pick indicator")
    b.add_argument("--normal", required=True)
    b.add_argument("--attack", required=True)
    b.add_argument("--normal-test",
                   help="unseen normal test sample; when given, --normal "
                        "is used whole to derive the thresholds")
    b.add_argument("--component", default="component")
    b.add_argument("--test-rows", type=int,
                   help="normal rows held out for testing "
                        "(default: min(len(attack), half of normal))")
    b.add_argument("--three-sigma", action="store_true",
                   help="use mean + 3*std thresholds (Table VII baseline)")
    b.add_argument("--trim-head", type=int, default=0)
    b.add_argument("--trim-tail", type=int, default=0)
    b.add_argument("--out")
    b.set_defaults(func=build)

    d = sub.add_parser("detect", help="run detection with saved thresholds")
    d.add_argument("--config", required=True)
    d.add_argument("--component", required=True)
    d.add_argument("--input", required=True)
    d.add_argument("--parameter",
                   help="override the configured indicator parameter")
    d.set_defaults(func=detect)

    t = sub.add_parser("timing",
                       help="time to detect and attack duration per run")
    t.add_argument("--config", required=True)
    t.add_argument("--component", required=True,
                   help="name of the threshold set in the config")
    t.add_argument("--attack", required=True, nargs="+",
                   help="attack samples; runs are told apart by the "
                        "`run` column")
    t.add_argument("--parameter",
                   help="override the configured indicator parameter")
    t.add_argument("--all-parameters", action="store_true",
                   help="report every parameter that has a threshold")
    t.set_defaults(func=timing)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
