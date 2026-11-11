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
  - `ML-KFold_without_name-10-10-9_dataset-*.ipynb` — one notebook per
    ML classifier under k-fold evaluation (BNB/CNB/GNB/MNB naive Bayes
    variants, SVM, decision tree `DS`, extra trees `ET`, random forest
    `RF`; the `no-bias` set is run on the bias-corrected dataset).
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

✅ Original notebooks and datasets migrated as-is from the experiment
folder. ✅ Verified to execute end-to-end on the committed data under
the pinned environment (Python 3.12, repository `requirements.txt`):
`Jaccard_index-9.ipynb` and `ML-DecisionTreeClassifier_version3.ipynb`.
🚧 Still to confirm: which notebook versions produced the dissertation
numbers (several iterations are kept).
