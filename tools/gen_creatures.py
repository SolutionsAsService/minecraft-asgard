#!/usr/bin/env python3
"""Generate the creatures' skins, spawn egg models, loot tables and advancements.

    python3 tools/gen_creatures.py

The draugr and the troll use the zombie model (a 64 by 64 skin); the raven uses the parrot model (32 by 32). The skins are
painted here, face by face, on the standard layout. Everything is derived from this script. Stdlib only.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_assets as ga  # noqa: E402  (write_png)

ROOT = HERE.parent
ASSETS = ROOT / "src/main/resources/assets/asgard"
DATA = ROOT / "src/main/resources/data/asgard"


def h(x, y, salt=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)) % 100


def shade(c, d):
    return tuple(max(0, min(255, v + d)) for v in c[:3])


class Skin:
    def __init__(self, w, h_):
        self.w, self.h = w, h_
        self.px = {}

    def fill(self, x0, y0, x1, y1, c, noise=0, salt=1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = ((h(x, y, salt) % (2 * noise + 1)) - noise) if noise else 0
                self.px[(x, y)] = shade(c, d)

    def put(self, x, y, c):
        self.px[(x, y)] = c

    def save(self, path):
        pix = [(*self.px[(x, y)], 255) if (x, y) in self.px else (0, 0, 0, 0) for y in range(self.h) for x in range(self.w)]   # unpainted = transparent (the hat layer)
        path.parent.mkdir(parents=True, exist_ok=True)
        ga.write_png(path, self.w, self.h, pix)


# face rectangles on the standard 64 by 64 layout: (x0, y0, x1, y1)
HEAD = dict(top=(8, 0, 15, 7), bottom=(16, 0, 23, 7), right=(0, 8, 7, 15), front=(8, 8, 15, 15), left=(16, 8, 23, 15), back=(24, 8, 31, 15))
BODY = dict(top=(20, 16, 27, 19), bottom=(28, 16, 35, 19), right=(16, 20, 19, 31), front=(20, 20, 27, 31), left=(28, 20, 31, 31), back=(32, 20, 39, 31))
RARM = dict(top=(44, 16, 47, 19), bottom=(48, 16, 51, 19), right=(40, 20, 43, 31), front=(44, 20, 47, 31), left=(48, 20, 51, 31), back=(52, 20, 55, 31))
LARM = dict(top=(36, 48, 39, 51), bottom=(40, 48, 43, 51), right=(32, 52, 35, 63), front=(36, 52, 39, 63), left=(40, 52, 43, 63), back=(44, 52, 47, 63))
RLEG = dict(top=(4, 16, 7, 19), bottom=(8, 16, 11, 19), right=(0, 20, 3, 31), front=(4, 20, 7, 31), left=(8, 20, 11, 31), back=(12, 20, 15, 31))
LLEG = dict(top=(20, 48, 23, 51), bottom=(24, 48, 27, 51), right=(16, 52, 19, 63), front=(20, 52, 23, 63), left=(24, 52, 27, 63), back=(28, 52, 31, 63))
SIDES = ("right", "front", "left", "back")


def draugr():
    s = Skin(64, 64)
    skin, rot = (104, 126, 122), (70, 90, 70)
    iron, rust = (150, 152, 158), (150, 100, 68)
    tunic, belt, fur = (88, 62, 44), (40, 28, 20), (170, 160, 140)
    trousers, boots = (58, 52, 50), (36, 30, 28)
    for f in HEAD.values():
        s.fill(*f, skin, 6, 1)
    x0, y0, x1, y1 = HEAD["top"]; s.fill(x0, y0, x1, y1, iron, 6, 2)
    for f in SIDES:
        x0, y0, x1, y1 = HEAD[f]
        s.fill(x0, y0, x1, y0 + 2, iron, 6, 3)
        s.fill(x0, y0 + 2, x1, y0 + 2, rust, 8, 4)
    fx0, fy0, fx1, fy1 = HEAD["front"]
    s.fill(fx0 + 3, fy0 + 3, fx0 + 4, fy0 + 5, iron, 4, 5)                    # nose guard
    for ex in (fx0 + 1, fx0 + 5):                                              # glowing eyes
        s.put(ex, fy0 + 3, (40, 60, 70)); s.put(ex + 1, fy0 + 3, (40, 60, 70))
        s.put(ex, fy0 + 4, (140, 230, 255)); s.put(ex + 1, fy0 + 4, (140, 230, 255))
    s.fill(fx0 + 2, fy0 + 6, fx0 + 5, fy0 + 6, (50, 40, 40))                   # mouth
    s.fill(fx0 + 1, fy0 + 7, fx0 + 6, fy0 + 7, fur, 8, 6)                      # beard
    for f in BODY.values():
        s.fill(*f, tunic, 7, 7)
    x0, y0, x1, y1 = BODY["front"]; s.fill(x0, y0, x1, y0 + 1, fur, 8, 8); s.fill(x0, y1 - 2, x1, y1 - 1, belt, 3, 9)
    for f in SIDES:
        x0, y0, x1, y1 = BODY[f]; s.fill(x0, y1 - 2, x1, y1 - 1, belt, 3, 10)
    x0, y0, x1, y1 = BODY["top"]; s.fill(x0, y0, x1, y1, fur, 8, 11)
    for arm in (RARM, LARM):
        for name, (x0, y0, x1, y1) in arm.items():
            s.fill(x0, y0, x1, y1, skin, 6, 12)
            if name in SIDES:
                s.fill(x0, y0, x1, y0 + 4, tunic, 6, 13)
        x0, y0, x1, y1 = arm["top"]; s.fill(x0, y0, x1, y1, tunic, 6, 14)
    for leg in (RLEG, LLEG):
        for name, (x0, y0, x1, y1) in leg.items():
            s.fill(x0, y0, x1, y1, trousers, 5, 15)
            if name in SIDES:
                s.fill(x0, y1 - 2, x1, y1, boots, 4, 16)
    for (x, y), c in list(s.px.items()):                                       # rot spots on skin
        if c[0] < 120 and c[1] > 105 and h(x, y, 17) < 6:
            s.put(x, y, rot)
    return s


def troll():
    s = Skin(64, 64)
    skin, dark = (92, 118, 84), (68, 90, 62)
    stone, moss = (122, 124, 122), (72, 104, 50)
    hide, strap = (110, 80, 52), (70, 50, 34)
    for f in HEAD.values():
        s.fill(*f, skin, 7, 21)
    x0, y0, x1, y1 = HEAD["top"]; s.fill(x0, y0, x1, y1, moss, 10, 22)
    for f in SIDES:
        x0, y0, x1, y1 = HEAD[f]; s.fill(x0, y0, x1, y0 + 1, moss, 10, 23)
    fx0, fy0, fx1, fy1 = HEAD["front"]
    s.fill(fx0, fy0 + 2, fx1, fy0 + 2, dark)                                   # brow
    for ex in (fx0 + 1, fx0 + 5):
        s.put(ex, fy0 + 3, (250, 210, 60)); s.put(ex + 1, fy0 + 3, (250, 210, 60))
    s.fill(fx0 + 3, fy0 + 4, fx0 + 4, fy0 + 5, dark)                           # nose
    s.fill(fx0 + 1, fy0 + 6, fx0 + 6, fy0 + 6, (50, 36, 34))                   # mouth
    s.put(fx0 + 1, fy0 + 5, (235, 230, 210)); s.put(fx0 + 6, fy0 + 5, (235, 230, 210))   # tusks
    for name in ("front", "left", "right"):                                    # stone cheeks
        x0, y0, x1, y1 = HEAD[name]
        for y in range(y0 + 3, y1 + 1):
            for x in range(x0, x1 + 1):
                if h(x, y, 24) < 14:
                    s.put(x, y, stone)
    for f in BODY.values():
        s.fill(*f, skin, 7, 25)
    x0, y0, x1, y1 = BODY["front"]; s.fill(x0 + 2, y0 + 3, x1 - 2, y1 - 6, (110, 132, 98), 6, 26)
    for i in range(8):
        s.put(x0 + i, y0 + 2 + i, strap)
    for arm in (RARM, LARM):
        for name, (x0, y0, x1, y1) in arm.items():
            s.fill(x0, y0, x1, y1, skin, 7, 27)
            if name in SIDES:
                s.fill(x0, y1 - 3, x1, y1 - 2, strap)
                for y in range(y0, y1):
                    for x in range(x0, x1 + 1):
                        if h(x, y, 28) < 9:
                            s.put(x, y, stone)
    for leg in (RLEG, LLEG):
        for name, (x0, y0, x1, y1) in leg.items():
            s.fill(x0, y0, x1, y1, skin, 7, 29)
            if name in SIDES or name == "top":
                s.fill(x0, y0, x1, y0 + 4, hide, 6, 30)
    for (x, y), c in list(s.px.items()):
        if c[1] > 100 and h(x, y, 31) < 5:
            s.put(x, y, moss)
    return s


def raven():
    s = Skin(32, 32)
    for y in range(32):
        for x in range(32):
            n = h(x, y, 33)
            c = (22, 24, 34)
            c = (40, 48, 74) if n < 8 else shade(c, (n % 9) - 4)
            s.put(x, y, c)
    return s


EGGS = {"draugr": ((104, 126, 122), (150, 152, 158)), "troll": ((92, 118, 84), (122, 124, 122)), "raven": ((22, 24, 34), (60, 72, 112))}


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def item(name, weight, lo=None, hi=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    if lo is not None:
        e["functions"] = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e


def chance(entries, c):
    return {"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:random_chance", "chance": c}], "entries": entries}


def pool(entries, lo, hi):
    return {"rolls": {"type": "minecraft:uniform", "min": lo, "max": hi}, "entries": entries}


def adv(name, parent, icon, title, desc, trigger, conditions, frame="task"):
    write_json(DATA / "advancement" / f"{name}.json", {"parent": f"asgard:{parent}", "display": {
        "icon": {"id": icon}, "title": {"text": title}, "description": {"text": desc}, "frame": frame, "show_toast": True,
        "announce_to_chat": True, "hidden": False}, "criteria": {"c": {"trigger": trigger, "conditions": conditions}}})


def kind(t):
    return {"entity": [{"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"type": f"asgard:{t}"}}]}


def main():
    draugr().save(ASSETS / "textures/entity/draugr.png")
    troll().save(ASSETS / "textures/entity/troll.png")
    raven().save(ASSETS / "textures/entity/raven.png")
    for name, (a, b) in EGGS.items():
        tint = lambda c: c[0] * 65536 + c[1] * 256 + c[2]
        write_json(ASSETS / "models/item" / f"{name}_spawn_egg.json", {"parent": "minecraft:item/template_spawn_egg"})
        write_json(ASSETS / "items" / f"{name}_spawn_egg.json", {"model": {"type": "minecraft:model", "model": f"asgard:item/{name}_spawn_egg",
                   "tints": [{"type": "minecraft:constant", "value": tint(a)}, {"type": "minecraft:constant", "value": tint(b)}]}})
    loot = DATA / "loot_table/entities"
    write_json(loot / "draugr.json", {"type": "minecraft:entity", "pools": [
        pool([item("minecraft:bone", 5, 0, 2), item("minecraft:rotten_flesh", 5, 0, 2), item("minecraft:iron_nugget", 4, 1, 4)], 1, 2),
        chance([item("asgard:rune_stone", 1, 1, 2)], 0.25), chance([item("asgard:yggdrasil_sap", 1)], 0.08),
        chance([item("minecraft:iron_ingot", 1)], 0.12)]})
    write_json(loot / "troll.json", {"type": "minecraft:entity", "pools": [
        pool([item("minecraft:cobblestone", 5, 2, 6), item("minecraft:rotten_flesh", 4, 1, 3), item("minecraft:bone", 3, 0, 2)], 2, 3),
        chance([item("minecraft:iron_ingot", 1, 1, 3)], 0.4), chance([item("asgard:rune_stone", 1, 2, 4)], 0.5),
        chance([item("asgard:sacred_root", 1)], 0.1), chance([item("minecraft:emerald", 1)], 0.15)]})
    write_json(loot / "raven.json", {"type": "minecraft:entity", "pools": [
        pool([item("minecraft:feather", 1, 1, 2)], 1, 1), chance([item("minecraft:ender_pearl", 1)], 0.04)]})
    adv("draugr", "rune_circle", "minecraft:iron_axe", "Restless Dead", "Put a draugr back in its mound.", "minecraft:player_killed_entity", kind("draugr"))
    adv("troll", "thors_shrine", "minecraft:cobblestone", "Under the Bridge", "Fell a mountain troll.", "minecraft:player_killed_entity", kind("troll"), "challenge")
    adv("raven", "odin_shrine", "minecraft:feather", "Hugin or Munin", "Tame one of Odin's ravens.", "minecraft:tame_animal", kind("raven"))
    print("creature assets, loot and advancements written")


if __name__ == "__main__":
    main()
