# Method settings and sensitivity tests

The pipeline uses fixed heuristic settings. They were selected during
development using checks on Ballroom, the mixed corpora, and MIREX, then used
unchanged for every reported analysis, including the GlobalTap benchmark.
Because the same validation corpora informed both development and evaluation,
the sensitivity test below checks how much the output depends on these choices.

The config files record the main settings. Stage 4 reads its window and KDE
settings from the config. Several other optimizer values come from matching
Python constants or function defaults, including some values also written in
the JSON for documentation. The table below lists the values the code uses.
The sensitivity script changes them by passing alternative values directly to
the optimizer.

| Setting | Value | What it does and why it was used |
|---|---:|---|
| KDE grid | 5 ms | Computational resolution well below the 70-ms evaluation tolerance. |
| KDE bandwidth | 80 ms | Favored overall in an earlier 50/80/120-ms cross-corpus comparison. A broader 40–160-ms check found relatively stable period and beat-count behavior around 70–100 ms. |
| Trial-level MAD filter | 3.5 scaled MADs, up to 3 passes | In a 100-excerpt test, enabling or disabling MAD cleaning changed post-optimizer mean F-measure by at most 1 percentage point, with no consistent direction across tolerances. A separate check on 10 difficult excerpts produced the same mean agreement at factors 3.5 and 4.5, so 3.5 was not uniquely best. |
| Peak prominence | 0.10 of maximum | Selected with the distance and cleaning settings in a 24-condition development test. The leading prominence values performed similarly. |
| Minimum peak distance | 150 ms | Included in the 24-condition test. This choice had little effect because prominent peaks were already more than 200 ms apart. |
| Period search | 0.28–1.25 s | Bounds the fitted near-isochronous grid to 48–214 BPM. |
| Period/phase search | 120 / 240 steps | Provides fixed finite resolution before local refinement. |
| Density/coverage weight | 1.0 / 0.5 | Balances support at grid beats with coverage of extracted peaks. |
| Peak-match tolerance | 0.12T + 20 ms | Scales matching tolerance with the candidate period while retaining a small fixed allowance. |
| Merge / insert thresholds | 0.6T / 1.4T | Removes close duplicates and fills large gaps in the near-isochronous grid. |
| Bimodal gap threshold | 0.10T | Triggers comparison of two offset phase families when inter-peak intervals separate. |

The rows above summarize the bandwidth comparison, the peak and cleaning test,
and the MAD-filter test. The remaining optimizer values were set during
development.

To test their effect, we changed each final-grid setting to one lower and one
higher value across all 240 validation excerpts. The Stage-2 peaks and all
other settings stayed fixed:

| Setting | Paper setting | Values tested |
|---|---:|---:|
| Period-grid steps | 120 | 80, 160 |
| Phase-grid steps | 240 | 160, 320 |
| Peak-fit weight | 0.5 | 0.25, 0.75 |
| Snap weight | 0.45 | 0.25, 0.65 |
| Snap-max fraction (of T) | 0.12 | 0.08, 0.16 |
| Bimodal gap threshold (of T) | 0.10 | 0.08, 0.12 |
| Minimum IOI bound | 0.28 s | 0.23 s, 0.33 s |

Agreement with the paper's output remained high (mean F-measure .947--1.000,
with the tactus unchanged in 92.1--100% of cases).
Changing the bimodality and snapping settings had almost no effect. Period-grid
resolution, period bounds, and peak fit weight produced the largest changes.
Mean agreement with corpus references changed by -.014 to +.012. Results and
the script are in `parameter_sensitivity/`.

## Released optimizer: implementation overview

This section is an overview of the operations `crowd_gs` performs.

Entry point: `pipeline/4_run_crowd_gs.py`, which wraps `optimize_beats` so
that `method="grid_search"` is supplied, installs that wrapper into the
cascade module, and then calls `run_cascade` in
`optimization/run_pipeline.py`. `optimize_beats` in
`optimization/optimization_regularize.py` therefore dispatches to
`optimize_beats_grid_search`.

**Scoring density** (`build_kde`). The density used for scoring is rebuilt
inside the optimizer from the extracted peak times: one unit Gaussian per peak
at the 80-ms bandwidth on the 5-ms grid, divided by the peak count. Peak
amplitudes from the pooled tap density are not carried forward.

**Search and refinement** (`optimize_beats_grid_search`, `_grid_score`,
`refine_period_ls`). S(T, φ) = D̄ + 0.5C is evaluated over 120 periods by 240
phases, with C at tolerance 0.12T + 20 ms. The winner is refined by least
squares on peaks within 0.15T, after which the phase is re-searched over up to
80 valid candidates spanning ±0.1T; candidates falling outside the permitted
phase range are dropped.

**Partial snapping** (`optimize_beats_grid_search`, step 4). A beat whose
nearest peak lies within 0.12T moves 45% of the distance toward that peak,
hard-capped at 0.12T. Another pass follows in which any beat whose preceding
interval deviates from the median interval by more than 24% in relative terms
reverts to its fitted grid position.

**Post-processing**, applied in this order: `_remove_doublets`,
`metrical_subdivide`, `_remove_doublets`, `_fill_gaps`.

- `_remove_doublets` drops one member of any pair closer than 0.60 times the
  median interval, keeping the member with the higher density value.
- `metrical_subdivide` subdivides by a factor of two only when all of the
  following hold: at least four beats and four peaks; half the period at or
  above the minimum inter-onset interval; more than 55% of midpoints carrying a
  peak within 0.18P; and mean density at midpoints above 0.40 of mean density
  at beats. When it applies, `_equalize_beats` runs up to ten iterations,
  stopping early once the largest shift falls below 0.1 ms, blending each
  interior beat 30% toward the position that would equalize its neighbouring
  intervals, damped where local density is high.
- `_fill_gaps` inserts `max(1, round(gap/P) - 1)` beats into any gap wider than
  1.4 times the median interval, provided the resulting spacing stays at or
  above 0.75P, and then extends both edges to the window boundaries at the
  median interval with no density test. This edge extension is part of every
  run and is independent of the grid-extension step below.

**Candidate selection** (`score_result` in `optimization/run_pipeline.py`).
S ranks periods and phases within a single fit. The choice among the standard
fit, the two single-phase fits after a bimodal split, and the balanced-weight
refit uses a different criterion: 2C + max(0, 1 - CV) + 0.5D̄, with C at
tolerance 0.12P + 30 ms. The unsplit candidate remains eligible. This is a
different rule from S rather than a refinement of it.

**Grid extension** (`_confident_grid_extension`, then `run_cascade`). Two
layers. The helper refits period and phase by least squares on a run of at
least six beats, selected using both its length and its interval regularity,
and stamps a pure grid across the
window, using no density for placement or for its own scoring, and proposes
that grid only if it covers the input peaks at least 75% as well as the beats
it would replace. The cascade then accepts the proposal only if its composite
score under the selection rule above, which does include density, is at least
95% of the pre-extension score.

**Balanced-weight refit.** The weights this branch passes are not consumed by
the grid-search estimator, so when it is reached it reproduces the standard
fit.
