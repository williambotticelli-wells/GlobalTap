#!/usr/bin/env python3
"""Recompute the structured-divergence columns of the metrical-preference table
(paper §3.6 and A.7).

For each of the 180 excerpts with an expert reference, over the rendered
10–25 s window, using the released annotations (`data/annotations/canonical240/`),
the released Stage 2 KDE peaks (`data/stage_inputs/canonical240/cleaned_kde_peaks.csv`)
and the references listed in `config/gt_source_map_canonical240.json`:

- Period relation: the median Crowd beat interval over the median reference
  beat interval. Matched, half, or double rate when it falls within ±0.15
  octaves of 1×, 2×, or 0.5× (the Crowd at half rate has twice the interval);
  other ratio otherwise.
- Phase offset: the median signed distance from each Crowd beat to the nearest
  reference beat, over the Crowd beats within 150 ms of one (negative: the
  Crowd earlier). On matched-rate excerpts it is consistent at 20 ms or more.
  It is empty when no Crowd beat comes within 150 ms of a reference beat; on
  matched-rate excerpts the Crowd beats then fall between the reference beats,
  and §3.6 counts these as consistent offsets too.
- Bimodal strength: of the intervals between successive peaks, those within
  0.40–0.60 or 1.70–2.30 of the Crowd median beat interval (the larger count),
  over those within 0.85–1.15. Flagged at 0.40 or more; empty with fewer than
  four peaks or no interval in 0.85–1.15.
- F-measure (±70 ms), CMLt and AMLt against the reference, from mir_eval.

Checks each column against `metrical_preference_per_excerpt.csv` and prints
the counts in §3.6.

Usage:
    export PROJECT_ROOT=/path/to/your/data/tree
    python supplementary_analyses/metrical_preference/structured_divergences.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mir_eval
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from lib.gt_loader import load_gt_for_stem  # noqa: E402
from lib.paths import load_config  # noqa: E402

T0, T1 = 10.0, 25.0
F_TOL = 0.07
MATCH_TOL = 0.150
CONSISTENT_MS = 20.0
OCTAVES = 0.15
BIMODAL_MIN = 0.40
COLUMNS = ["n_crowd_beats", "n_gt_beats", "crowd_median_ioi_s", "gt_median_ioi_s",
           "metrical_ratio", "metrical_class", "phase_offset_ms", "phase_async",
           "bimodal_strength", "bimodal_flag", "F", "AMLt", "CMLt"]


def window(t: np.ndarray) -> np.ndarray:
    return t[(t >= T0) & (t <= T1)]


def period_class(ratio: float) -> str:
    lr = np.log2(ratio)
    if abs(lr) < OCTAVES:
        return "tactus_match"
    if abs(lr - 1.0) < OCTAVES:
        return "half_time"
    if abs(lr + 1.0) < OCTAVES:
        return "double_time"
    return "other_flip"


def phase_offset_ms(crowd: np.ndarray, ref: np.ndarray) -> float:
    d = np.array([b - ref[np.argmin(np.abs(b - ref))] for b in crowd])
    d = d[np.abs(d) <= MATCH_TOL]
    return float(np.median(d) * 1000.0) if d.size else float("nan")


def bimodal_strength(peaks: np.ndarray, crowd_ioi: float) -> float:
    if peaks.size < 4:
        return float("nan")
    r = np.diff(peaks) / crowd_ioi
    count = lambda lo, hi: float(np.sum((r > lo) & (r < hi)))
    dominant = count(0.85, 1.15)
    if dominant == 0:
        return float("nan")
    return max(count(0.40, 0.60), count(1.70, 2.30)) / dominant


def main() -> None:
    cfg = load_config(REPO / "config" / "canonical240.json")
    if "${" in str(cfg["data_root"]):
        raise SystemExit("Set PROJECT_ROOT to the data tree (see README §2).")
    data_root = Path(cfg["data_root"])
    gt_map = json.loads((REPO / "config" / "gt_source_map_canonical240.json").read_text())
    peaks = pd.read_csv(REPO / "data" / "stage_inputs" / "canonical240" / "cleaned_kde_peaks.csv")
    released = pd.read_csv(HERE / "metrical_preference_per_excerpt.csv")

    rows = []
    for stem in released._stem:
        crowd = window(np.sort(np.atleast_1d(np.loadtxt(
            REPO / "data" / "annotations" / "canonical240" / f"{stem}.beats"))))
        ref = window(np.sort(load_gt_for_stem(stem, gt_map, data_root)[:, 0]))
        p = window(np.sort(peaks.loc[peaks.stimulus_id == stem, "peak_time_s"].to_numpy(float)))
        crowd_ioi, ref_ioi = float(np.median(np.diff(crowd))), float(np.median(np.diff(ref)))
        ratio = crowd_ioi / ref_ioi
        cls = period_class(ratio)
        phase = phase_offset_ms(crowd, ref)
        bim = bimodal_strength(p, crowd_ioi)
        _, cmlt, _, amlt = mir_eval.beat.continuity(ref, crowd)
        rows.append({
            "_stem": stem,
            "n_crowd_beats": crowd.size,
            "n_gt_beats": ref.size,
            "crowd_median_ioi_s": round(crowd_ioi, 4),
            "gt_median_ioi_s": round(ref_ioi, 4),
            "metrical_ratio": round(ratio, 3),
            "metrical_class": cls,
            "phase_offset_ms": round(phase, 1),
            "phase_async": bool(np.isfinite(phase) and abs(phase) >= CONSISTENT_MS
                                and cls == "tactus_match"),
            "bimodal_strength": round(bim, 3),
            "bimodal_flag": bool(np.isfinite(bim) and bim >= BIMODAL_MIN),
            "F": round(float(mir_eval.beat.f_measure(ref, crowd, f_measure_threshold=F_TOL)), 3),
            "AMLt": round(float(amlt), 3),
            "CMLt": round(float(cmlt), 3),
        })
    out = pd.DataFrame(rows)

    merged = released.merge(out, on="_stem", suffixes=("", "_recomputed"))
    for col in COLUMNS:
        a, b = merged[col], merged[f"{col}_recomputed"]
        if a.dtype.kind in "fi":
            same = np.isclose(a, b, rtol=0, atol=1e-9, equal_nan=True)
        else:
            same = a.astype(str) == b.astype(str)
        print(f"{col}: {int(same.sum())} of {len(merged)} reproduce the released table")

    m = out[out.metrical_class == "tactus_match"]
    between = m.phase_offset_ms.isna()
    earlier = m.phase_async & (m.phase_offset_ms < 0)
    print(f"\nmatched rate {len(m)} of {len(out)}")
    print(f"consistent phase offsets: {int(m.phase_async.sum())} + {int(between.sum())} with the "
          f"Crowd beats between the reference beats = {int(m.phase_async.sum() + between.sum())} "
          f"of {len(m)}; Crowd earlier in {int(earlier.sum())} "
          f"(up to {-m.phase_offset_ms[earlier].min():.0f} ms)")
    n = out.metrical_class.value_counts()
    print(f"other period: {len(out) - len(m)} of {len(out)} ({n['half_time']} half, "
          f"{n['double_time']} double, {n['other_flip']} other)")
    print(f"bimodal pooled tapping: {int(out.bimodal_flag.sum())} of {len(out)}")


if __name__ == "__main__":
    main()
