#!/usr/bin/env python3
"""Regenerate the Chapter 4 tables from the recordings in ../data/dstat.

Runs rds.py's Building-RDS steps on the preserved 80/20 split and prints
the dissertation's tables: data sample sizes (Table II), thresholds
(Table III), per-parameter evaluation for Client, Controller and DB
server (Tables IV-VI), the three-sigma baseline (Table VII) and the Time
Computation table (Table IV.8 of the dissertation).

With --check every number is also compared with the original result
workbooks in ../data/results and with ../config/thresholds.json
(needs openpyxl); the script exits with status 1 if any value differs.

Usage:
  python reproduce_tables.py [--check]
"""

import argparse
import json
import sys
from pathlib import Path

import rds

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dstat"
RESULTS = ROOT / "data" / "results"
CONFIG = ROOT / "config"

# report name, data file stem, result workbook stem
COMPONENTS = [("Client", "client", "Client"),
              ("Controller", "controller", "Controller"),
              ("DB server", "dbserver", "Dbserver")]
PAPER_PARAMS = list(rds.PARAMS)
WORKBOOK_ROW = {"CPU Usage": "CPU consumed by User"}   # other names match
SPEEDS = ("fast", "slow", "all")


def fmt(x):
    return f"{x:,.2f}"


def exact(x):
    """Up to four decimals, so averages ending in 5 show unrounded."""
    return "-" if x is None else f"{x:,.4f}".rstrip("0").rstrip(".")


def table(title, header, rows, widths=(16,), first=40):
    """Print rows under a header; the last width repeats."""
    def line(cells):
        ws = list(widths) + [widths[-1]] * len(cells)
        return f"{cells[0]:<{first}}" + "".join(
            f"{c:>{w}}" for c, w in zip(cells[1:], ws))
    print(f"\n{title}")
    print(line(header))
    for r in rows:
        print(line(r))


def load_split(stem):
    d = DATA / "split" / stem
    return (rds.load_rows(d / "normal_sample.csv.gz"),
            rds.load_rows(d / "normal_test.csv.gz"),
            rds.load_rows(d / "attack_test.csv.gz"))


def load_runs(stem):
    fast = rds.split_runs(rds.load_rows(DATA / "attack" / f"{stem}_fast.csv.gz"))
    slow = rds.split_runs(rds.load_rows(DATA / "attack" / f"{stem}_slow.csv.gz"))
    return {"fast": fast, "slow": slow, "all": fast + slow}


