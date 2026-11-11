# Chapter 5 data preparation

The visualization tool in [../code/](../code/) consumes three data
products derived from the **CIC IoT Dataset 2022** flooding-attack
captures (https://www.unb.ca/cic/datasets/iotdataset-2022.html).
One CSV per device per protocol, for 11 devices (ArloQ Camera, Atomi
Coffee Maker, Borun Camera, Eufy Home Base, Globe Lamp, Gosund
Plug - Roomba, HeimVision Camera, Netatmo Camera, Philips Hue Bridge,
Ring Basestation, SimCam) under three attack protocols (HTTP, TCP, UDP),
across three capture rounds (`round1`–`round3`).

## Data products

### 1. `data/{HTTP,TCP,UDP}/{Device}.csv` — per-packet export (~3 GB, not committed)

Packet records exported from the dataset's flooding-attack pcaps, with
attack labeling added:

```
time,src,srcport,dst,dstport,length,protocols,info,round,attack_type,is_attacker
18:51:39,192.168.137.5,64949,192.168.137.249,80,78,TCP,64949 -> 80 [SYN] ...,round1,HTTP,attacker
```

`is_attacker` is one of `attacker`, `victim`, `other`.

### 2. `data_aggregation/{HTTP,TCP,UDP}/{Device}.csv` — aggregated packets (not committed)

Same columns as the per-packet export plus a `size` count column.
**This is the input `3d.html` loads**; it must be regenerated locally
before the 3D plots will render.

### 3. `data_count/{srcport,fsrcport,length}/{HTTP,TCP,UDP}/{Device}.csv` — counts (committed)

Small aggregate counts per value per round, one folder per counted
dimension (source port, filtered source port, packet length):

```
value,count,round
49152,3,round1
```

**This is the input `2d.html` loads.** Because these are small, highly
aggregated statistics (≈8 MB total), they are committed with the tool in
`../code/data_count/` so the 2D comparisons run out of the box.

## Source captures

The flooding-attack pcaps the CSVs derive from (3 rounds per device per
protocol, e.g. `ArloQCamHTTPFlood_1.pcap`) are part of the CIC IoT
Dataset 2022 download. The dataset also provides a feature-extracted
CSV format (the wide CICIoT feature columns); that format is **not**
what the visualization tool reads — the tool's inputs are the packet
lists described above.

## Regenerating from the CIC download

[`prepare_cic.py`](prepare_cic.py) rebuilds all three data products from
the dataset's flooding pcaps. It requires Python 3 and
[tshark](https://www.wireshark.org/) (ships with Wireshark):

```bash
python prepare_cic.py \
  --flood-root "<CIC download>/CICIOT/6-Attacks/1-Flood" \
  --out ../code
```

Options: `--devices` to process a subset, `--attacker-ip` (default
`192.168.137.5`, the flooding host in these captures), `--victim-ip`
(auto-detected per device by default), `--tshark` for an explicit
tshark path. The output lands inside `../code/`, where the pages load
it; `data/` and `data_aggregation/` are gitignored there.

**Verification:** the script's output was diffed against the original
exports used for the published figures (ArloQ Camera, HeimVision
Camera, Philips Hue Bridge — 8 device/protocol files). The per-packet
`data/` export reproduces row-for-row (ports, addresses, lengths,
timestamps, labels identical); the only differences are
Wireshark-version wording changes in the Info column's analysis
annotations (e.g. the original Wireshark printed "[TCP Port numbers
reused]" where current versions do not), which also carry into the
corresponding `data_aggregation` rows. All `srcport` and `length`
count tables reproduce byte-identically, as do 6 of 8 `fsrcport`
tables. The remaining two (HeimVision HTTP and TCP) differ by a single
port entry each — 11 and 1 packets of the camera's periodic discovery
broadcasts, which the original export filtered inconsistently across
files (the same packet class was kept in other files); the script
applies the consistent rule (ephemeral source ports, >= 1024) instead.
