#!/usr/bin/env python3
"""Render Figure-2-style playhead videos for the four §3.5 case studies.

Each video shows the four-panel Figure 2 layout for one case-study stem:

    (i)   Audio spectrogram
    (ii)  Per-participant tap raster
    (iii) Pooled KDE + consensus peaks
    (iv)  Optimized beat grid (Crowd) vs reference annotation

A vertical playhead line moves across the [10, 25] s window. Each video
plays the **Crowd** click-overlay first (label "Crowd" displayed below
the figure), then the **Reference** click-overlay (label "Reference"),
back-to-back in the same MP4. It uses MP3 click overlays rendered locally by
Stage 7 of the pipeline. Pre-rendered output for the eight case studies ships
in audio_demos/; this script is for regenerating that media from source.

Outputs (≈1.5 MB each):
    audio_demos/<case-label>__playhead.mp4
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO      = Path(__file__).resolve().parents[1]
if "GLOBALTAP_DATA_ROOT" not in os.environ:
    raise RuntimeError(
        "Set GLOBALTAP_DATA_ROOT to the directory containing GlobalTap_v1.0 "
        "and canonical240_30s before rendering local-only media."
    )
DATA_ROOT = Path(os.environ["GLOBALTAP_DATA_ROOT"]).expanduser().resolve()
PIPELINE  = DATA_ROOT / "GlobalTap_v1.0/pipeline"
AUDIO     = DATA_ROOT / "audio/canonical240_30s"
OUT_DIR   = REPO / "audio_demos"

# Pipeline run that produced the case studies (canonical 240).
RUN_DIR   = PIPELINE / "outputs/canonical240"
MERGED    = RUN_DIR / "merged/TapTrialMusic_EXPORT_COMPAT.csv"
PEAKS     = RUN_DIR / "repp/cleaned_kde_peaks.csv"
CROWD_DIR = RUN_DIR / "crowd_gs"

# Reference annotations, resolved as for the listening study's Reference clicks.
GT_MAP    = REPO / "config/gt_source_map_canonical240.json"

# ─── Pipeline constants, read from the Stage 2 config ────────────────────────
CFG            = json.loads((REPO / "config/canonical240.json").read_text())
ALIGN          = CFG["alignment"]
REPP_OFFSET_MS = 1000.0 * CFG["stim_offset_s"]   # REPP marker lead-in before the music
KDE_DT         = ALIGN["kde_dt_s"]
WIN_T0, WIN_T1 = CFG["listening_window"]["t0"], CFG["listening_window"]["t1"]

# ─── Case studies ─────────────────────────────────────────────────────────────
# Eight stems total: four illustrate the §3.5 structural divergences (the
# "challenging" set), four illustrate cases where Crowd and Reference align
# tightly throughout the song (the "simple" set).  The two sets are
# interleaved in the supplementary HTML grid.
CASES = [
    # ── Challenging cases (§3.5 phenomena) ─────────────────────────────────
    {
        "label":   "candombe_phase_offset",
        "stem":    "proyecto.1992_lobo_06",
        "title":   "Candombe — phase offset (~140 ms)",
        "audio":   AUDIO / "candombe/proyecto.1992_lobo_06.wav",
    },
    {
        "label":   "ballroom_halftime",
        "stem":    "Albums-Chrisanne3-09",
        "title":   "Viennese Waltz — half-time tactus alternative",
        "audio":   AUDIO / "ballroom_heldout/Albums-Chrisanne3-09.wav",
    },
    {
        "label":   "mixed_bimodal",
        "stem":    "Media-105914",
        "title":   "Ballroom — bimodal pooled tapping",
        "audio":   AUDIO / "ballroom_heldout/Media-105914.wav",
    },
    {
        "label":   "ballroom_baseline",
        "stem":    "Albums-AnaBelen_Veneo-13",
        "title":   "Ballroom — high-consensus baseline",
        "audio":   AUDIO / "ballroom/Albums-AnaBelen_Veneo-13.wav",
    },
    # ── Simple cases (high agreement, KDE peaks ≈ optimizer beats) ─────────
    {
        "label":   "gtzan_disco_simple",
        "stem":    "gtzan_disco_00000",
        "title":   "GTZAN Disco — tight alignment throughout",
        "audio":   AUDIO / "gtzan/gtzan_disco_00000.wav",
    },
    {
        "label":   "tapcorrect_pop_simple",
        "stem":    "054_youtube_UgL4N4Hf1dk",
        "title":   "Pop (TapCorrect) — KDE peaks track the optimizer grid",
        "audio":   AUDIO / "tapcorrect/054_youtube_UgL4N4Hf1dk.wav",
    },
    {
        "label":   "ballroom_latin_simple",
        "stem":    "Albums-Latin_Jam-04",
        "title":   "Latin Ballroom — high-consensus dance feel",
        "audio":   AUDIO / "ballroom_heldout/Albums-Latin_Jam-04.wav",
    },
    {
        "label":   "cretan_simple",
        "stem":    "cretan1",
        "title":   "Cretan — high consensus on a non-Western corpus",
        "audio":   AUDIO / "cretan/cretan1.wav",
    },
]


# ─── Data loaders ─────────────────────────────────────────────────────────────
def load_taps_per_participant(stem: str, merged_csv: Path):
    df = pd.read_csv(
        merged_csv,
        usecols=["participant_id", "_stem", "resp_onsets_aligned",
                 "failed", "analysis_failed"],
        low_memory=False,
    )
    df = df[(df["_stem"] == stem)
            & (df["failed"] != True)             # noqa: E712
            & (df["analysis_failed"] != True)]   # noqa: E712
    out = {}
    for _, row in df.iterrows():
        try:
            ms = np.array(ast.literal_eval(str(row["resp_onsets_aligned"])),
                          dtype=float)
        except (ValueError, SyntaxError):
            continue
        s = (ms - REPP_OFFSET_MS) / 1000.0
        s = s[(s >= 0) & (s <= 35)]
        if s.size > 2:
            out[row["participant_id"]] = np.sort(np.unique(s))
    return out


def load_kde_peaks(stem: str, peaks_csv: Path) -> np.ndarray:
    df = pd.read_csv(peaks_csv)
    col = "stimulus_id" if "stimulus_id" in df.columns else "_stem"
    sub = df[df[col] == stem]
    if sub.empty:
        return np.array([])
    return np.sort(sub["peak_time_s"].values)


def load_crowd_beats(stem: str) -> np.ndarray:
    fp = CROWD_DIR / f"{stem}_crowd_gs.txt"
    if fp.exists():
        return np.loadtxt(fp)
    fp = CROWD_DIR / f"{stem}__crowd_gs.txt"
    if fp.exists():
        return np.loadtxt(fp)
    return np.array([])


def load_reference_beats(case: dict) -> np.ndarray:
    """Reference beats from the released loader, which also places the
    Reference clicks. The .beats file beside each 30 s clip can be a different
    annotation release (proyecto.1992_lobo_06 differs by about 22 ms)."""
    import sys
    sys.path.insert(0, str(REPO))
    from lib.gt_loader import load_gt_for_stem
    gt_map = json.loads(GT_MAP.read_text())
    for entry in gt_map.values():
        path = entry.get("path")
        if isinstance(path, str) and path.startswith("${PROJECT_ROOT}/data/"):
            entry["path"] = path.removeprefix("${PROJECT_ROOT}/data/")
    beats = load_gt_for_stem(case["stem"], gt_map, DATA_ROOT)
    return np.array([]) if beats is None else np.sort(beats[:, 0].astype(float))


def stage2_density(stem: str, merged_csv: Path):
    """Stage 2's pooled density and consensus peaks, from the pipeline's own
    functions and settings; the peaks equal cleaned_kde_peaks.csv."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    from repp_gt_alignment_pipeline import (clean_taps_trial, gaussian_kde,
                                            kde_peaks, taps_ms_to_s)
    df = pd.read_csv(merged_csv,
                     usecols=["_stem", "resp_onsets_aligned", "analysis_failed"],
                     low_memory=False)
    df = df[(df["_stem"] == stem) & (df["analysis_failed"] == False)]  # noqa: E712
    w0, w1 = CFG["optimizer_window"]["w0"], CFG["optimizer_window"]["w1"]
    pool = []
    for raw in df["resp_onsets_aligned"]:
        taps = np.sort(taps_ms_to_s(ast.literal_eval(str(raw)), CFG["stim_offset_s"]))
        clean, _ = clean_taps_trial(taps, w0, w1, None, 0.0, ALIGN["mad_threshold"],
                                    skip_tempo_gate=True)
        if clean.size:
            pool.append(clean)
    t_grid, y = gaussian_kde(np.concatenate(pool), w0, w1,
                             ALIGN["kde_bandwidth_ms"], KDE_DT)
    peaks = kde_peaks(t_grid, y, KDE_DT, ALIGN["peak_prominence"],
                      ALIGN["peak_distance_s"], ALIGN["peak_width_s"])
    return t_grid, y, np.sort(peaks)


