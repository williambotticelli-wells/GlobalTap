# Recruitment-panel tests (final)

- Trials: 23,492; participants: 746; excerpts: 200. (One of the 23,493 usable
  benchmark trials has fewer than three taps after cleaning, too few for a
  period estimate, and drops out here.)
- Per-trial taps were cleaned by the canonical adjacent-IOI MAD filter.
- Omnibus tests residualize outcomes by excerpt, aggregate to the participant level, and permute panel labels across participants.
- These permutation tests condition on the sampled excerpts and leave-panel-out references. They do not propagate excerpt-sampling or reference-estimation uncertainty.
- Full metrical-choice distribution: statistic=7.8471, permutation p=0.0001.
- Joint circular phase: statistic=1.6975, permutation p=0.1516.
- Metrical-choice pairwise post hoc: 9 of 45 panel pairs tie at the FDR-corrected floor q=0.0005; no single pair is resolvable as strongest. See tactus_pairwise_panel_tests.csv for the full pairwise table.
