# Chapter 5 — Visualization of Attack Behavior in IoT Network Traffic

Reproduces the Chapter 5 3D visualizations of flooding attacks against
IoT devices, built from the CIC IoT Dataset 2022.

## Data

The **CIC IoT Dataset 2022 is not included in this repository.**
Download it from the original source, the Canadian Institute for
Cybersecurity (University of New Brunswick):

- https://www.unb.ca/cic/datasets/iotdataset-2022.html

[data-prep/](data-prep/) documents the three data products the tool
consumes and how each is derived from the original download. Small
aggregated count data (≈8 MB) is committed in `code/data_count/`; the
multi-gigabyte per-packet exports are not and must be regenerated
locally.

## Layout

- `code/` — the visualization tool: a D3.js (v7 + d3-3d) web app.
  `3d.html` renders the 3D scatter/line plots of flooding attacks per
  device and protocol; `2d.html` renders 2D count comparisons (source
  port, packet length) across capture rounds. `assets/` is the
  Bootstrap "Paper Dashboard 2" template (Creative Tim) the pages are
  styled with; `data_count/` is the committed derived count data.
- `data-prep/` — documentation of the data products and formats
  (preparation scripts to be added; see its README).
- `config/` — device/protocol selections are made in the page UI; kept
  for any future run configurations.
- `figures/` — the reference output figures: the published 3D scatter
  and line plots per device and protocol (TCP/UDP/HTTP flooding against
  the ArloQ camera, Eufy Home Base, HeimVision camera, and Philips Hue
  Bridge), the plot legends, and the tool interface. Rerunning the
  visualization tool should reproduce these.

## How to run

Serve `code/` over HTTP (the pages load CSVs with `d3.csv`, which
browsers block from `file://`):

```bash
cd code
python -m http.server 8000
```

- **2D count plots:** open http://localhost:8000/2d.html — works out of
  the box using the committed `data_count/` data.
- **3D attack plots:** open http://localhost:8000/3d.html — first
  regenerate `data_aggregation/` from the CIC IoT Dataset 2022 download
  with [data-prep/prepare_cic.py](data-prep/prepare_cic.py), writing
  into `code/`.

The pages load D3 from CDNs, so an internet connection is required.

## Status

✅ Complete: the visualization tool runs as committed (`2d.html` out of
the box), and `data-prep/prepare_cic.py` rebuilds every input from the
CIC IoT Dataset 2022 download — verified to reproduce the original
exports (see [data-prep/](data-prep/)), so `3d.html` is rerunnable from
scratch.