def compute_spectrogram(y, sr, t0, t1, fmax_hz=6000.0,
                        n_fft=2048, hop=256):
    import librosa
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop)) ** 2
    S_db = librosa.power_to_db(S, ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    S_db = S_db[freqs <= fmax_hz, :]
    times = librosa.frames_to_time(
        np.arange(S_db.shape[1]), sr=sr, hop_length=hop)
    mask = (times >= t0) & (times <= t1)
    return S_db[:, mask]


def compute_envelope(y, sr, t0, t1, hop_ms=5.0):
    hop = max(1, int(sr * hop_ms / 1000.0))
    n_frames = len(y) // hop
    env = np.array([np.max(np.abs(y[i*hop:(i+1)*hop]))
                    for i in range(n_frames)])
    if env.max() > 0:
        env = env / env.max()
    t_env = np.arange(n_frames) * hop_ms / 1000.0
    mask = (t_env >= t0) & (t_env <= t1)
    return t_env[mask], env[mask]


# ─── Static figure (Figure-2 layout) ─────────────────────────────────────────
def build_figure(case: dict):
    """Build the static figure-2 layout. Returns (fig, axes, playhead_lines,
    condition_text, frame_dt) — playhead lines are updated per frame."""
    import sys
    sys.path.insert(0, str(REPO / "figures"))
    from fig_utils import apply_style
    apply_style()

    stem = case["stem"]
    taps_by_pid = load_taps_per_participant(stem, MERGED)
    if not taps_by_pid:
        raise RuntimeError(f"No taps loaded for {stem}")
    pids = sorted(taps_by_pid.keys())
    n_pids = len(pids)

    t_grid, yk, peaks = stage2_density(stem, MERGED)
    yk = yk / (yk.max() + 1e-12)

    crowd = load_crowd_beats(stem)
    gt    = load_reference_beats(case)

    import librosa
    y_audio, sr = librosa.load(case["audio"], sr=22050, mono=True)
    S_db = compute_spectrogram(y_audio, sr, WIN_T0, WIN_T1)
    t_env, env = compute_envelope(y_audio, sr, WIN_T0, WIN_T1)

    # 8.0 in × 5.4 in × 110 dpi = 880 × 594 px (both even — required by
    # libx264 / yuv420p).
    fig = plt.figure(figsize=(8.0, 5.4), dpi=110)
    gs = fig.add_gridspec(
        4, 1, height_ratios=[0.85, 1.6, 0.9, 0.9],
        hspace=0.40, left=0.10, right=0.985, top=0.93, bottom=0.13,
    )

    fig.suptitle(case["title"], fontsize=10.5, fontweight="bold", y=0.985)

    mask_eval = (t_grid >= WIN_T0) & (t_grid <= WIN_T1)

    OPT_C = "#2166AC"; GT_C = "#4DAF4A"

    # (i) Spectrogram
    ax_spec = fig.add_subplot(gs[0])
    ax_spec.imshow(S_db, aspect="auto", origin="lower",
                   extent=[WIN_T0, WIN_T1, 0.0, 6.0],
                   cmap="magma", interpolation="bilinear")
    ax_spec.set_xlim(WIN_T0, WIN_T1)
    ax_spec.set_yticks([0, 2, 4, 6])
    ax_spec.set_ylabel("Freq.\n(kHz)", fontsize=8)
    ax_spec.set_title("(i)  Audio spectrogram", loc="left",
                      fontweight="bold", fontsize=9)
    ax_spec.tick_params(labelbottom=False, labelsize=7.5)

    # (ii) Tap raster
    ax_rast = fig.add_subplot(gs[1])
    for i, pid in enumerate(pids):
        t = taps_by_pid[pid]
        t_v = t[(t >= WIN_T0) & (t <= WIN_T1)]
        ax_rast.vlines(t_v, i + 0.05, i + 0.95, linewidth=0.9,
                       color="#1a1a1a", alpha=0.95)
    ax_rast.set_ylabel(f"Participant\n(N={n_pids})", fontsize=8)
    ax_rast.set_yticks([0, n_pids])
    ax_rast.set_xlim(WIN_T0, WIN_T1)
    ax_rast.set_ylim(0, n_pids)
    ax_rast.set_title("(ii)  Per-participant tap raster", loc="left",
                      fontweight="bold", fontsize=9)
    ax_rast.tick_params(labelbottom=False, labelsize=7.5)

    # (iii) Stage 2's pooled KDE and its consensus peaks
    ax_kde = fig.add_subplot(gs[2])
    ax_kde.fill_between(t_grid[mask_eval], yk[mask_eval], alpha=0.22,
                        color=OPT_C, zorder=1)
    ax_kde.plot(t_grid[mask_eval], yk[mask_eval], color=OPT_C,
                linewidth=1.5, zorder=2)
    eval_y = yk[mask_eval]
    pv = peaks[(peaks >= WIN_T0) & (peaks <= WIN_T1)]
    if pv.size:
        ax_kde.scatter(pv, np.interp(pv, t_grid, yk),
                       color=OPT_C, s=28, zorder=5,
                       edgecolors="white", linewidths=0.6)
    ax_kde.set_ylabel("KDE\ndensity", fontsize=8)
    ax_kde.set_xlim(WIN_T0, WIN_T1)
    ax_kde.set_ylim(0, max(1.0, eval_y.max() * 1.05))
    ax_kde.set_title("(iii)  Pooled KDE + consensus peaks", loc="left",
                     fontweight="bold", fontsize=9)
    ax_kde.tick_params(labelbottom=False, labelsize=7.5)

    # (iv) Beats vs reference
    ax_b = fig.add_subplot(gs[3])
    ax_b.set_xlim(WIN_T0, WIN_T1); ax_b.set_ylim(0, 1.0)
    ax_b.fill_between(t_env, 0, env * 0.75, color="#888888", alpha=0.30,
                      linewidth=0, zorder=0)
    cv = crowd[(crowd >= WIN_T0) & (crowd <= WIN_T1)]
    gv = gt[(gt >= WIN_T0) & (gt <= WIN_T1)]
    for t in cv:
        ax_b.axvline(t, color=OPT_C, linewidth=1.8, alpha=0.85,
                     ymin=0.0, ymax=0.92, zorder=3)
    for t in gv:
        ax_b.axvline(t, color=GT_C, linewidth=1.3, alpha=0.6,
                     linestyle="--", ymin=0.0, ymax=0.92, zorder=3)
    ax_b.set_xlabel("Time (s)", fontsize=8.5)
    ax_b.set_ylabel("Audio\nenvelope", fontsize=8)
    ax_b.set_yticks([])
    ax_b.set_title("(iv)  Optimized beat grid vs. reference", loc="left",
                   fontweight="bold", fontsize=9)
    ax_b.tick_params(labelsize=7.5)

    # Playhead lines (one per axis), updated each frame.
    playheads = [
        ax.axvline(WIN_T0, color="#d62728", linewidth=1.8, alpha=0.85,
                   zorder=10) for ax in (ax_spec, ax_rast, ax_kde, ax_b)
    ]

    # Condition label below the figure (centered).
    cond_text = fig.text(0.5, 0.045, "Crowd",
                         ha="center", va="center",
                         fontsize=11, fontweight="bold",
                         color=OPT_C,
                         bbox=dict(facecolor="#eaf3fb",
                                   edgecolor=OPT_C,
                                   boxstyle="round,pad=0.35"))

    return fig, playheads, cond_text


# ─── Render one video ─────────────────────────────────────────────────────────
def render_video(case: dict, fps: int = 25, work_dir: Path | None = None):
    label = case["label"]
    print(f"\n[{label}] building figure …")
    fig, playheads, cond_text = build_figure(case)

    work = work_dir or (OUT_DIR / f"_frames_{label}")
    work.mkdir(exist_ok=True, parents=True)
    for old in work.glob("*.png"):
        old.unlink()

    # 30 s total = 15 s Crowd + 15 s Reference. Frame N runs at N / fps
    # seconds into the video; map to playhead time and condition label.
    n_frames = int(30 * fps)
    OPT_C = "#2166AC"; GT_C = "#4DAF4A"
    print(f"[{label}] rendering {n_frames} frames at {fps} fps …")
    for n in range(n_frames):
        v_t = n / fps
        if v_t < 15:
            playhead_t = WIN_T0 + v_t
            cond_text.set_text("Crowd")
            cond_text.set_color(OPT_C)
            cond_text.get_bbox_patch().set_edgecolor(OPT_C)
            cond_text.get_bbox_patch().set_facecolor("#eaf3fb")
        else:
            playhead_t = WIN_T0 + (v_t - 15)
            cond_text.set_text("Reference")
            cond_text.set_color(GT_C)
            cond_text.get_bbox_patch().set_edgecolor(GT_C)
            cond_text.get_bbox_patch().set_facecolor("#ebf6e8")
        for line in playheads:
            line.set_xdata([playhead_t, playhead_t])
        fig.savefig(work / f"frame_{n:05d}.png", dpi=110)
        if (n + 1) % 100 == 0:
            print(f"  {n+1}/{n_frames}")
    plt.close(fig)

    # Concatenate the two MP3s with ffmpeg, then mux with the silent
    # frame stream into a single MP4.
    crowd_mp3 = OUT_DIR / f"{label}__crowd_gs.mp3"
    gt_mp3    = OUT_DIR / f"{label}__gt.mp3"
    if not crowd_mp3.exists() or not gt_mp3.exists():
        print(f"  [warn] MP3s missing ({crowd_mp3}, {gt_mp3}); skip mux")
        return None

    audio_concat = work / "audio_concat.mp3"
    list_file = work / "concat_list.txt"
    list_file.write_text(
        f"file '{crowd_mp3.resolve()}'\n"
        f"file '{gt_mp3.resolve()}'\n"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c:a", "libmp3lame", "-b:a", "96k",
         str(audio_concat)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    out_mp4 = OUT_DIR / f"{label}__playhead.mp4"
    print(f"[{label}] muxing → {out_mp4.relative_to(REPO)}")
    subprocess.run(
        ["ffmpeg", "-y",
         "-r", str(fps),
         "-i", str(work / "frame_%05d.png"),
         "-i", str(audio_concat),
         "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
         "-preset", "medium",
         "-c:a", "aac", "-b:a", "96k",
         "-shortest",
         str(out_mp4)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Clean up frames.
    shutil.rmtree(work, ignore_errors=True)

    size_kb = out_mp4.stat().st_size / 1024
    print(f"[{label}] done — {size_kb:.0f} KB")
    return out_mp4


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for case in CASES:
        try:
            render_video(case)
        except Exception as e:
            print(f"[error] {case['label']}: {e}")


if __name__ == "__main__":
    main()
