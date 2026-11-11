#!/usr/bin/env python3
"""Rebuild the Chapter 5 visualization inputs from the CIC IoT Dataset 2022.

Reads the flooding-attack pcaps (CIC IoT Dataset 2022, "6-Attacks/1-Flood",
laid out as <flood-root>/<Device>/<HTTP|TCP|UDP>/<...Flood_N.pcap>) and
produces the three data products the visualization tool consumes:

  data/{HTTP,TCP,UDP}/{Device}.csv              per-packet export
  data_aggregation/{HTTP,TCP,UDP}/{Device}.csv  identical rows collapsed, +size
  data_count/{srcport,fsrcport,length}/{HTTP,TCP,UDP}/{Device}.csv
                                                value,count,round tables

Format notes (reverse-engineered from, and verified against, the original
exports used for the published figures):
  - `time` is the packet timestamp in UTC, second precision.
  - `src`/`dst` are Wireshark's resolved address columns (IP, or vendor-
    resolved MAC for non-IP traffic such as ARP).
  - `srcport`/`dstport` are TCP or UDP ports, 0 for non-TCP/UDP packets.
  - `info` is Wireshark's Info column; "→" is normalized to "->" to match
    the original export.
  - `round` comes from the pcap's _N suffix, `attack_type` from the
    protocol folder.
  - `is_attacker`: "attacker" if src is the flooding host, "victim" if src
    is the device (auto-detected as the attacker's most frequent peer,
    overridable), else "other".
  - aggregation groups fully identical rows, `size` = group size.
  - counts are per (value, round); `fsrcport` keeps ephemeral source
    ports only (srcport >= 1024), dropping portless rows, well-known
    service responses, and DHCP.

Requires tshark (Wireshark) on the PATH or via --tshark.
"""

import argparse
import csv
import subprocess
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

PROTOCOLS = ("HTTP", "TCP", "UDP")
FIELDS = [
    "frame.time_epoch", "_ws.col.def_src", "tcp.srcport", "udp.srcport",
    "_ws.col.def_dst", "tcp.dstport", "udp.dstport", "frame.len",
    "_ws.col.protocol", "_ws.col.info",
]
HEADER = ["time", "src", "srcport", "dst", "dstport", "length",
          "protocols", "info", "round", "attack_type", "is_attacker"]


def tshark_rows(tshark, pcap):
    cmd = [tshark, "-r", str(pcap), "-N", "m", "-T", "fields",
           "-E", "separator=/t"]
    for f in FIELDS:
        cmd += ["-e", f]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace")
    for line in proc.stdout:
        yield line.rstrip("\r\n").split("\t")
    if proc.wait() != 0:
        sys.exit(f"tshark failed on {pcap}")


def port(tcp_val, udp_val):
    return tcp_val or udp_val or "0"


def export_pcap(tshark, pcap, round_name, attack_type):
    """One pcap -> list of unlabeled rows (is_attacker filled in later)."""
    rows = []
    for f in tshark_rows(tshark, pcap):
        (epoch, src, tsp, usp, dst, tdp, udp_, length, proto, info) = f
        t = datetime.fromtimestamp(float(epoch), tz=timezone.utc)
        rows.append([t.strftime("%H:%M:%S"), src, port(tsp, usp), dst,
                     port(tdp, udp_), length, proto,
                     info.replace(" → ", " -> "),
                     round_name, attack_type])
    return rows


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def process(device_dir, proto, out_dir, tshark, attacker_ip, victim_ip):
    pcaps = sorted((device_dir / proto).glob("*.[pP][cC][aA][pP]"))
    if not pcaps:
        return False
    device = device_dir.name

    rows = []
    for pcap in pcaps:
        round_no = pcap.stem.rsplit("_", 1)[-1]
        rows += export_pcap(tshark, pcap, f"round{round_no}", proto)

    victim = victim_ip
    if not victim:
        peers = Counter(r[3] for r in rows if r[1] == attacker_ip)
        if not peers:
            sys.exit(f"{device}/{proto}: no packets from attacker "
                     f"{attacker_ip}; pass --victim-ip explicitly")
        victim = peers.most_common(1)[0][0]
        print(f"  victim auto-detected: {victim}")

    for r in rows:
        r.append("attacker" if r[1] == attacker_ip
                 else "victim" if r[1] == victim else "other")

    write_csv(out_dir / "data" / proto / f"{device}.csv", HEADER, rows)

    groups = OrderedDict()
    for r in rows:
        groups[tuple(r)] = groups.get(tuple(r), 0) + 1
    write_csv(out_dir / "data_aggregation" / proto / f"{device}.csv",
              HEADER + ["size"],
              [list(k) + [n] for k, n in groups.items()])

    counts = {
        "srcport": Counter((r[2], r[8]) for r in rows),
        # filtered source ports: ephemeral (client-side) ports only, which
        # drops portless rows (ARP etc.), well-known service responses
        # (e.g. the victim's port-80 replies) and DHCP
        "fsrcport": Counter((r[2], r[8]) for r in rows
                            if int(r[2]) >= 1024),
        "length": Counter((r[5], r[8]) for r in rows),
    }
    for kind, counter in counts.items():
        table = sorted(((v, n, rnd) for (v, rnd), n in counter.items()),
                       key=lambda x: (int(x[0]), x[2]))
        write_csv(out_dir / "data_count" / kind / proto / f"{device}.csv",
                  ["value", "count", "round"], table)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--flood-root", required=True, type=Path,
                    help="path to the dataset's 6-Attacks/1-Flood folder")
    ap.add_argument("--out", required=True, type=Path,
                    help="output root (the tool's code/ folder)")
    ap.add_argument("--devices", nargs="*",
                    help="device folder names to process (default: all)")
    ap.add_argument("--attacker-ip", default="192.168.137.5",
                    help="flooding host (default: %(default)s)")
    ap.add_argument("--victim-ip",
                    help="device IP; auto-detected per device if omitted")
    ap.add_argument("--tshark", default="tshark",
                    help="path to the tshark executable")
    args = ap.parse_args()

    device_dirs = sorted(d for d in args.flood_root.iterdir() if d.is_dir())
    if args.devices:
        device_dirs = [d for d in device_dirs if d.name in args.devices]
    if not device_dirs:
        sys.exit("no device folders found")

    for device_dir in device_dirs:
        for proto in PROTOCOLS:
            if (device_dir / proto).is_dir():
                print(f"{device_dir.name} / {proto}")
                process(device_dir, proto, args.out, args.tshark,
                        args.attacker_ip, args.victim_ip)


if __name__ == "__main__":
    main()
