# Chapter 4 — Threshold-Based Ransomware Detection

Reproduces the Chapter 4 evaluation of threshold-based ransomware
detection built on host resource monitoring: CPU, memory, disk, and I/O
metrics collected with [Dstat](https://github.com/dstat-real/dstat).
Published as: P. Roemsri, S. Puangpontip, R. Hewett, "On Detecting
Crypto Ransomware Attacks: Can Simple Strategies be Effective?",
ICICT 2023, [DOI 10.1109/ICICT58900.2023.00030](https://doi.org/10.1109/ICICT58900.2023.00030).

Table numbers below are the paper's (I–VII). The dissertation numbers
the same tables IV.1–IV.7 and adds the Time Computation table (IV.8),
which is not in the paper.

## Data

All data is the author's own testbed data (five virtual machines: three
clients, a controller, a database server; recorded February 2022) and
is redistributed directly.

`data/dstat/` holds the Dstat measurements the tables were computed
from, as gzip-compressed CSVs with one sample per second. Columns:
`date` (dd-mm), `time`, the Dstat CPU, memory, disk and I/O columns, a
power estimate (`power est.`, watts), and `is_attacked` (0/1).

- `normal/` — 20 hours of normal operation per machine (5 hours each
  of regular, high-CPU, high-I/O and combined load): `client1`,
  `client2`, `client3`, `controller`, `dbserver`, 72,000 samples each.
- `attack/` — the attack-period samples of the 80 ransomware runs on
  each component: 40 fast (PyCrypto) in `*_fast.csv.gz` and 40 slow
  (PyAES) in `*_slow.csv.gz`. The `run` column numbers the runs 1–40
  within a file. The client attacks were run on client 1.
- `split/<component>/` — the 80/20 split behind Tables II–VII:
  `normal_sample` (the thresholds are its averages), `normal_test` and
  `attack_test`. The original analysis drew this split at random
  without a seed, so the split itself is shipped.

In `attack/controller_slow.csv.gz`, 1,817 rows carry the date as
`2-Oct` instead of `10-02`: a spreadsheet reformatting already present
in the original files, left as it is.

`data/results/` holds the result workbooks of the original analysis
(May 2022), the record the reruns are checked against:
`average-threshold/` for the dissertation's method and `three-sigma/`
for the baseline. In each workbook, sheet `Table1` has the thresholds
and metrics, `Table2` the sample sizes, and `Table3`/`Table4` the
outcome and time to detect for every attack run. `Client`,
`Controller`, `Dbserver` cover fast and slow attacks together; the
`Fast_`/`Slow_` workbooks one attack speed; the `Client1` workbooks
use the normal data of client 1 only.

The workbooks directly in `data/` are earlier working books of the
analysis: `compare.xlsx` (resource metrics for Client, Controller and
DB server, one sheet each), `80_NormalvsNormalAttack.xlsx` (normal vs.
under-attack comparison), and `Book1.xlsx`, `Book1-KURO.xlsx`,
`Book2.xlsx`, `Book3.xlsx` (measurement rounds).

## Layout

- `code/rds.py` — the Ransomware Detection System, a faithful
  implementation of the dissertation's pseudocode (Algorithm
  *Building-RDS*, Fig. 1 of the paper): thresholds are the average of
  each Dstat parameter over a normal-operation sample; each parameter
  is evaluated on held-out normal + attack data (ACC, AUC, TN/FP/FN/TP
  as fractions, as in Tables IV–VI); the parameter with the best AUC
  becomes the component's indicator; detection alerts when an incoming
  value exceeds the indicator's threshold. `--three-sigma` reproduces
  the Table VII baseline (mean + 3·std, CPU capped at 100). `timing`
  reports, for every attack run, the time until the indicator first
  exceeds its threshold and the length of the attack.
- `code/reproduce_tables.py` — regenerates Tables II–VII and the Time
  Computation table from `data/dstat/` in one run; `--check` compares
  every number with `data/results/` and `config/thresholds.json`.
- `config/thresholds.json` — the published thresholds at full
  precision (Table III), with the selected indicators per component
  (Client: DISK Read; Controller: DISK Read / I/O Read; DB server:
  MEMORY Usage) and the additional Power Consumption parameter.
