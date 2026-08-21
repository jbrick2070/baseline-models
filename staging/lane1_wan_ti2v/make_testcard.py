"""Draw the OTR radio-drama test card: the lane's measuring instrument.

A found still tells you whether a recipe change matters on real content. It
cannot tell you HOW MUCH more the recipe resolves, because nothing in it has a
known size. This card does: every element has a declared dimension, so a judge
answers "read down to which row" and "where do the gratings merge" by counting
instead of by taste.

Three deliberate design choices:

* It is authored at EXACTLY the render canvas, 832x480. The latent node
  bilinear-rescales any other size, so a card drawn at another resolution would
  be judged through a resampler. At native size that step is a no-op and the
  model sees the pixels as drawn.
* Element sizes SPAN the VAE's resolving limit rather than sitting under it.
  Wan 2.2 compresses this canvas to a 52x30 latent grid, so detail below a few
  pixels cannot survive in ANY arm. A card made entirely of fine detail would
  return "both arms failed" and teach nothing -- the same uncontrolled shared
  limitation Bible 12.121 was promoted for. Sizes run generous to marginal, and
  the arms separate in the middle of that range.
* Every acuity instrument appears on BOTH a light and a dark field. A sampler
  that holds an edge on paper does not necessarily hold it on black, and a card
  that tested only one polarity would average that difference away.

The letter chart uses the Sloan set (C D H K N O R S V Z), which is the set
real eye charts use precisely because those glyphs are equally legible as one
another -- so a row that fails, fails on size and not on letter choice.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 832, 480
INPUT = Path(r"C:\Users\jeffr\Documents\ComfyUI\input")
HERE = Path(__file__).resolve().parent
NAME = "lane1_testcard.png"

LIGHT = (232, 224, 208)
DARK = (16, 16, 20)
INK = (22, 20, 18)
PAPER = (238, 231, 216)

BARS = [
    ("white", (235, 235, 235)), ("yellow", (235, 235, 40)), ("cyan", (40, 235, 235)),
    ("green", (40, 200, 60)), ("magenta", (220, 50, 200)), ("red", (215, 45, 45)),
    ("blue", (45, 60, 210)), ("black", (16, 16, 16)),
]
SHAPE_SIZES = [38, 26, 17, 11]
GRATING_PITCHES = [16, 12, 8, 6, 4, 3]
# Sloan rows: (glyph height in px, letters). Row 1 is the "big E" position.
EYE_ROWS = [
    (38, "C"),
    (27, "D H K"),
    (19, "N O R S"),
    (13, "V Z C D H"),
    (9, "K N O R S V"),
]


def load_font(size, bold=True):
    names = ("arialbd.ttf", "arial.ttf") if bold else ("arial.ttf",)
    for name in names:
        try:
            return ImageFont.truetype(r"C:\Windows\Fonts\%s" % name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_shape(draw, kind, cx, cy, size, colour):
    half = size / 2.0
    box = (cx - half, cy - half, cx + half, cy + half)
    stroke = max(1, int(round(size / 7.0)))
    if kind == "circle":
        draw.ellipse(box, outline=colour, width=stroke)
    elif kind == "square":
        draw.rectangle(box, outline=colour, width=stroke)
    elif kind == "triangle":
        draw.polygon([(cx, cy - half), (cx + half, cy + half), (cx - half, cy + half)],
                     outline=colour, width=stroke)
    elif kind == "diamond":
        draw.polygon([(cx, cy - half), (cx + half, cy), (cx, cy + half), (cx - half, cy)],
                     outline=colour, width=stroke)
    elif kind == "cross":
        draw.line((cx - half, cy, cx + half, cy), fill=colour, width=stroke)
        draw.line((cx, cy - half, cx, cy + half), fill=colour, width=stroke)


def shape_panel(draw, x0, y0, panel_w, panel_h, background, foreground, label):
    draw.rectangle((x0, y0, x0 + panel_w, y0 + panel_h), fill=background)
    draw.text((x0 + 5, y0 + 3), label, fill=foreground, font=load_font(10))
    kinds = ["circle", "square", "triangle", "diamond", "cross"]
    row_y = y0 + 20
    for row, size in enumerate(SHAPE_SIZES):
        cx = x0 + 22
        for column in range(5):
            draw_shape(draw, kinds[(row + column) % len(kinds)],
                       cx, row_y + size / 2.0, size, foreground)
            cx += size + max(7, int(size * 0.5))
        draw.text((x0 + panel_w - 14, row_y + size / 2.0 - 5),
                  str(row + 1), fill=foreground, font=load_font(10))
        row_y += size + 7


def eye_panel(draw, x0, y0, panel_w, panel_h, background, foreground, label):
    """A Sloan-letter acuity chart: the row number IS the measurement."""
    draw.rectangle((x0, y0, x0 + panel_w, y0 + panel_h), fill=background)
    draw.text((x0 + 5, y0 + 3), label, fill=foreground, font=load_font(10))
    row_y = y0 + 19
    for index, (size, letters) in enumerate(EYE_ROWS):
        font = load_font(size)
        pitch = size * 1.05
        x = x0 + 26
        for glyph in letters.replace(" ", ""):
            draw.text((x, row_y), glyph, fill=foreground, font=font)
            x += pitch
        draw.text((x0 + panel_w - 14, row_y + size / 2.0 - 5),
                  str(index + 1), fill=foreground, font=load_font(10))
        row_y += size + 5


def gratings(draw, x0, y0, block_w, block_h, background, foreground):
    draw.rectangle((x0, y0, x0 + block_w, y0 + block_h), fill=background)
    font = load_font(8, bold=False)
    cell = block_w // len(GRATING_PITCHES)
    for index, pitch in enumerate(GRATING_PITCHES):
        left = x0 + index * cell
        x = left + 3
        while x < left + cell - 5:
            draw.rectangle((x, y0 + 11, x + max(1, pitch // 2) - 1, y0 + block_h - 3),
                           fill=foreground)
            x += pitch
        draw.text((left + 3, y0 + 1), "%dpx" % pitch, fill=foreground, font=font)


def main() -> int:
    image = Image.new("RGB", (WIDTH, HEIGHT), DARK)
    draw = ImageDraw.Draw(image)

    bar_w = WIDTH / len(BARS)
    for index, (_name, colour) in enumerate(BARS):
        draw.rectangle((index * bar_w, 0, (index + 1) * bar_w, 38), fill=colour)

    steps = 16
    step_w = WIDTH / steps
    for index in range(steps):
        level = int(round(255 * index / (steps - 1)))
        draw.rectangle((index * step_w, 38, (index + 1) * step_w, 66),
                       fill=(level, level, level))

    shape_panel(draw, 8, 72, 400, 132, PAPER, INK, "SHAPES / LIGHT")
    shape_panel(draw, 424, 72, 400, 132, DARK, LIGHT, "SHAPES / DARK")

    gratings(draw, 8, 208, 400, 46, PAPER, INK)
    gratings(draw, 424, 208, 400, 46, DARK, LIGHT)

    eye_panel(draw, 8, 258, 400, 160, PAPER, INK, "EYE CHART / LIGHT")
    eye_panel(draw, 424, 258, 400, 160, DARK, LIGHT, "EYE CHART / DARK")

    for x in range(WIDTH):
        level = int(round(255 * x / (WIDTH - 1)))
        draw.line((x, 422, x, 452), fill=(level, level, level))

    draw.rectangle((0, 452, WIDTH, HEIGHT), fill=DARK)
    draw.text((10, 458), "OTR LANE 1 -- WAN TI2V RECIPE TEST CARD",
              fill=LIGHT, font=load_font(14))
    for index, radius in enumerate([10, 7, 5, 3]):
        cx = WIDTH - 28 - index * 28
        draw.ellipse((cx - radius, 466 - radius, cx + radius, 466 + radius),
                     outline=LIGHT, width=2)

    destination = INPUT / NAME
    image.save(destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()

    spec = {
        "image": NAME,
        "sha256": digest,
        "size": [WIDTH, HEIGHT],
        "authored_at_canvas": True,
        "eye_chart_rows": [{"row": i + 1, "glyph_px": s, "letters": t}
                           for i, (s, t) in enumerate(EYE_ROWS)],
        "shape_row_sizes_px": SHAPE_SIZES,
        "grating_pitches_px": GRATING_PITCHES,
        "colour_bars": [name for name, _ in BARS],
        "grayscale_steps": steps,
        "polarities": ["light field", "dark field"],
        "note": ("Sizes span the latent resolving limit (52x30 cells for this "
                 "canvas) so the arms separate mid-range instead of both "
                 "failing at the bottom. Sloan letters are equally legible to "
                 "one another, so a failed row failed on size."),
    }
    io.open(HERE / "TESTCARD.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print("[TESTCARD] %s  %dx%d  sha256=%s" % (destination, WIDTH, HEIGHT, digest[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
