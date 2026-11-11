# Chapter 4 — Threshold-Based Ransomware Detection

Reproduces the Chapter 4 evaluation of threshold-based ransomware
detection built on host resource monitoring: CPU, memory, disk, and I/O
metrics collected with [Dstat](https://github.com/dstat-real/dstat).
Published as: P. Roemsri, S. Puangpontip, R. Hewett, "On Detecting
Crypto Ransomware Attacks: Can Simple Strategies be Effective?",
ICICT 2023, [DOI 10.1109/ICICT58900.2023.00030](https://doi.org/10.1109/ICICT58900.2023.00030).

## Data

`data/` holds the Dstat-derived measurement and analysis workbooks from
the original experiments (the author's own testbed data, redistributed
directly):

- `compare.xlsx` — resource metrics for the three monitored machines,
  one sheet each: **Client**, **Controller**, **DB server**.
- `80_NormalvsNormalAttack.xlsx` — normal vs. under-attack comparison
  (sheet "All").
- `Book1.xlsx`, `Book1-KURO.xlsx`, `Book2.xlsx`, `Book3.xlsx` — working
  books of the measurement rounds.

## Layout

- `code/rds.py` — the Ransomware Detection System, a faithful
  implementation of the dissertation's pseudocode (Algorithm
  *Building-RDS*, Fig. 1 of the paper): thresholds are the average of
  each Dstat parameter over a normal-operation sample; each parameter
  is evaluated on held-out normal + attack data (ACC, AUC, TN/FP/FN/TP
  as fractions, as in Tables IV–VI); the parameter with the best AUC
  becomes the component's indicator; detection alerts when an incoming
  value exceeds the indicator's threshold. `--three-sigma` reproduces
  the Table VII baseline (mean + 3·std, CPU capped at 100).
- `config/thresholds.json` — the original thresholds at full precision,
  extracted from the analysis workbook (`data/compare.xlsx`); they match
  the paper's Table III, with the selected indicators per component
  (Client: DISK Read; Controller: DISK Read / I/O Read; DB server:
  MEMORY Usage) and the dissertation's additional Power Consumption
  parameter.
- `data/` — the original Dstat-derived measurement/analysis workbooks
  (above), the record behind Tables III–VII.
- `data-prep/` — not needed: `rds.py` reads raw `dstat --output` CSVs
  directly (it also accepts plain CSVs with the Table I column names).

## How to run

```bash
# derive thresholds + pick an indicator from your own monitoring data
python code/rds.py build --normal normal.csv --attack attack.csv \
    --component Client --out my_thresholds.json
python code/rds.py build ... --three-sigma     # Table VII baseline

# run detection with the published thresholds
python code/rds.py detect --config config/thresholds.json \
    --component Client --input monitoring.csv
```

Inputs are Dstat CSVs (`dstat -tcmdr --output file.csv` or equivalent)
covering the paper's parameters: cpu.usr, mem.used, dsk.read, dsk.writ,
io.read, io.writ.

## Status

✅ Detector implemented from the dissertation's pseudocode and smoke-
tested (build, three-sigma baseline, and detect). The published
thresholds ship in `config/` at full precision. ⚠️ The raw 20-hour
Dstat recordings behind Tables II–VII were not preserved, so the exact
published metrics cannot be re-derived from raw data; the workbooks in
`data/` remain the record of that analysis, and the pipeline reruns
end-to-end on newly collected monitoring data.
