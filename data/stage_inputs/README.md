# Bundled pipeline-stage snapshots

This directory ships de-identified aggregate outputs of Stages 2–3 of the
pipeline, taken from the runs that drove the validation experiment in the
paper. With this snapshot, **Stage 4 (`pipeline/4_run_crowd_gs.py`) can be
run from a fresh clone** — no `PROJECT_ROOT` and no raw audio required.

**Reproducibility status:** running Stage 4 from this bundled snapshot
exactly reproduces the `cv_pipeline` value in `data/per_stem_metrics.csv`
(up to the 5-decimal rounding already applied in the released CSV) for all
240 stems — all 100 mixed-corpora, all 80 Ballroom, all 20 MIREX, and all 40
supplementary GlobalMood-40 stems — using the paper-documented Stage-2
setting `peak_prominence=0.10` (`config/canonical240.json` /
`config/globalmood200.json`).

```
canonical240/   240-stem validation set (paper §3.2–§3.3, §3.6)
globalmood200/  200-stem GlobalTap cross-cultural benchmark (paper §3.4–§3.5)
```

Each subdirectory contains:

| File                                  | Stage | Purpose                                            |
| ------------------------------------- | ----- | -------------------------------------------------- |
| `cleaned_kde_peaks.csv`               | 2     | KDE peaks after MAD-based outlier cleaning (Stage-4 input) |
| `algorithm_beats.csv`                 | 3     | Madmom DBN F-measure baseline beats                |
| `beat_this_algorithm_beats.csv`       | 3b    | Beat This! transformer F-measure baseline beats    |

The benchmark taps behind the GlobalMood200 snapshot are released in
`data/taps/`, and `scripts/kde_peaks_from_taps.py` rebuilds
`cleaned_kde_peaks.csv` from them, returning the snapshot below. The
validation-set taps are not redistributed, and that snapshot is frozen at the
tapper pool the click-track listening stimuli were rendered from, so it is the
file to use for anything that has to match the rated stimuli
(`data/taps/README.md` has the details).
All bundled `cleaned_kde_peaks.csv`, algorithm-beat tables, and optimized
`crowd_gs` beats are already in **music time** (0 s = first audio sample of
the 30 s clip).

`pipeline/4_run_crowd_gs.py` will look in
`${PROJECT_ROOT}/outputs/<dataset>/{repp,madmom}/` first. If that path
is absent (e.g. `PROJECT_ROOT` is unset, as in a fresh clone), it
transparently falls back to the snapshot here, so running

```bash
python pipeline/4_run_crowd_gs.py --config config/canonical240.json
```

from a fresh clone regenerates the `crowd_gs` beat files without any
external inputs. That output's derived `cv_pipeline` is now confirmed
byte-for-byte reproducible against `data/per_stem_metrics.csv` for the
full 240-stem set (see the reproducibility status above). The repo does
not separately ship a copy of the raw `.txt` beat files to diff against
— `data/per_stem_metrics.csv` is the released aggregate derived from them.

The raw audio, original PsyNet exports, and reference annotations from
the upstream corpora are not redistributed in this repo — see
`data/SOURCES.md` for how to fetch them.
