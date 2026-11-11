# Chapter 2 — Device Identification for IoT Security

Reproduces the Chapter 2 comparison between machine-learning classifiers
and a modified Jaccard similarity baseline for identifying IoT devices
from their protocol behavior.

## Data

All datasets are committed in `code/` as Excel workbooks, side by side
with the notebooks that read them (relative paths are preserved from the
original experiments):

- `dataset_all_original*.xlsx` — the real protocol records, collected
  via SSDP discovery at two sites (`dataset_myroom_*` and
  `dataset_university_*` are the per-site subsets).
- `dataset_all_gen*.xlsx` — the synthetic records generated from
  `db_for_gen.xlsx` / `db_for_gen_ssdp.xlsx`.
- `dataset_jaccard_*.xlsx` — the record sets shaped for the Jaccard
  baseline.

These are the author's own collected/synthesized data (no third-party
dataset is involved), so they are redistributed here directly.

## Layout

- `code/` — Jupyter notebooks for every compared method plus the data
  they read:
  - `Jaccard_index-9.ipynb` — the modified Jaccard similarity baseline
    (latest version; `Jaccard_index.ipynb` and `_old` are earlier).
  - `ML-KFold_without_name-10-10-9_dataset-no-bias_*.ipynb` — **the
    dissertation's ML comparison** (Chapter 2, Table 3): 10-fold
    cross-validation repeated 10 times (mean of 100 folds) on
    `dataset_all_original_ssdp.xlsx` (Data Set 2 — 12,000 records,
    10 attributes) for the chapter's four classifiers: decision tree
    (`no-bias_DS`), CategoricalNB (`no-bias_CNB`), extra trees
    (`no-bias_ET`), and all four including random forest in
    `no-bias_DS_ET_RF_CNB` (switch the `clf =` line inside the k-fold
    loop to pick the classifier).
  - the other `ML-KFold_without_name-10-10-9_dataset-*.ipynb` notebooks
    (BNB/GNB/MNB naive Bayes, SVM/MLP variants, and the unsuffixed
    decision-tree runs) are exploratory experiments that did not enter
    the dissertation.
  - `ML-DecisionTreeClassifier_version1..3.ipynb` — decision-tree runs.
- `data-prep/` — reserved; the synthetic-record generation currently
  lives inside the notebooks that read `db_for_gen*.xlsx`.
- `config/` — reserved; parameters are set inside the notebooks.

## How to run

```bash
cd code
jupyter notebook
```

Open the notebook for the method you want to rerun (see Layout). Every
notebook reads its Excel inputs from the same directory, so no path
configuration is needed. Requires `pandas`, `scikit-learn`, `openpyxl`,
`jupyter` (see the repository-level `requirements.txt`).

## Status

✅ Original notebooks and datasets migrated from the experiment folder.
✅ `Jaccard_index-9.ipynb` verified to execute end-to-end on the
committed data under the pinned environment (Python 3.12, repository
`requirements.txt`), reproducing its stored result (accuracy 1.0 on
`dataset_gen`, 100 sampled records); one line that had lost its newline
in the stored file was restored (the stored outputs show the original
run executed the same two statements). Note the notebook's last edited
state evaluates `dataset_gen` only — the other datasets' entries are
commented out in `list_data`.
⚠️ `ML-DecisionTreeClassifier_version3.ipynb` is kept as a historical
working copy: its last edited state runs `CategoricalNB` (not a decision
tree) on one dataset, and its final summary cell indexes five results —
it fails there, as it also did in the stored original run.
✅ The `no-bias` k-fold set confirmed as the dissertation's Table 3
(10-fold CV × 10 iterations on Data Set 2, 12,000 records): rerunning
all four classifiers under the pinned environment reproduces the
published numbers — decision tree 0.9992 (published 0.9987),
CategoricalNB 0.9993 (0.9990), random forest 0.9960 (0.9965), extra
trees 0.9945 (0.9949) — with fold-level standard deviations in the
published range; the residual differences come from unseeded fold
shuffles.
⚠️ `no-bias_DS_ET_RF_CNB.ipynb` was saved mid-edit: its `list_data`
cell points at the 677-record real set and its summary cells index five
datasets. To reproduce Table 3, run `no-bias_DS` / `no-bias_CNB` /
`no-bias_ET` as committed, and for random forest change the active
`clf =` line in the k-fold loop to `RandomForestClassifier()` (or point
`list_data` at `y` in the combined notebook).
