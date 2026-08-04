# Final consensus-grid reliability

- Subsets are passed through the canonical per-trial MAD cleaning, 5-ms KDE/peak extraction, and canonical Stage-4 grid optimizer.
- The full 746-participant merge is used only for this audit; its de-identified taps are released in `data/taps/`.
- At each N, one disjoint A/B split was evaluated per excerpt. The higher-repetition KDE/peak analysis provides the dense convergence curve.
- Final full-pool grids generated: 200.
- The 200 grids in `full_746/` are byte-identical to the released consensus
  annotations in `data/annotations/globalmood200/`, so the annotations we release
  are the ones evaluated in the paper.

## Subset results

- independent_n_vs_n, N=10: mean F=0.828, matched-rate=0.790, median |phase|=0.021 cycles.
- independent_n_vs_n, N=20: mean F=0.893, matched-rate=0.850, median |phase|=0.016 cycles.
- independent_n_vs_n, N=30: mean F=0.916, matched-rate=0.895, median |phase|=0.012 cycles.
- independent_n_vs_n, N=50: mean F=0.918, matched-rate=0.885, median |phase|=0.009 cycles.
- subsample_vs_full, N=10: mean F=0.878, matched-rate=0.835, median |phase|=0.014 cycles.
- subsample_vs_full, N=20: mean F=0.923, matched-rate=0.877, median |phase|=0.010 cycles.
- subsample_vs_full, N=30: mean F=0.938, matched-rate=0.910, median |phase|=0.008 cycles.
- subsample_vs_full, N=50: mean F=0.951, matched-rate=0.927, median |phase|=0.005 cycles.
