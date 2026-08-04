# Period-relation and phase analysis

- Trials analyzed: 23,492 (of the 23,493 usable benchmark trials; one trial has
  fewer than three taps after cleaning, too few for a period estimate)
- Participants: 746
- Stimuli: 200
- Reference: leave-one-country-out, equal country weighting.
- Timing: 2-second REPP marker offset removed before analysis.
- Cleaning: canonical adjacent-IOI MAD filter before period/phase extraction.
- Period-relation thresholds were specified before inspecting panel outcomes.

## Primary panel tests

- Full metrical-choice distribution: participant-level residualized permutation p<.001.
- Metrical-choice pairwise post hoc: 9 of 45 panel pairs tie at the FDR-corrected
  floor q=.0005 (most involve Japan or South Africa). No single pair is resolvable
  as strongest. See `panel_tests/tactus_pairwise_panel_tests.csv`.
- Joint circular phase: participant-level residualized permutation p=.152.
- Phase pairwise post hoc: 2 of 45 panel pairs survive FDR correction
  (JP--MX and BR--JP, both q=.045). The omnibus test is null, so the phase
  evidence is weak rather than absent. See
  `panel_tests/phase_pairwise_panel_tests.csv`.

The figure is descriptive. Primary inference is produced by `run_panel_tests.py`.
