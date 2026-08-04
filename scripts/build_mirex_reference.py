#!/usr/bin/env python3
"""Build the MIREX reference annotations from the 40 lab annotators' taps.

For each of the 20 MIREX excerpts, the MIREX 2006 beat-tracking training set
gives one line of tap times per lab annotator. Each annotator's taps are
treated as one trial and go through the same Stage 2 cleaning and KDE and the
same Stage 4 optimizer as the crowd taps, with the settings in
`config/canonical240.json`. The resulting beats are the MIREX references in
the listening experiment (paper §2.2), and the files that the MIREX entries
of `config/gt_source_map_canonical240.json` point at.

Input:  `train{1..20}.txt` from the MIREX 2006 training set, one annotator per
        line (default `${PROJECT_ROOT}/mirex_40_annotators/train/`).
Output: `${PROJECT_ROOT}/outputs/canonical240/mirex_reference/train{1..20}.beats`

Usage:
    export PROJECT_ROOT=/path/to/your/data/tree
    python scripts/build_mirex_reference.py
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent  # companion_repo/
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "scripts"))
sys.path.insert(0, str(HERE / "optimization"))

from lib.paths import load_config  # noqa: E402
from repp_gt_alignment_pipeline import clean_taps_trial, gaussian_kde, kde_peaks  # noqa: E402

_spec = importlib.util.spec_from_file_location("stage4", HERE / "pipeline" / "4_run_crowd_gs.py")
stage4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage4)

STEMS = [f"train{i}" for i in range(1, 21)]


def load_annotators(path: Path, w0: float, w1: float) -> list[np.ndarray]:
    """One array of tap times per annotator, rounded to 1 ms, inside [w0, w1]."""
    seqs = []
    for line in path.read_text().splitlines():
        vals = [float(x) for x in line.replace(",", " ").split() if x.strip()]
        taps = np.array(sorted(set(round(v, 3) for v in vals)))
        taps = taps[(taps >= w0) & (taps <= w1)]
        if taps.size >= 3:
            seqs.append(taps)
    return seqs


def consensus(path: Path, cfg: dict, mm_beats: np.ndarray) -> np.ndarray:
    align = cfg["alignment"]
    w0, w1 = cfg["optimizer_window"]["w0"], cfg["optimizer_window"]["w1"]
    pool = []
    for taps in load_annotators(path, w0, w1):
        clean, _ = clean_taps_trial(taps, w0, w1, None, 0.0, align["mad_threshold"],
                                    skip_tempo_gate=True)
        if clean.size >= 3:
            pool.append(clean)
    t_grid, y = gaussian_kde(np.concatenate(pool), w0, w1,
                             align["kde_bandwidth_ms"], align["kde_dt_s"])
    peaks = np.sort(kde_peaks(t_grid, y, align["kde_dt_s"], align["peak_prominence"],
                              align["peak_distance_s"], align["peak_width_s"]))
    diag = stage4.run_crowd_gs(path.stem, peaks, mm_beats)
    return np.sort(np.asarray(diag.get("crowd_beats", [])))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=str(HERE / "config" / "canonical240.json"))
    ap.add_argument("--annotator_dir", default=None,
                    help="Folder with train{1..20}.txt (default "
                         "${PROJECT_ROOT}/mirex_40_annotators/train)")
    ap.add_argument("--out_dir", default=None,
                    help="Default ${PROJECT_ROOT}/outputs/canonical240/mirex_reference")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if "${" in str(cfg["data_root"]):
        raise SystemExit("Set PROJECT_ROOT to the data tree (see README §2).")
    data_root = Path(cfg["data_root"])
    ann_dir = Path(args.annotator_dir or data_root / "mirex_40_annotators" / "train")
    out_dir = Path(args.out_dir or data_root / cfg["outputs_root"] / "mirex_reference")
    out_dir.mkdir(parents=True, exist_ok=True)

    madmom = stage4.load_madmom_by_stem(
        HERE / "data" / "stage_inputs" / "canonical240" / "algorithm_beats.csv")
    for stem in STEMS:
        beats = consensus(ann_dir / f"{stem}.txt", cfg, madmom.get(stem, np.array([])))
        np.savetxt(out_dir / f"{stem}.beats", beats)
        print(f"{stem}: {beats.size} beats")
    print(f"Wrote {len(STEMS)} files to {out_dir}")


if __name__ == "__main__":
    main()
