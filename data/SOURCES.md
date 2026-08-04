## Where to obtain the audio and reference annotations

The companion repository does **not** redistribute the music itself.
The 30 s audio excerpts and the upstream beat-reference annotations
are sourced from publicly distributed corpora (or, for GlobalMood,
public YouTube uploads). This document maps every stem in the paper
to its source so anyone can rebuild the audio inputs from scratch.

Stem-level indices:

- `data/stimuli_index_canonical240.csv` — the 240 stems that enter the
  validation experiment (Mixed corpora + Ballroom + MIREX +
  GlobalMood). The `audio_source` field is either an
  `upstream::<corpus>` token (look up the row's corpus below) or a
  direct YouTube URL.
- `data/stimuli_index_globalmood200.csv` — the 200 GlobalMood stems
  that constitute the GlobalTap benchmark. Each `stem_id` is a
  YouTube video ID; `audio_source` resolves to
  `https://www.youtube.com/watch?v=<stem_id>`.

For every stem the pipeline operates on a 30 s clip starting at a
corpus-specific offset. That offset is recorded in
`config/gt_source_map_canonical240.json` (see the `clip_offset_s`
section of the top-level README) so anyone downloading
full-length audio can extract the matching window.

### Reference annotation packs (canonical240)

| Corpus       | Audio                                          | Reference annotations                                            |
|--------------|------------------------------------------------|------------------------------------------------------------------|
| Ballroom     | ISMIR 2004 Ballroom dance corpus (200 clips).  | Krebs et al. (2013) annotations; redistributed in the Beat This! release. |
| Hainsworth   | Hainsworth & Macleod (2003) corpus.            | Beat This! release.                                              |
| RWC          | RWC Pop / Royalty / Classical / Jazz subsets.  | Goto et al. RWC annotations; bm30_filt clip-window pack distributed with the GlobalTap pipeline. |
| Beatles      | Isophonics Beatles corpus.                     | Mauch et al. Isophonics beats (Beat This! release).              |
| Robbie Williams | Di Giorgi et al. Robbie Williams set.       | Beat This! release.                                              |
| Hjerkinn     | Hjerkinn corpus.                               | Beat This! release.                                              |
| Harmonix     | Harmonix Set (Nieto et al. 2019).              | Harmonix Set beats; Beat This! release.                          |
| Tapcorrect   | TapCorrect / GTZAN-rhythm pack.                | Driedger et al. tap-correct annotations.                         |
| Candombe     | Candombe corpus (Rocamora et al.).             | Candombe beat annotations.                                       |
| GTZAN-rhythm | GTZAN with Marchand & Peeters annotations.     | Marchand & Peeters beats; Beat This! release.                    |
| ASAP         | ASAP solo-piano performances.                  | ASAP score-aligned beats.                                        |
| Carnatic     | CompMusic Carnatic music collection.           | Srinivasamurthy et al. (2014) beats.                             |
| Cretan       | Holzapfel Cretan-leaping-dance set.            | Holzapfel & Stylianou (2011) beats.                              |
| MIREX        | MIREX 2006 beat-tracking set (40 clips).       | Pooled lab-tapper consensus distributed with the MIREX 2006 set. |

`source_label = "beat_this_upstream"` rows in
`config/gt_source_map_canonical240.json` mean the reference beats are
those distributed in the
[Beat This!](https://github.com/CPJKU/beat_this) release. Everything
else lists its own pack name in the `source_label` field.

### Audio for GlobalMood (200-stem benchmark)

Each `stem_id` is the YouTube video ID. To rebuild the 30 s clips:

```bash
yt-dlp -x --audio-format wav -o "audio/%(id)s.%(ext)s" "<stem-url>"
ffmpeg -ss 30 -t 30 -i audio/<stem-id>.wav -ac 1 -ar 44100 \
       audio/globalmood_30s/<stem-id>.wav
```

(Start times for GlobalMood clips are 30 s into each track, matching
the GlobalMood release, see the original GlobalMood paper for the
recruitment-driven excerpt selection.)

### Tapping data

The taps themselves are released in `data/taps/`, de-identified and in music
time. What is not redistributed is the original PsyNet export tree for every
tapping deployment (≈1,500 participants, ≈37k valid trials, 2.1 GB), which
carries platform identifiers and per-session metadata (see the paper's Ethics
Statement).

Participants were recruited through Prolific for the eleven benchmark exports
and the listener-rating panel. The 40-excerpt GlobalMood validation panel used
both Prolific and Cint, with three Cint exports contributing 58 of that panel's
296 tappers (their batch names appear in `scripts/compute_istc_per_stem.py`).
The paper's Methods and Ethics Statement name Prolific only. All sessions used
the same PsyNet tapping paradigm and audio-marker screening, and the batches
were analyzed together rather than separately by recruitment platform.

The PsyNet exports are
**not** needed to verify the paper: every numerical claim and figure is
reproducible from `data/per_stem_metrics.csv`, `data/example_stem_panels.npz`
and `data/country_panels.csv`, and Stage 4 itself can be re-run end-to-end
against the aggregate Stage-2/3 snapshots in `data/stage_inputs/`. See
`data/stage_inputs/README.md` for details; Stage 4 exactly reproduces the
released `cv_pipeline` values for all 240 stems (mixed-corpora, Ballroom,
MIREX, and the supplementary GlobalMood-40 stems alike). `istc` is a
separate, pre-optimization measure computed directly from raw taps (not
Stage-4 output); `scripts/compute_istc_per_stem.py`, run against a
`raw_tapping_data/merged/` tree, recovers the released `istc`
column for all 240 stems to within 0.2 points on the 10-90 scale (verified:
Spearman $\rho$=0.99997, median absolute difference 0.03, maximum 0.2).
ISTC is the mean of 30 per-second maxima, so a 0.2 gap is a handful of seconds
in which one participant more or fewer fell inside a 100 ms bin, which follows
from small trial-level filtering differences between this script and the
original run. Stem rankings and the reported associations hold at that
magnitude.

The `n_participants` column records the per-stem pool behind these
reference-free measures rather than a participation count. It agrees with the
usable-trial counts in the supplementary participant-flow summary to within a
few trials for the mixed-corpora, MIREX and GlobalMood-40 panels, and runs
about 9% higher for the Ballroom panel. Cite the participant-flow counts for
participation figures and `n_participants` when reasoning about `istc` or
`cv_pipeline`.

If you want to re-run the *full* Stages 1–3 (raw exports → merged
taps → KDE peaks → Madmom baseline) or the ISTC script above, point
`PROJECT_ROOT` at a tree that mirrors `raw_tapping_data/` and invoke
`./run_pipeline.sh`.

### License notes

All upstream corpora retain their original licenses. Outside of
`audio_demos/` (eight short case-study clips, see its `README.md`), this
repository only redistributes derived per-stem **annotation** outputs
(crowd beats, KDE peaks, F-measure tables) and aggregate per-stem metrics.
No other audio is committed.