- `config/thresholds_time_computation.json` — the thresholds the
  original analysis used for the Time Computation table (see Status).
- `data-prep/export_dstat_csv.py` — provenance: how `data/dstat/` was
  exported from the original analysis workbooks (about 1.5 GB as
  `.xlsx`, not shipped) and how the attack runs were numbered.

## How to run

```bash
cd ch4-ransomware-detection

# every table, compared with the original results
python code/reproduce_tables.py --check

# one component, step by step (Table IV; add --three-sigma for Table VII)
python code/rds.py build --component Client \
    --normal      data/dstat/split/client/normal_sample.csv.gz \
    --normal-test data/dstat/split/client/normal_test.csv.gz \
    --attack      data/dstat/split/client/attack_test.csv.gz

# time to detect and attack duration per run
python code/rds.py timing --config config/thresholds.json \
    --component Client --attack data/dstat/attack/client_fast.csv.gz

# run detection with the published thresholds
python code/rds.py detect --config config/thresholds.json \
    --component Client --input data/dstat/attack/client_fast.csv.gz
```

`rds.py` needs only the Python standard library; `--check` and the
export script need `openpyxl` / `pandas` (repository `requirements.txt`).

To build an RDS from your own monitoring data, pass Dstat CSVs
(`dstat -tcmdr --output file.csv` or equivalent) covering cpu.usr,
mem.used, dsk.read, dsk.writ, io.read, io.writ. Without
`--normal-test`, `build` holds out the last rows of `--normal` as the
unseen normal test sample.

## Status

✅ Tables III–VII rerun from the shipped data and agree with the
original results: `reproduce_tables.py --check` compares 351 values
(thresholds, metrics, sample sizes, timings) with the original result
workbooks and `config/thresholds.json`, and all agree to floating-point
precision. At the printed precision they equal the tables in the paper
and the dissertation, including the selected indicators, with the
differences listed here:

- **Table II.** The test sample sizes (32,512 / 14,365 / 8,258) match.
  The normal sample sizes of the preserved split are 172,553 / 57,635 /
  57,712; the table prints 172,975 / 57,831 / 57,608. The preserved
  split is the one the published thresholds were computed from (it
  reproduces Table III exactly).
- **Last printed digit.** Of the 198 numbers printed in Tables III–VII,
  195 are the computed values rounded as printed. The Controller's
  MEMORY Usage threshold is 1,152.66M (printed 1,152.67M in Tables III
  and V), and its three-sigma threshold for I/O Read is 19.55 (printed
  19.60 in Table VII).
- **Time Computation table (dissertation IV.8), times to detect.** The
  original analysis timed each attack subset with thresholds from that
  subset's own random split, and the Client subsets with the normal
  data of client 1 only (`config/thresholds_time_computation.json`).
  With those thresholds its results are reproduced exactly (Client:
  0.18 / 0.28 / 0.23 s for fast / slow / all attacks). With the
  Table III thresholds the Client's values are 0.23 / 0.30 / 0.26 s;
  Controller and DB server are the same either way.
- **Time Computation table, attack durations.** Two measures are
  printed by `rds.py timing` and `reproduce_tables.py`. The original
  analysis took the difference between the time-of-day stamps of a
  run's first and last attack sample. The DB server VM was restored
  from a snapshot before each run, so its clock restarts from the
  snapshot's time and later steps forward to the current time; in 16
  of the 40 slow runs that step falls inside the attack, so those
  stamps span hours while every slow run holds only 890–1,296
  one-second samples. For the DB server the sample count is therefore
  the attack's length: 1,034.20 s on average for the slow attack
  (about 17 minutes; 13,293.93 s by time stamps) and 520.35 s for all
  attacks (6,650.21 s by time stamps). Elsewhere the two measures
  differ by at most 1.2%. The times to detect are not affected (0 s
  for the DB server's indicator).

⚠️ `data/dstat/` holds every sample the analysis used, after the
original cleaning (missing values filled; for the attack runs, only the
samples of the attack period). The per-run raw log folders of the
experiments are not included.
