#!/usr/bin/env python3
"""Generate the assets for the non-potion content: relics, Yggdrasil items and blocks, the rune stone.

    python3 tools/gen_content.py && python3 tools/gen_assets.py

Writes textures, item and block models, block states, item definitions (Minecraft 1.21.4 needs
assets/<ns>/items/<id>.json) and tools/content_lang.json, which gen_assets.py merges into the language file.
Everything is derived from this script; edit it, not the output. Stdlib only.
"""

import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_assets as ga  # noqa: E402  (write_png)

ROOT = HERE.parent
NS = "asgard"
ASSETS = ROOT / "src/main/resources/assets" / NS

DYE = dict(white=(249, 255, 254), orange=(249, 128, 29), yellow=(254, 216, 61), light_blue=(58, 179, 218),
           light_gray=(157, 157, 151), gray=(71, 79, 82), brown=(131, 84, 50), lime=(128, 199, 31),
           green=(94, 124, 22), red=(176, 46, 38))
INK = (11, 11, 13)


class Pix:
    def __init__(self):
        self.p = {}

    def put(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.p[(x, y)] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(16):
            for x in range(16):
                if math.hypot(x - cx, y - cy) <= r:
                    self.put(x, y, c)

    def erase_disc(self, cx, cy, r):
        for k in [k for k in self.p if math.hypot(k[0] - cx, k[1] - cy) <= r]:
            del self.p[k]

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = max(abs(x1 - x0), abs(y1 - y0)) * 2 or 1
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            for dx in range(thick):
                for dy in range(thick):
                    self.put(x + dx, y + dy, c)

    def outline(self, c=INK):
        add = {}
        for (x, y) in self.p:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                k = (x + dx, y + dy)
                if k not in self.p and 0 <= k[0] < 16 and 0 <= k[1] < 16:
                    add[k] = c
        self.p.update(add)

    def save(self, path):
        px = [self.p.get((x, y), (0, 0, 0, 0)) for y in range(16) for x in range(16)]
        px = [c if len(c) == 4 else (*c, 255) for c in px]
        path.parent.mkdir(parents=True, exist_ok=True)
        ga.write_png(path, 16, 16, px)


def h(x, y, salt=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)) % 100


def shade(c, d):
    return tuple(max(0, min(255, v + d)) for v in c)


# ---------- item sprites ----------

def mjolnir():
    p = Pix()
    p.rect(6, 1, 14, 6, DYE["light_gray"])
    p.rect(6, 1, 14, 1, DYE["white"])
    p.rect(6, 6, 14, 6, DYE["gray"])
    p.rect(9, 3, 11, 4, DYE["light_blue"])
    p.put(10, 2, DYE["light_blue"]); p.put(10, 5, DYE["light_blue"])
    p.line(7, 7, 1, 13, DYE["brown"], 2)
    p.rect(0, 13, 2, 15, DYE["gray"])
    p.outline()
    return p


def gungnir():
    p = Pix()
    p.line(1, 14, 11, 4, DYE["brown"], 2)
    p.line(9, 6, 10, 5, DYE["yellow"], 2)
    p.rect(12, 1, 14, 3, DYE["white"])
    p.put(11, 3, DYE["light_gray"]); p.put(12, 4, DYE["light_gray"]); p.put(13, 0, DYE["white"])
    p.put(14, 4, DYE["light_gray"]); p.put(11, 0, DYE["light_gray"])
    p.outline()
    return p


def gjallarhorn():
    p = Pix()
    p.disc(7, 8, 6, DYE["yellow"])
    p.erase_disc(10, 5, 5)
    p.rect(11, 2, 13, 4, DYE["orange"]); p.put(12, 3, DYE["yellow"])
    p.line(2, 10, 5, 13, DYE["orange"])
    p.outline()
    return p


# ---------- block textures (opaque 16x16) ----------

def tex(fn):
    p = Pix()
    for y in range(16):
        for x in range(16):
            p.put(x, y, fn(x, y))
    return p


def log_side(x, y):
    base = (91, 62, 36)
    c = shade(base, -18 if x % 4 == 0 else (8 if x % 4 == 2 else 0))
    if h(x, y, 1) < 9:
        c = (63, 107, 42)
    elif h(x, y, 2) < 14:
        c = shade(base, -30)
    return c


def log_top(x, y):
    d = math.hypot(x - 7.5, y - 7.5)
    if d > 7.4:
        return (91, 62, 36)
    ring = int(d) % 2
    return (169, 124, 80) if ring == 0 else (139, 94, 52)


def leaves(x, y):
    n = h(x, y, 3)
    if n < 4:
        return DYE["yellow"] if h(x, y, 7) < 50 else (79, 174, 74)
    if n < 30:
        return (79, 174, 74)
    if n < 60:
        return (47, 125, 50)
    return (31, 90, 36)


def rune_stone(x, y):
    n = h(x, y, 4)
    base = (108, 110, 114)
    c = shade(base, (n % 9) - 4)
    if x in (0, 15) or y in (0, 15):
        c = (74, 76, 80)
    rune = {(7, y) for y in range(3, 13)} | {(8, y) for y in range(3, 13)} | \
           {(9, 5), (10, 6), (10, 7), (9, 8)} | {(9, 4), (11, 6), (11, 7)}
    if (x, y) in rune:
        c = DYE["yellow"]
    return c


