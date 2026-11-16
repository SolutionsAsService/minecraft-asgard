#!/usr/bin/env python3
"""Compose the site's creature pictures from playtest/models/<id>-*.png (the six-angle photographs of each model).

    python3 tools/creature_shots.py       writes site/img/shots/creature-<id>.png (three-quarter + side) and creatures.png (all of them)

Needs ImageMagick. Each photograph is cropped around the creature by hand-set boxes (the camera distance is fixed per creature in
tools/model_sheet.py) and enlarged with nearest-neighbour so the pixels stay square.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "playtest/models"
OUT = ROOT / "site/img/shots"
# id: (crop width, crop height, y0, three-quarter x0, side x0)   -- aspect is kept at 427:480 for a two-panel 854x480 picture
CROPS = {"draugr": (252, 283, 70, 241, 301), "draugr_lord": (252, 283, 60, 241, 301), "troll": (268, 301, 50, 233, 293), "jotunn": (280, 315, 40, 227, 287),
         "warg": (400, 450, 20, 100, 227), "fenrir": (380, 427, 35, 90, 237), "raven": (300, 337, 110, 250, 277)}
ORDER = ["draugr", "draugr_lord", "troll", "jotunn", "warg", "fenrir", "raven", "fenrir2"]


def run(*a):
    subprocess.run(a, check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (w, h, y0, x3, xs) in CROPS.items():
        panels = []
        for view, x0 in (("three-quarter", x3), ("side", xs)):
            p = OUT / f".tmp-{i}-{view}.png"
            run("convert", str(SRC / f"{i}-{view}.png"), "-crop", f"{w}x{h}+{x0}+{y0}", "+repage", "-filter", "point", "-resize", "427x480!", str(p))
            panels.append(str(p))
        run("convert", *panels, "+append", "+repage", str(OUT / f"creature-{i}.png"))
        for p in panels:
            Path(p).unlink()
    run("convert", str(OUT / "creature-fenrir.png"), "-crop", "427x480+427+0", "+repage", str(OUT / "creature-fenrir2.png"))
    tiles = []
    for i in ORDER:
        t = OUT / f".tile-{i}.png"
        run("convert", str(OUT / f"creature-{i}.png"), "-crop", "427x480+0+0", "+repage", "-resize", "213x240!", str(t))
        tiles.append(str(t))
    run("montage", *tiles, "-tile", "4x2", "-geometry", "213x240+0+0", "-background", "#10141c", str(OUT / "creatures.png"))
    for t in tiles:
        Path(t).unlink()
    (OUT / "creature-fenrir2.png").unlink()
    print("creature pictures written")


if __name__ == "__main__":
    main()
