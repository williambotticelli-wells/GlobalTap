# Period-relation and phase analysis

- The period-relation analysis included 23,492 trials. The phase analysis used
  the subset of 11,450 matched-rate trials, broken down by panel in
  `country_phase_circular_summary.csv`.
- Participants: 746
- Stimuli: 200
- Reference: leave-one-country-out, equal country weighting.
- Timing: 2-second REPP marker offset removed before analysis.
- Cleaning: the adjacent-IOI MAD filter used in the paper before period and
  phase extraction.
- Period-relation thresholds were specified before inspecting panel outcomes.

## Primary panel tests

- Full metrical-choice distribution: participant-level residualized permutation p<.001.
- Metrical-choice pairwise comparisons: 9 of 45 panel pairs had the minimum
  FDR-corrected q-value, q=.0005 (most involved Japan or South Africa). See
  `panel_tests/tactus_pairwise_panel_tests.csv`.
- Joint circular phase: participant-level residualized permutation p=.152.
- Phase pairwise comparisons: 2 of 45 panel pairs survived FDR correction
  (JP--MX and BR--JP, both q=.045). Tap timing showed no consistent differences
  across panels overall (p=.152), so the pairwise results provide weak phase
  evidence rather than none. See
  `panel_tests/phase_pairwise_panel_tests.csv`.

The figure is descriptive. Primary inference is produced by `run_panel_tests.py`.
