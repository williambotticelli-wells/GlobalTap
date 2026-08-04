#!/usr/bin/env python3
"""Reproduce the pre-grid KDE-reference alignment (paper §3.1).

For each of the 200 reference-paired validation excerpts: the share of the
released Stage 2 KDE peaks (`data/stage_inputs/canonical240/cleaned_kde_peaks.csv`)
within 70 ms of the nearest reference beat, using the references listed in
`config/gt_source_map_canonical240.json` (for MIREX, the output of
`scripts/build_mirex_reference.py`). Distances are rounded to the microsecond,
and peaks exactly 70 ms from a beat count as hits, as in mir_eval.

Usage:
    export PROJECT_ROOT=/path/to/your/data/tree
    python supplementary_analyses/kde_alignment/reproduce_kde_alignment.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from lib.gt_loader import load_gt_for_stem  # noqa: E402
from lib.paths import load_config  # noqa: E402

TOL_MS = 70.0
GROUPS = {"ballroom": "Ballroom", "benchmark100": "Mixed corpora", "mirex": "MIREX"}


def nearest_beat_ms(peaks: np.ndarray, beats: np.ndarray) -> np.ndarray:
    d = np.min(np.abs(peaks[:, None] - beats[None, :]), axis=1) * 1000.0
    return np.round(d, 3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(HERE / "per_stem_kde_alignment.csv"))
    args = ap.parse_args()

    cfg = load_config(REPO / "config" / "canonical240.json")
    if "${" in str(cfg["data_root"]):
        raise SystemExit("Set PROJECT_ROOT to the data tree (see README §2).")
    data_root = Path(cfg["data_root"])
    gt_map = json.loads((REPO / "config" / "gt_source_map_canonical240.json").read_text())
    peaks = pd.read_csv(REPO / "data" / "stage_inputs" / "canonical240" / "cleaned_kde_peaks.csv")
    stems = pd.read_csv(REPO / "data" / "per_stem_metrics.csv")
    stems = stems[stems.corpus_group.isin(GROUPS)]
    row_order = {"ballroom": 0, "mirex": 1, "benchmark100": 2}
    stems = stems.assign(o=stems.corpus_group.map(row_order)).sort_values(["o", "_stem"])

    rows = []
    for stem, group in zip(stems._stem, stems.corpus_group):
        p = np.sort(peaks.loc[peaks.stimulus_id == stem, "peak_time_s"].to_numpy(float))
        ref = np.sort(load_gt_for_stem(stem, gt_map, data_root)[:, 0])
        d = nearest_beat_ms(p, ref)
        rows.append({
            "_stem": stem,
            "corpus_group": group,
            "pct_peaks_within_70ms_of_gt": 100.0 * np.mean(d <= TOL_MS),
            "mean_abs_peak_to_gt_ms": float(np.mean(d)),
            "median_abs_peak_to_gt_ms": float(np.median(d)),
        })
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)

    print("| Corpus group | n | Mean % of peaks within 70 ms | Mean abs. peak-to-reference offset (ms) |")
    print("|---|---:|---:|---:|")
    for key, label in GROUPS.items():
        g = out[out.corpus_group == key]
        print(f"| {label} | {len(g)} | {g.pct_peaks_within_70ms_of_gt.mean():.1f} | "
              f"{g.mean_abs_peak_to_gt_ms.mean():.1f} |")
    print(f"| All three | {len(out)} | {out.pct_peaks_within_70ms_of_gt.mean():.1f} | "
          f"{out.mean_abs_peak_to_gt_ms.mean():.1f} |")


if __name__ == "__main__":
    main()
