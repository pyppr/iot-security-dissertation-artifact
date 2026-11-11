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
io.writ (#requests). Input files are CSVs with those columns (a raw
Dstat --output CSV is accepted: its preamble and two-row header are
detected and flattened). Preprocessing follows the paper: leading (and
for attack data, trailing) rows can be trimmed and missing values are
filled with the most recent preceding value.

As in the paper's Tables IV-VI, TN/FP/FN/TP are reported as fractions
of the whole test sample, ACC = TN + TP, and AUC is the area under the
ROC curve of the single-threshold classifier, i.e. balanced accuracy
(TPR + TNR) / 2 (with the paper's balanced test sets, ACC = AUC).
The --three-sigma option reproduces the Table VII baseline instead:
Threshold(C, p) = mean + 3 * std over the normal sample, with CPU
capped at 100.

Usage:
  rds.py build  --normal normal.csv --attack attack.csv
                [--component NAME] [--test-rows K] [--three-sigma]
                [--trim-head N] [--trim-tail N] [--out thresholds.json]
  rds.py detect --config ../config/thresholds.json --component Client
                --input monitoring.csv [--parameter "DISK Read"]
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PARAMS = {  # report name -> Dstat column (aliases accepted)
    "CPU Usage": ("cpu.usr", "usr"),
    "MEMORY Usage": ("mem.used", "used"),
    "DISK Read": ("dsk.read", "read"),
    "DISK Write": ("dsk.writ", "dsk.write", "writ"),
    "I/O Read": ("io.read",),
    "I/O Write": ("io.writ", "io.write"),
}


def load_rows(path):
    """Read a CSV of Dstat samples -> list of {param: float}.

    Accepts a plain CSV whose header holds the Table I column names, or
    a raw `dstat --output` CSV, whose preamble lines and group-header
    row are skipped and whose group row + column row are flattened
    (e.g. groups "dsk/total" + column "read" -> "dsk.read").
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        raw = [r for r in csv.reader(fh)]
    aliases = {a for names in PARAMS.values() for a in names}
    header_i = None
    for i, row in enumerate(raw):
        cells = [c.strip().strip('"').lower() for c in row]
        if len(row) > 2 and (
                any(c in ("date", "time", "epoch", "system") for c in cells)
                or any(c in aliases for c in cells)):
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
            rows.append(rec)
            prev = rec
    return rows


def _is_num(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def mean(xs):
    return sum(xs) / len(xs)


def std(xs):
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


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


def build(args):
    normal = load_rows(args.normal)[args.trim_head:]
    attack = load_rows(args.attack)[args.trim_head:]
    if args.trim_tail:
        attack = attack[:-args.trim_tail]
    if len(normal) < 2 or not attack:
        sys.exit("not enough data after trimming")

    # split normal into sample (threshold derivation) and unseen test;
    # per the paper's Table II the normal test set matches the attack
    # set in size
    k = args.test_rows or min(len(attack), len(normal) // 2)
    sample, normal_test = normal[:-k], normal[-k:]

    results, thresholds = {}, {}
    for p in PARAMS:
        t = mean([r[p] for r in sample])
        if args.three_sigma:
            t += 3 * std([r[p] for r in sample])
            if p == "CPU Usage":
                t = min(t, 100.0)
        thresholds[p] = t
        results[p] = evaluate(t, normal_test, attack, p)

    best_auc = max(m["AUC"] for m in results.values())
    indicators = [p for p, m in results.items() if m["AUC"] == best_auc]

    comp = args.component
    kind = "three-sigma" if args.three_sigma else "normal-average"
    print(f"component: {comp}   thresholds: {kind}")
    print(f"normal sample {len(sample)}, normal test {len(normal_test)}, "
          f"attack test {len(attack)}")
    print(f"{'Parameter':<14}{'Threshold':>16}{'ACC':>6}{'AUC':>6}"
          f"{'TN':>6}{'FP':>6}{'FN':>6}{'TP':>6}")
    for p, m in results.items():
        print(f"{p:<14}{thresholds[p]:>16,.2f}{m['ACC']:>6.2f}"
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


def main():
    ap = argparse.ArgumentParser(
        description="Threshold-based Ransomware Detection System")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="derive thresholds and pick indicator")
    b.add_argument("--normal", required=True)
    b.add_argument("--attack", required=True)
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

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
