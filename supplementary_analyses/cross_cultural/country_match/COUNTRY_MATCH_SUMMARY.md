# Own-country tapping coherence

Does tapping coherence (ISTC) rise when an excerpt's source country matches
the panel that tapped it? The main paper reports the primary test in §3.5.

- Design: the five source countries with 20 benchmark excerpts each
  (US, KR, FR, MX, EG), giving 100 excerpts and 1,000
  excerpt-by-panel cells, 100 of them source-matched.
- ISTC is computed per cell with equal-N subsampling (7 tappers per cell,
  500 draws) so that cell sizes cannot drive the comparison.
- Primary model: `istc ~ source_match + C(excerpt) + C(panel)`, standard
  errors clustered by excerpt.

## Primary result

- Match effect **+0.066 ISTC units**, 95% CI [-0.030, +0.161],
  two-sided p=.179 (`balanced_five_fixed_effect_model.json`).
- No reliable own-country advantage once excerpt-level and panel-level
  differences in coherence are accounted for.

## Sensitivities

- All 110 match-eligible excerpts: +0.079, 95% CI [-0.018, +0.176], p=.109.
- All 200 excerpts in the model: +0.083, 95% CI [-0.010, +0.176], p=.080.
  The match coefficient is still identified only by the 110 excerpts whose
  source country has a recruitment panel
  (`expanded_fixed_effect_sensitivities.json`).
- A country-wise standardized-effect meta-analysis over the same five
  panels gives d=+0.211, 95% CI [+0.004, +0.418], one-sided p=.023, with a
  positive adjusted effect in 5 of 5 panels (`meta_balanced_five.json`).
  It pools five country-level estimates
  rather than clustering by excerpt, so it does not carry the same weight as
  the primary model, and with five panels it is not a well-powered test.

Read together, the estimates lean positive but do not establish an
own-country effect. The five remaining panels (AU, BR, JP, PL, ZA) each have
only two source-country excerpts in the benchmark, so they appear in
`country_delta_summary.csv` as descriptives and are not treated as
country-level tests.