# ---------- writers ----------

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def item_def(name, model):
    write_json(ASSETS / "items" / f"{name}.json", {"model": {"type": "minecraft:model", "model": model}})


LANG = {
    "item.asgard.mjolnir": "Mjölnir",
    "item.asgard.mjolnir.lore": "Thor's hammer. Right-click to call lightning where you look.",
    "item.asgard.gungnir": "Gungnir",
    "item.asgard.gungnir.lore": "Odin's spear. What it strikes, it marks for all to see.",
    "item.asgard.gjallarhorn": "Gjallarhorn",
    "item.asgard.gjallarhorn.lore": "Heimdall's horn. Right-click to reveal what is near, and to run.",
    "item.asgard.yggdrasil_leaf": "Yggdrasil Leaf",
    "item.asgard.yggdrasil_leaf.lore": "A leaf from the world tree. The ingredient of the Blessing.",
    "item.asgard.yggdrasil_fruit": "Yggdrasil Fruit",
    "item.asgard.yggdrasil_fruit.lore": "Fruit of the world tree. It feeds the body and little else.",
    "block.asgard.yggdrasil_log": "Yggdrasil Log",
    "block.asgard.yggdrasil_leaves": "Yggdrasil Leaves",
    "block.asgard.rune_stone": "Rune Stone",
    "item.minecraft.potion.effect.blessing": "Potion of Blessing",
    "item.minecraft.splash_potion.effect.blessing": "Splash Blessing",
    "item.minecraft.lingering_potion.effect.blessing": "Lingering Blessing",
}


def main():
    # item sprites
    for name, art in (("mjolnir", mjolnir()), ("gungnir", gungnir()), ("gjallarhorn", gjallarhorn())):
        art.save(ASSETS / "textures/item" / f"{name}.png")
    # the leaf and the fruit: reuse the sprites drawn for the example mod, copied once into this repository
    src = Path("/home/user/shadw-modding/examples/minecraft-yggdrasil/src/main/resources/assets/yggdrasil/textures/item")
    for name in ("yggdrasil_leaf", "yggdrasil_fruit"):
        dst = ASSETS / "textures/item" / f"{name}.png"
        if src.exists():
            shutil.copyfile(src / f"{name}.png", dst)
        assert dst.exists(), f"missing {dst}"
    # block textures
    tex(log_side).save(ASSETS / "textures/block/yggdrasil_log.png")
    tex(log_top).save(ASSETS / "textures/block/yggdrasil_log_top.png")
    tex(leaves).save(ASSETS / "textures/block/yggdrasil_leaves.png")
    tex(rune_stone).save(ASSETS / "textures/block/rune_stone.png")

    # item models and definitions
    for name, parent in (("mjolnir", "minecraft:item/handheld"), ("gungnir", "minecraft:item/handheld"),
                         ("gjallarhorn", "minecraft:item/generated"), ("yggdrasil_leaf", "minecraft:item/generated"),
                         ("yggdrasil_fruit", "minecraft:item/generated")):
        write_json(ASSETS / "models/item" / f"{name}.json", {"parent": parent, "textures": {"layer0": f"{NS}:item/{name}"}})
        item_def(name, f"{NS}:item/{name}")
    # block models, block states, block-item definitions
    tx = {"end": f"{NS}:block/yggdrasil_log_top", "side": f"{NS}:block/yggdrasil_log"}
    write_json(ASSETS / "models/block/yggdrasil_log.json", {"parent": "minecraft:block/cube_column", "textures": tx})
    write_json(ASSETS / "models/block/yggdrasil_log_horizontal.json",
               {"parent": "minecraft:block/cube_column_horizontal", "textures": tx})
    write_json(ASSETS / "models/block/yggdrasil_leaves.json",
               {"parent": "minecraft:block/leaves", "textures": {"all": f"{NS}:block/yggdrasil_leaves"}})
    write_json(ASSETS / "models/block/rune_stone.json",
               {"parent": "minecraft:block/cube_all", "textures": {"all": f"{NS}:block/rune_stone"}})
    write_json(ASSETS / "blockstates/yggdrasil_log.json", {"variants": {
        "axis=y": {"model": f"{NS}:block/yggdrasil_log"},
        "axis=x": {"model": f"{NS}:block/yggdrasil_log_horizontal", "x": 90, "y": 90},
        "axis=z": {"model": f"{NS}:block/yggdrasil_log_horizontal", "x": 90}}})
    write_json(ASSETS / "blockstates/yggdrasil_leaves.json", {"variants": {"": {"model": f"{NS}:block/yggdrasil_leaves"}}})
    write_json(ASSETS / "blockstates/rune_stone.json", {"variants": {"": {"model": f"{NS}:block/rune_stone"}}})
    for name in ("yggdrasil_log", "yggdrasil_leaves", "rune_stone"):
        item_def(name, f"{NS}:block/{name}")
    # language entries merged by gen_assets.py
    write_json(HERE / "content_lang.json", LANG)
    print("content assets written")


if __name__ == "__main__":
    main()
