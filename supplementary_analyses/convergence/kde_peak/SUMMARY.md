# Validated GlobalTap consensus convergence

- Stems: 200.
- Median usable tappers per stem: 117 (range 114--120).
- Each tapper contributes a normalized smoothed tap density, so prolific tappers do not receive more weight.
- Primary curve compares random N-tapper consensuses with the full available consensus. An independent N-vs-N curve checks overlap optimism.
- Confidence intervals bootstrap stems, not repeated subsamples.
- Smallest tested N with mean peak F-measure >= .90: 30.
- Smallest tested N with mean density correlation >= .90: 40.
- The full consensus pools all available tappers (114--120 per stem, median 117), more than any subsample tested, so it is at least as stable as the largest tested point (N=90) suggests.

These thresholds describe this corpus, preprocessing, and metric. They are not universal power guarantees.
