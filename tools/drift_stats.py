"""Does the prompted lateral camera drift actually happen?

Fable's point: testcard_motion has three possible outcomes and the verdict must
be pre-registered, not invented after the fact.
  (a) both arms drift at a similar rate -> acuity-under-motion is judgeable
  (b) neither arm drifts             -> motion axis floored; the fixture
                                        degenerates to lane 1's static card and
                                        must be reported as a fixture failure,
                                        NOT as an encoder null
  (c) the arms differ in drift       -> the most encoder-legible signal available,
                                        since drift is the one prompt demand the
                                        conditioning still does not already supply

Global translation per frame pair by phase correlation. Free: frames are on disk.
NOTE: run against the PRE-CORRECTION testcard legs, whose negative still
suppressed "text". Drift is a camera behaviour, not a lettering behaviour, so it
is informative about which branch we are in -- but it is a PILOT signal, and the
corrected legs must be re-measured before any verdict cites it.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(r"C:\Users\jeffr\Documents\ComfyUI\output\baseline_output"
            r"\lane4_wan_text_encoder")


def load(path):
    return np.asarray(Image.open(path).convert("L"), dtype=np.float64)


def shift_between(a, b):
    """Global (dy, dx) of b relative to a, by phase correlation."""
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa = np.fft.fft2(a * window)
    fb = np.fft.fft2(b * window)
    cross = fa * np.conj(fb)
    magnitude = np.abs(cross)
    magnitude[magnitude == 0] = 1e-12
    correlation = np.fft.ifft2(cross / magnitude).real
    peak = np.unravel_index(np.argmax(correlation), correlation.shape)
    dy, dx = peak
    if dy > a.shape[0] // 2:
        dy -= a.shape[0]
    if dx > a.shape[1] // 2:
        dx -= a.shape[1]
    return float(dy), float(dx)


print("%-38s %10s %10s %12s" % ("leg", "dx_total", "dy_total", "dx_per_frame"))
for fixture in ("testcard_motion", "crowd"):
    for arm in ("ours", "official"):
        for seed in (42, 20260821):
            leg = ROOT / fixture / ("%s_seed%d" % (arm, seed))
            first = leg / "frame_00001_.png"
            last = leg / "frame_00097_.png"
            if not first.exists() or not last.exists():
                continue
            dy, dx = shift_between(load(first), load(last))
            print("%-38s %10.1f %10.1f %12.3f"
                  % ("%s/%s_seed%d" % (fixture, arm, seed), dx, dy, dx / 96.0))