def time_summary(runs, threshold, param):
    """(avg time to detect or None, runs detected, avg duration by time
    stamps, avg duration by sample count)."""
    timed = rds.time_runs(runs, threshold, param)
    delays = [d for d, _, _ in timed if d is not None]
    return (rds.mean(delays) if delays else None, len(delays),
            rds.mean([d for _, d, _ in timed]),
            rds.mean([n for _, _, n in timed]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="compare with the original result workbooks")
    args = ap.parse_args()

    published = json.loads((CONFIG / "thresholds.json").read_text())
    original = json.loads(
        (CONFIG / "thresholds_time_computation.json").read_text())

    avg, sigma, sizes, times = {}, {}, {}, {}
    for name, stem, _ in COMPONENTS:
        sample, normal_test, attack_test = load_split(stem)
        sizes[name] = (len(sample), len(normal_test), len(attack_test))
        avg[name] = rds.build_rds(sample, normal_test, attack_test)
        sigma[name] = rds.build_rds(sample, normal_test, attack_test,
                                    three_sigma=True)
        # uncapped CPU three-sigma value, as the original workbook has it
        xs = [r["CPU Usage"] for r in sample]
        sigma[name][0]["_CPU uncapped"] = rds.mean(xs) + 3 * rds.std(xs)

        runs = load_runs(stem)
        indicator = published["_selected_indicators"][name][0]
        times[name] = {"indicator": indicator}
        for speed in SPEEDS:
            times[name][speed] = {
                "original": time_summary(
                    runs[speed],
                    original["thresholds"][f"{name} ({speed})"][indicator],
                    indicator),
                "table3": time_summary(
                    runs[speed], avg[name][0][indicator], indicator)}

    names = [c[0] for c in COMPONENTS]

    table("Table II. Data sample size of each component type",
          ["Sample size", *names],
          [["Normal sample size", *(f"{sizes[n][0]:,}" for n in names)],
           ["Normal test sample size", *(f"{sizes[n][1]:,}" for n in names)],
           ["Attack test sample size", *(f"{sizes[n][2]:,}" for n in names)],
           ["Total test sample size",
            *(f"{sizes[n][1] + sizes[n][2]:,}" for n in names)]])

    table("Table III. Resulting RDS thresholds",
          ["Parameter", *names],
          [[p, *(fmt(avg[n][0][p]) for n in names)] for p in PAPER_PARAMS],
          widths=(20,), first=16)

    for number, name in zip(("IV", "V", "VI"), names):
        thresholds, results, indicators = avg[name]
        table(f"Table {number}. Parameter thresholds for {name} "
              f"(indicator by AUC: {', '.join(indicators)})",
              ["Parameter", "Threshold", "ACC", "AUC", "TN", "FP", "FN", "TP"],
              [[p, fmt(thresholds[p]),
                *(f"{results[p][m]:.2f}"
                  for m in ("ACC", "AUC", "TN", "FP", "FN", "TP"))]
               for p in PAPER_PARAMS], widths=(20, 7), first=16)

    print("\nTable VII. Results from three-sigma-based threshold")
    print(f"{'':<16}" + "".join(f"{n:^38}" for n in names))
    print(f"{'Parameter':<16}" + f"{'Thres.':>22}{'AUC':>8}{'FN':>8}" * 3)
    for p in PAPER_PARAMS:
        print(f"{p:<16}" + "".join(
            f"{fmt(sigma[n][0][p]):>22}{sigma[n][1][p]['AUC']:>8.2f}"
            f"{sigma[n][1][p]['FN']:>8.2f}" for n in names))

    def time_rows(which):
        rows = [["Indicator name", *(times[n]["indicator"] for n in names)]]
        for speed in SPEEDS:
            rows.append([f"Avg. detected of {speed} attack",
                         *(exact(times[n][speed][which][0])
                           for n in names)])
            rows.append([f"Avg. attacked duration of {speed} attack",
                         *(exact(times[n][speed][which][2]) for n in names)])
        return rows

    table("Time Computation table (seconds) as the original analysis "
          "computed it:\nits thresholds (config/thresholds_time_"
          "computation.json), durations by time stamps",
          ["", *names], time_rows("original"))
    table("Time Computation table (seconds), Table III thresholds, "
          "durations by time stamps",
          ["", *names], time_rows("table3"))
    table("Attack duration by sample count (seconds; one sample per "
          "second,\nindependent of the machines' clocks)",
          ["", *names],
          [[f"Avg. attacked duration of {speed} attack",
            *(exact(times[n][speed]["table3"][3]) for n in names)]
           for speed in SPEEDS])

    if args.check:
        sys.exit(check(published, avg, sigma, sizes, times))


def check(published, avg, sigma, sizes, times):
    """Compare every computed number with the original records."""
    try:
        import openpyxl
    except ImportError:
        print("\n--check needs openpyxl (pip install openpyxl)")
        return 2

    def sheet(folder, book, name):
        wb = openpyxl.load_workbook(RESULTS / folder / f"{book}.xlsx",
                                    read_only=True, data_only=True)
        return {r[0]: r[1:] for r in wb[name].iter_rows(values_only=True)}

    checked, bad = 0, []

    def same(what, mine, theirs):
        nonlocal checked
        checked += 1
        if abs(mine - theirs) > 1e-9 * max(1.0, abs(theirs)):
            bad.append(f"{what}: computed {mine!r}, original {theirs!r}")

    metrics = ("ACC", "AUC", "TN", "FP", "FN", "TP")
    for name, _, book in COMPONENTS:
        t1 = sheet("average-threshold", book, "Table1")
        t2 = sheet("average-threshold", book, "Table2")
        s1 = sheet("three-sigma", book, "Table1")
        same(f"{name} normal sample size", sizes[name][0],
             t2["Normal scenario"][1])
        same(f"{name} normal test size", sizes[name][1],
             t2["Normal scenario"][2])
        same(f"{name} attack test size", sizes[name][2],
             t2["Attack scenario"][2])
        for p in avg[name][0]:
            row = WORKBOOK_ROW.get(p, p)
            same(f"{name} {p} threshold (thresholds.json)", avg[name][0][p],
                 published["thresholds"][name][p])
            same(f"{name} {p} threshold", avg[name][0][p], t1[row][0])
            three = sigma[name][0]["_CPU uncapped" if p == "CPU Usage" else p]
            same(f"{name} {p} three-sigma threshold", three, s1[row][0])
            for i, m in enumerate(metrics, 1):
                same(f"{name} {p} {m}", avg[name][1][p][m], t1[row][i])
                same(f"{name} {p} three-sigma {m}", sigma[name][1][p][m],
                     s1[row][i])
        indicator = times[name]["indicator"]
        for speed, prefix in (("fast", "Fast_"), ("slow", "Slow_"),
                              ("all", "")):
            t4 = sheet("average-threshold", prefix + book, "Table4")
            row = t4[WORKBOOK_ROW.get(indicator, indicator)]
            delay, detected, duration, _ = times[name][speed]["original"]
            same(f"{name} {speed} runs", detected, len(row) - 2)
            same(f"{name} {speed} avg. detected", delay, row[0])
            same(f"{name} {speed} avg. duration", duration, row[1])

    print(f"\ncheck: {checked} values compared with the original result "
          f"workbooks and thresholds.json - "
          + ("all agree" if not bad else f"{len(bad)} differ"))
    for line in bad:
        print("  " + line)
    return 1 if bad else 0


if __name__ == "__main__":
    main()
