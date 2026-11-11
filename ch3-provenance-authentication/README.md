# Chapter 3 — Provenance/Location-Based Authentication

Reproduces the Chapter 3 comparison between a provenance- and
location-based authentication policy and a decision-tree classifier,
evaluated on 5,000 synthesized authentication requests.

## Data

The synthesized request data is committed in `code/policy/` as Excel/CSV
files next to the code that reads it: `DataSet.xlsx` holds the
synthesized users (fake identities: generated names, emails, passwords,
device MAC addresses, locations), the `db_*.csv` files are the lookup
databases the policy consults, and `data_for_train*.xlsx` /
`result*.xlsx` hold the labeled requests and policy outcomes used to
train and compare against the decision tree. All of it is synthetic —
no real user data.

## Layout

- `code/ml/` — **the dissertation pipeline, self-contained**:
  `run_result.py` is the policy engine behind the chapter's numbers —
  it reads `database.xlsx` (synthesized users) and `dataset.xlsx`
  (5,000 synthesized requests) and writes `result.xlsx` (the requests
  plus the policy's Allow / Allow with condition / Deny label), which
  `ML-DecisionTreeClassifier.ipynb` and `ML-KFold.ipynb` then read for
  the decision-tree comparison.
- `code/policy/` — later development iterations of the policy engine
  (`run_resultv3.py` is the newest: 3,000-request runs on an extended
  schema; `#run_resultv0.py` / `#run_resultv1.py` are earlier), kept as
  history together with the data they read.
- `data-prep/` — reserved; request synthesis artifacts currently live
  with the policy code.
- `config/` — reserved; parameters are constants in the scripts.
- `figures/` — the method and flow diagrams from the underlying
  publication ("Provenance Location-based Authentication in Cloud
  Computing"), for reference against the chapter text.

## How to run

```bash
cd code/ml
python run_result.py        # regenerates result.xlsx — the 5,000
                            # labeled requests behind the chapter
jupyter notebook            # ML-DecisionTreeClassifier / ML-KFold,
                            # both read ./result.xlsx
```

Requires `openpyxl`, `pandas`, `scikit-learn`, `jupyter` (see the
repository-level `requirements.txt`).

**Caveats (inherited from the original experiment folder):**

- The policy scripts load `dataset.xlsx` while the file on disk is
  `DataSet.xlsx` — fine on Windows (case-insensitive), fails on Linux;
  rename or symlink there.
- `run_resultv3.py` (the later iteration in `code/policy/`) writes its
  labeled output to `result_test.xlsx`, not `result.xlsx`, and its
  labels are **not** the chapter's training data — only
  `code/ml/run_result.py` regenerates that.

## Status

✅ Canonical pipeline confirmed by regeneration under the pinned
environment (Python 3.12, repository `requirements.txt`):
`code/ml/run_result.py` reproduces the committed `result.xlsx` — 5,000
rows with identical labels (Allow 3,784 / Allow with condition 100 /
Deny 1,116); the only differences are 511 cells where the committed
original still carries the old "Online transection" spelling that
`dataset.xlsx` has since corrected. Both notebooks rerun on the
committed `result.xlsx` and reproduce their stored accuracies (decision
tree 0.82 stored vs 0.84 rerun; the k-fold folds match closely,
including the low final fold ≈0.64). The later `run_resultv3.py` also
runs end-to-end on its own data.
