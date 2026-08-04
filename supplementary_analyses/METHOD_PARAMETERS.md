# Method parameter rationale

The consensus pipeline uses fixed implementation heuristics. Values were
selected during pipeline development using diagnostic checks and sensitivity
analyses on the validation corpora (Ballroom, the mixed corpora, and MIREX),
then held fixed across all reported excerpts and corpora, including the
GlobalTap benchmark. Tuning and evaluation therefore share corpora, which is
why the bounded sensitivity check below matters. The values are not claimed to
be theoretically unique.

The run config records these values, but several Stage-4 micro-parameters are
supplied by matching function defaults rather than dynamically read from the
config. The table reports effective behavior. The bounded check passes
overrides directly to the active grid optimizer.

| Setting | Value | Role and basis |
|---|---:|---|
| KDE grid | 5 ms | Computational resolution well below the 70-ms evaluation tolerance. |
| KDE bandwidth | 80 ms | Favored overall in an earlier 50/80/120-ms cross-corpus comparison. A broader 40–160-ms check found relatively stable period and beat-count behavior around 70–100 ms. |
| Trial-level MAD filter | 3.5 scaled MADs, up to 3 passes | In a 100-excerpt ablation, enabling versus disabling MAD cleaning changed post-optimizer mean F-measure by at most 1 percentage point, without a consistent direction across tolerances. A separate 10-difficult-excerpt check produced identical mean agreement at factors 3.5 and 4.5; 3.5 was not uniquely optimized. |
| Peak prominence | 0.10 of maximum | Selected with the distance and cleaning settings in a 24-cell development sweep; the leading prominence values lay on a shallow performance plateau. |
| Minimum peak distance | 150 ms | Included in the 24-cell sweep; distance values were effectively degenerate because prominent peaks were already more than 200 ms apart. |
| Period search | 0.28–1.25 s | Bounds the fitted near-isochronous grid to 48–214 BPM. |
| Period/phase search | 120 / 240 steps | Provides fixed finite resolution before local refinement. |
| Density/coverage weight | 1.0 / 0.5 | Balances support at grid beats with coverage of extracted peaks. |
| Peak-match tolerance | 0.12T + 20 ms | Scales matching tolerance with the candidate period while retaining a small fixed allowance. |
| Merge / insert thresholds | 0.6T / 1.4T | Removes close duplicates and fills large gaps in the near-isochronous grid. |
| Bimodal gap threshold | 0.10T | Triggers comparison of two offset phase families when inter-peak intervals separate. |

The bandwidth comparison, the peak/cleaning sweep, and the MAD ablation are
documented in the rows above. The remaining
optimizer values were refined through iterative development diagnostics and
are implementation heuristics rather than universal defaults. The table below
reports a bounded one-at-a-time sensitivity check of those remaining
settings.

The check varied each active final-grid setting around the canonical value
across all 240 pipeline excerpts, holding the Stage-2 peaks and other settings
fixed. The seven settings perturbed, each to a lower and a higher value while
the rest stayed at the canonical value above:

| Setting | Canonical | Perturbed to |
|---|---:|---:|
| Period-grid steps | 120 | 80, 160 |
| Phase-grid steps | 240 | 160, 320 |
| Peak-fit weight | 0.5 | 0.25, 0.75 |
| Snap weight | 0.45 | 0.25, 0.65 |
| Snap-max fraction (of T) | 0.12 | 0.08, 0.16 |
| Bimodal gap threshold (of T) | 0.10 | 0.08, 0.12 |
| Minimum IOI bound | 0.28 s | 0.23 s, 0.33 s |

Agreement with the canonical output remained
high (mean F-measure .947--1.000, with the tactus unchanged in 92.1--100% of
cases).
The bimodality and snapping perturbations were nearly invariant. Period-grid
resolution, period bounds, and peak fit weight produced the largest changes.
Mean agreement with corpus references changed by -.014 to +.012, which does
not identify a unique optimum because those references can encode a different
metrical target and the check was retrospective. Aggregate results and the
runner are in `parameter_sensitivity/`.

## Final-grid behavior

Two behaviors of the final-grid stage come from the implementation rather than
the config, and are recorded here because they shape the released grids.

Snapping pulls each beat partway toward its nearest peak rather than onto it.
The shift is 45% of the distance to the peak (`snap_weight`), capped at 0.12 of
the period (`snap_max_frac`), so a beat settles between its fitted position and
the peak. Both values are perturbed in the sensitivity check above, where they
were nearly invariant (`optimization/optimization_regularize.py`).

The grid score S(T, phi) = D-bar + 0.5C ranks periods and phases within a
single fit. Choosing among the fits the cascade can produce -- the standard
fit, the two single-phase-family fits after a bimodal split, and the
balanced-lambda refit above the high-CV threshold -- uses a composite of peak
coverage, isochrony (1 - IOI CV), and KDE density at the beats (`score_result`
in `optimization/run_pipeline.py`). Stage 4 reruns from the bundled inputs, and
`stage4_summary.csv` then lists the branch each excerpt took in its
`crowd_gs_path` column.
