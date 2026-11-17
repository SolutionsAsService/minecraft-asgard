#!/usr/bin/env python3
"""Compose the site's creature pictures from playtest/models/<id>-*.png (needs ImageMagick).

    python3 tools/creature_shots.py     site/img/shots/creature-<id>.png (three-quarter), creature-<id>-side.png, creatures.png (all of them)

The cameras are aimed and set by tools/model_sheet.py so the creature is centred and fills about half the frame; a boss's frame loses its top 40 pixels
(the boss bar) and is trimmed back to 16:9; nothing else is cropped, so no per-creature crop boxes are needed.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "playtest/models"
OUT = ROOT / "site/img/shots"
ORDER = ["draugr", "draugr_lord", "troll", "jotunn", "warg", "fenrir", "raven", "sleipnir"]


def run(*a):
    subprocess.run(a, check=True)


BOSSES = {"fenrir"}


def frame(src, dst, size="854x480", boss=False):
    if boss:        # a boss bar sits in the top 40 pixels: cut it and trim back to 16:9
        run("convert", str(src), "-crop", "782x440+36+40", "+repage", "-filter", "point", "-resize", size + "!", str(dst))
    else:
        run("convert", str(src), "-filter", "point", "-resize", size + "!", str(dst))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = []
    for i in ORDER:
        frame(SRC / f"{i}-three-quarter.png", OUT / f"creature-{i}.png", boss=i in BOSSES)
        frame(SRC / f"{i}-side.png", OUT / f"creature-{i}-side.png", boss=i in BOSSES)
        t = OUT / f".tile-{i}.png"
        frame(SRC / f"{i}-three-quarter.png", t, "427x240", boss=i in BOSSES)
        tiles.append(str(t))
    run("montage", *tiles, "-tile", "4x2", "-geometry", "427x240+0+0", "-background", "#10141c", str(OUT / "creatures.png"))
    for t in tiles:
        Path(t).unlink()
    print("creature pictures written")


if __name__ == "__main__":
    main()
