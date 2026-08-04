# Tapping experiment template

Online beat-tapping experiment built on
[PsyNet](https://www.psynet.dev/) with audio-based timing recovery via
[REPP](https://gitlab.com/computational-audition/repp). This is the
generalised template used to collect the GlobalTap tapping data.

## How a session looks

1. Participant is recruited (Prolific / Hot Air / Cint).
2. Audio-volume calibration + microphone-marker pre-screen
   (`repp_prescreens.py`).
3. Practice trials.
4. ~30 second tapping trials on randomly assigned stimuli.
5. Optional Goldsmiths-MSI questionnaire
   (`gmsi.py`; Müllensiefen et al., 2014).

Trials with failed recordings, marker analysis, or empty taps are
flagged and excluded from downstream analysis.

## Stimuli

Audio stimuli (24-bit WAV, mono, 30 s clips) live in
`static/audio_stimuli/` (not redistributed). Update the per-stem
manifest in `experiment.py` (`STIMULI_MANIFEST` constant) to point at
your filenames. The manifest also carries optional fields like
`bpm_hint` (used by the IOI tempo-gate prescreen).

## Running

See the [PsyNet documentation](https://www.psynet.dev/) for the
canonical local-debug, build, and deploy recipes.

## What the upstream produces

Every PsyNet deployment writes a per-deployment export folder
containing `Participant.csv`, `Response.csv`, and
`TapTrialMusic.csv`. Convert / merge those into the canonical
`TapTrialMusic_EXPORT_COMPAT.csv` schema using
`../../pipeline/1_merge_exports.py` to feed them into the analysis
pipeline.
