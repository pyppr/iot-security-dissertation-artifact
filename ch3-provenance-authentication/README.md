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

- `code/policy/` — the provenance/location-based authentication policy
  engine: `run_resultv3.py` is the latest version (`run_result.py`,
  `#run_resultv0.py`, `#run_resultv1.py` are earlier iterations), plus
  the request data and lookup databases it reads.
- `code/ml/` — the decision-tree baseline:
  `ML-DecisionTreeClassifier.ipynb` and `ML-KFold.ipynb` with their
  workbooks.
- `data-prep/` — reserved; request synthesis artifacts currently live
  with the policy code.
- `config/` — reserved; parameters are constants in the scripts.
- `figures/` — the method and flow diagrams from the underlying
  publication ("Provenance Location-based Authentication in Cloud
  Computing"), for reference against the chapter text.

## How to run

```bash
cd code/policy
python run_resultv3.py      # policy evaluation; writes result.xlsx
                            # (requests only) and result_test.xlsx /
                            # result_test2.xlsx (requests + the policy's
                            # "result" label column)

cd ../ml
cp ../policy/result_test.xlsx result.xlsx   # notebooks read ./result.xlsx
jupyter notebook            # decision-tree comparison notebooks
```

Requires `openpyxl`, `pandas`, `scikit-learn`, `jupyter` (see the
repository-level `requirements.txt`).

**Caveats (inherited from the original experiment folder):**

- The policy scripts load `dataset.xlsx` while the file on disk is
  `DataSet.xlsx` — fine on Windows (case-insensitive), fails on Linux;
  rename or symlink there.
- The ML notebooks load `result.xlsx` and expect it to carry the
  policy's `result` label column — but `run_resultv3.py` writes the
  labeled output to `result_test.xlsx` (its `result.xlsx` holds the
  requests only). Copy `result_test.xlsx` to `code/ml/result.xlsx`
  before running the notebooks, as shown above.

## Status

✅ Policy engine, decision-tree notebooks, and synthesized data migrated
as-is. ✅ Verified end-to-end under the pinned environment (Python 3.12,
repository `requirements.txt`): `run_resultv3.py` runs to completion on
the committed data, and both ML notebooks execute on its labeled output.
🚧 Still to confirm: that `run_resultv3.py` is the exact version behind
the dissertation numbers.
