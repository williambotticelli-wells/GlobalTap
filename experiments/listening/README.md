# Listening experiment template

Online click-overlay listening experiment built on
[PsyNet](https://www.psynet.dev/). This is the generalized template
used to collect the listener ratings reported in §3.2 of the paper.

## How a session looks

1. Participant is recruited (Prolific / Hot Air / Cint).
2. Audio-volume calibration.
3. For each music excerpt, two click-overlay versions
   (`Crowd` vs `Reference`) are presented as a paired block in a
   randomised order. The participant rates each on a 1–7 scale with
   the question "How well did the clicks match the beat of the
   music?".
4. Stem blocks are randomised per participant.

Each stimulus is a 10–25 s window with click-track overlays at
1100 Hz, 12 ms Hann clicks, mixed at music 0.35 / click 0.65, with
the music loudness-normalized to −23 LUFS and the clicks at a fixed
peak level.

## Stimuli

Click-overlay WAVs are produced by Stage 7 of the analysis pipeline
(`pipeline/7_render_clicks.py`) — one WAV per
(`stem`, `condition`) pair. Stage 7 renders them as listeners heard them. To run
the experiment,
put them in `data/validation_audio/` and list them in `manifest.csv`, both
next to `experiment.py` and not included: one row per clip, with the columns
`stimulus_id`, `condition`, `corpus`, `corpus_group`, and `audio_filename`.
The `scripts/build_manifest_and_audio.py` named in its error message isn't
included.

## Running

See the [PsyNet documentation](https://www.psynet.dev/) for local testing,
build, and deployment instructions.

## What the experiment produces

Every PsyNet deployment writes a per-deployment export folder
containing `Participant.csv`, `Response.csv`, and an
`AbsoluteSliderRating.csv`-style file with listener ratings for each stem and
condition. Use those ratings as the input to the
per-corpus mean-rating tables in §3.2 of the paper.
