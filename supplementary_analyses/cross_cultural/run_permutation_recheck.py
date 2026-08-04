#!/usr/bin/env python3
"""Sensitivity check for the panel tests in `run_panel_tests.py`.

`run_panel_tests.py` builds each trial's leave-one-panel-out reference period
and phase, its metrical class, and the matched-rate phase subset once, from
the observed panel labels, then permutes the labels over the resulting
participant vectors. Here the labels are permuted first and everything that
depends on them is rebuilt in each permutation: the reference periods, the
metrical classes, the reference phases, and which trials enter the phase test.
Both versions are run with the same permutations, and the observed statistics
are checked against `panel_tests/omnibus_panel_tests.csv`.

This is not the published analysis. The paper and supplement cite
`run_panel_tests.py` (metrical choice p < .001, phase p = .152) and its pairwise
tests, which were not rerun this way.

Needs the raw tapping export, which is not included. Writes only aggregate
statistics, to `panel_tests/permutation_recheck.csv`.

Usage:
    python supplementary_analyses/cross_cultural/run_permutation_recheck.py
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from pipeline_subset_core import load_and_clean_trials  # noqa: E402
import run_globaltap_phase_periodicity_nested as N  # noqa: E402
from run_panel_tests import DEFAULT_INPUT  # noqa: E402

CATEGORIES = ["double_time", "matched", "half_time", "other", "unclear"]
OUT = HERE / "panel_tests" / "permutation_recheck.csv"


def classify(ratio: np.ndarray) -> np.ndarray:
    out = np.full(ratio.shape, 4, dtype=int)
    fin = np.isfinite(ratio) & (ratio > 0)
    out[fin] = 3
    for k, (_, lo, hi) in enumerate(N.TACTUS_BINS):
        out[fin & (ratio >= lo) & (ratio <= hi)] = k
    return out


def between_panel_stat(pv: np.ndarray, labels: np.ndarray) -> float:
    grand = pv.mean(0)
    tot = 0.0
    for c in np.unique(labels):
        g = pv[labels == c]
        tot += len(g) * float(((g.mean(0) - grand) ** 2).sum())
    return tot


def ref_periods(d: dict, cidx: np.ndarray) -> np.ndarray:
    """Per excerpt and panel: the median of the other panels' median periods
    (at least three panels)."""
    df = pd.DataFrame({"s": d["stim"], "c": cidx, "p": d["period"]})
    M = np.full((d["n_stim"], d["n_c"]), np.nan)
    med = df.dropna(subset=["p"]).groupby(["s", "c"])["p"].median()
    M[med.index.get_level_values(0), med.index.get_level_values(1)] = med.to_numpy()
    ref = np.full_like(M, np.nan)
    for c in range(d["n_c"]):
        others = np.delete(M, c, axis=1)
        ok = np.isfinite(others).sum(1) >= 3
        ref[:, c] = np.nanmedian(np.where(ok[:, None], others, np.nan), axis=1)
    return ref


def metrical_stat(d: dict, cat: np.ndarray, country_of_part: np.ndarray) -> float:
    stim, part, n_stim, n_part = d["stim"], d["part"], d["n_stim"], d["n_part"]
    onehot = np.eye(5)[cat]
    cnt_s = np.bincount(stim, minlength=n_stim)
    mean_s = np.stack([np.bincount(stim, onehot[:, j], n_stim) for j in range(5)], 1) / cnt_s[:, None]
    resid = onehot - mean_s[stim]
    cnt_p = np.bincount(part, minlength=n_part)
    pv = np.stack([np.bincount(part, resid[:, j], n_part) for j in range(5)], 1) / cnt_p[:, None]
    return between_panel_stat(pv, country_of_part)


def metrical_categories(d: dict, cidx: np.ndarray) -> np.ndarray:
    ref = ref_periods(d, cidx)
    return classify(d["period"] / ref[d["stim"], cidx])


def phase_stat(d: dict, country_of_part: np.ndarray):
    cidx = country_of_part[d["part"]]
    ref = ref_periods(d, cidx)
    stim, n_stim, n_c, T, tt = d["stim"], d["n_stim"], d["n_c"], d["T"], d["tap_trial"]
    tap_stim, tap_c = stim[tt], cidx[tt]
    # Reference phase for (excerpt, panel): mean unit vector of the other panels' pooled taps.
    ref_angle = np.full((n_stim, n_c), np.nan)
    key = tap_stim * n_c + tap_c
    with np.errstate(invalid="ignore"):
        for c in range(n_c):
            R = ref[tap_stim, c]
            z = np.exp(2j * np.pi * T / R)
            re = np.bincount(key, z.real, n_stim * n_c).reshape(n_stim, n_c)
            im = np.bincount(key, z.imag, n_stim * n_c).reshape(n_stim, n_c)
            cnt = np.bincount(key, minlength=n_stim * n_c).reshape(n_stim, n_c)
            V = (re + 1j * im) / np.where(cnt > 0, cnt, np.nan)
            good = np.isfinite(V.real) & (np.abs(V) > 0)
            good[:, c] = False
            U = np.where(good, V / np.where(good, np.abs(V), 1), 0)
            k = good.sum(1)
            mean = U.sum(1) / np.where(k > 0, k, 1)
            ref_angle[:, c] = np.where(k > 0, np.angle(mean), np.nan)
    Rt = ref[stim, cidx]
    cat = classify(d["period"] / Rt)
    zt = np.exp(2j * np.pi * T / Rt[tt])
    n = len(stim)
    vre = np.bincount(tt, zt.real, n) / np.where(d["n_taps"] > 0, d["n_taps"], np.nan)
    vim = np.bincount(tt, zt.imag, n) / np.where(d["n_taps"] > 0, d["n_taps"], np.nan)
    vec = vre + 1j * vim
    ang = ref_angle[stim, cidx]
    ok = (cat == 1) & np.isfinite(ang) & np.isfinite(vec.real) & (np.abs(vec) > 0)
    frac = (((np.angle(vec) - ang) + np.pi) % (2 * np.pi) - np.pi) / (2 * np.pi)
    a = frac[ok] * 2 * np.pi
    vals = np.stack([np.sin(a), np.cos(a)], 1)
    s, p = stim[ok], d["part"][ok]
    cnt_s = np.bincount(s, minlength=n_stim)
    ms = np.stack([np.bincount(s, vals[:, j], n_stim) for j in range(2)], 1) / np.where(cnt_s > 0, cnt_s, np.nan)[:, None]
    resid = vals - ms[s]
    cnt_p = np.bincount(p, minlength=d["n_part"])
    keep = cnt_p > 0
    pv = np.stack([np.bincount(p, resid[:, j], d["n_part"]) for j in range(2)], 1)[keep] / cnt_p[keep][:, None]
    labels = country_of_part[keep]
    return between_panel_stat(pv, labels), int(ok.sum()), pv, labels


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--permutations", type=int, default=9999)
    args = ap.parse_args()

    cleaned = load_and_clean_trials(args.input)
    base = cleaned.rename(columns={"stem": "stim_name", "clean_taps": "taps"})
    base = base[["participant_id", "listener_country", "stim_name", "taps"]].reset_index(drop=True)
    period = np.array([N.trial_period(t) for t in base["taps"]], dtype=float)
    stim_codes, stim = np.unique(base["stim_name"], return_inverse=True)
    part_codes, part = np.unique(base["participant_id"], return_inverse=True)
    c_codes, cidx = np.unique(base["listener_country"], return_inverse=True)
    country_of_part = np.zeros(len(part_codes), dtype=int)
    country_of_part[part] = cidx
    if not (country_of_part[part] == cidx).all():
        raise SystemExit("A participant appears in two panels.")
    n_taps = base["taps"].map(len).to_numpy()
    d = dict(period=period, stim=stim, part=part, n_stim=len(stim_codes), n_part=len(part_codes),
             n_c=len(c_codes), n_taps=n_taps,
             T=np.concatenate([np.asarray(t, float) for t in base["taps"]]),
             tap_trial=np.repeat(np.arange(len(base)), n_taps))
    stored = pd.read_csv(HERE / "panel_tests" / "omnibus_panel_tests.csv").set_index("outcome").statistic

    cat_obs = metrical_categories(d, cidx)
    repo = N.build_trial_metrics(base)
    key = ["participant_id", "stim_name"]
    chk = base[key].assign(cat=np.array(CATEGORIES)[cat_obs]).merge(
        repo[key + ["tactus_choice"]], on=key)
    if len(chk) != len(base) or not (chk["cat"] == chk.tactus_choice).all():
        raise SystemExit("Metrical classes differ from build_trial_metrics.")
    m_obs = metrical_stat(d, cat_obs, country_of_part)
    p_obs, n_phase, pv_obs, lab_obs = phase_stat(d, country_of_part)
    for name, value in [("full_metrical_choice", m_obs), ("joint_circular_phase", p_obs)]:
        if not np.isclose(value, stored[name], rtol=1e-9):
            raise SystemExit(f"{name}: {value} differs from the stored {stored[name]}")
    print(f"{len(base)} trials, {n_phase} in the phase test; observed statistics match "
          "omnibus_panel_tests.csv", flush=True)

    n = args.permutations
    rng = np.random.default_rng(20260720)
    fixed = rebuilt = 0
    t0 = time.time()
    for _ in range(n):
        perm = rng.permutation(country_of_part)
        fixed += metrical_stat(d, cat_obs, perm) >= m_obs
        rebuilt += metrical_stat(d, metrical_categories(d, perm[part]), perm) >= m_obs
    rows = [dict(outcome="full_metrical_choice", statistic=m_obs, trials=len(base), permutations=n,
                 seed=20260720, p_fixed_outcomes=(fixed + 1) / (n + 1),
                 p_rebuilt_references=(rebuilt + 1) / (n + 1))]
    print(f"metrical choice: {time.time() - t0:.0f} s", flush=True)

    rng = np.random.default_rng(20260721)
    fixed = rebuilt = 0
    for _ in range(n):
        perm = rng.permutation(country_of_part)
        fixed += between_panel_stat(pv_obs, rng.permutation(lab_obs)) >= p_obs
        rebuilt += phase_stat(d, perm)[0] >= p_obs
    rows.append(dict(outcome="joint_circular_phase", statistic=p_obs, trials=n_phase, permutations=n,
                     seed=20260721, p_fixed_outcomes=(fixed + 1) / (n + 1),
                     p_rebuilt_references=(rebuilt + 1) / (n + 1)))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
