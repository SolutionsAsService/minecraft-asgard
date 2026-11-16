#!/usr/bin/env python3
"""Author Asgard's creature models (the "model" section of each mobs/<id>.json): Draugr, Troll, Raven, Warg, Fenrir, Draugr Lord, Jotunn.

    python3 tools/gen_models.py && shadw-mod mob . gen

Edit this script, not the JSON. Uses shadwlib.figure on the model system in shadw-modding's adapters/minecraft-fabric/mobmodel.py.
Coordinates are Minecraft model pixels: +y down, -z forward, root at the feet. The Raven is a hand-written Parrot (it flies and can be
tamed), so it is an "external" spec: only its model, texture, egg, loot and language come from here.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from shadwlib.figure import Rig, box, rect  # noqa: E402

PAINTS = {
    # the dead
    "dead": {"type": "skin", "base": "#6a827c", "shade": 6}, "dead_dark": {"type": "skin", "base": "#4a5e5a", "shade": 5},
    "tunic": {"type": "cloth", "base": "#5a402c", "trim": "#34261a"}, "tunic_blue": {"type": "cloth", "base": "#2c3c58", "trim": "#18223a"},
    "pelt": {"type": "fur", "base": "#a89e88", "dark": "#6a6250", "light": "#d8d0bc"}, "beard": {"type": "fur", "base": "#b8b0a0", "dark": "#7a7262", "light": "#e8e4d8"},
    "iron": {"type": "metal", "base": "#8a8e96", "dark": "#4a4e56", "light": "#d0d4dc"}, "rust": {"type": "ridged", "base": "#96644a", "dark": "#5a3a28", "light": "#b88664"},
    "mail": {"type": "scales", "base": "#6a6e76", "dark": "#34383e", "light": "#a8acb4", "cell": 3}, "leather": {"type": "cloth", "base": "#3a2a1e", "trim": "#24180e"},
    "bone": {"type": "plain", "base": "#e6dfc8"}, "wood": {"type": "ridged", "base": "#7a5a34", "dark": "#4a3418", "light": "#9a7a4a"},
    "ice_eye": {"type": "plain", "base": "#8ae8ff"}, "gold": {"type": "metal", "base": "#d8b030", "dark": "#80640e", "light": "#fff0a0"},
    "cape": {"type": "cloth", "base": "#6a1c20", "trim": "#2c0a0c"},
    # the troll
    "troll": {"type": "skin", "base": "#5c7654", "shade": 7}, "troll_dark": {"type": "skin", "base": "#44583e", "shade": 5},
    "stone": {"type": "ridged", "base": "#7c7e7a", "dark": "#4a4c48", "light": "#a8aaa4"}, "moss": {"type": "fur", "base": "#486a32", "dark": "#2a4018", "light": "#78a050"},
    "hide": {"type": "cloth", "base": "#6e5034", "trim": "#3e2c1a"}, "tusk": {"type": "plain", "base": "#ece4cc"},
    "eye_amber": {"type": "plain", "base": "#ffc830"},
    # the wolves
    "warg": {"type": "fur", "base": "#3e3a38", "dark": "#1a1816", "light": "#6e675e"}, "warg_belly": {"type": "fur", "base": "#625a50", "dark": "#3a342c", "light": "#8a8070"},
    "warg_mane": {"type": "fur", "base": "#26221f", "dark": "#0e0c0b", "light": "#554e46"}, "nose": {"type": "plain", "base": "#0e0e10"},
    "fenrir": {"type": "fur", "base": "#7a8088", "dark": "#2c3038", "light": "#c4ccd4"}, "fenrir_belly": {"type": "fur", "base": "#a8b0b8", "dark": "#6a727a", "light": "#e0e6ec"},
    "fenrir_mane": {"type": "fur", "base": "#c8d0d8", "dark": "#7c848c", "light": "#f4f8fc"},
    "chain": {"type": "metal", "base": "#5a5e66", "dark": "#24262c", "light": "#9ea2aa"}, "ember": {"type": "plain", "base": "#ff4a30"},
    "rune": {"type": "plain", "base": "#ff7a30"}, "scar": {"type": "skin", "base": "#5a3238", "shade": 3},
    # the frost giant
    "frost": {"type": "skin", "base": "#a6c4dc", "shade": 5}, "frost_dark": {"type": "skin", "base": "#6e92b4", "shade": 4},
    "ice": {"type": "metal", "base": "#bcdcf0", "dark": "#5a86b0", "light": "#f2faff"}, "snowpelt": {"type": "fur", "base": "#e8eef4", "dark": "#a8b8c8", "light": "#ffffff"},
    "frost_cloth": {"type": "cloth", "base": "#3a5a82", "trim": "#1c2e4a"}, "frost_eye": {"type": "plain", "base": "#e8f8ff"},
    # the raven
    "raven": {"type": "skin", "base": "#14161e", "shade": 3}, "raven_sheen": {"type": "skin", "base": "#222a44", "shade": 4}, "raven_wing": {"type": "ridged", "base": "#171a26", "dark": "#0c0d14", "light": "#2c3558"},
    "beak": {"type": "plain", "base": "#2a2a30"}, "beak_light": {"type": "plain", "base": "#4a4a52"}, "claw": {"type": "plain", "base": "#3a3438"}, "raven_eye": {"type": "plain", "base": "#e8e8f0"},
}


def part_of(r, name):
    return next(p for p in r.parts if p["name"] == name)


def set_head(r, boxes):
    part_of(r, "head")["boxes"] = boxes


def add(r, name, *boxes):
    part_of(r, name)["boxes"].extend(boxes)


def held(r, hand, name, pivot, rot, boxes):
    return r.part(name, hand, pivot, rot, boxes)


# ------------------------------------------------------------------ draugr
def helm(r, w=8, hh=8, d=8, horns=False, crest=False, face="open"):
    """An iron cap with a nose guard and cheek plates on the standard head (y from -(hh-2) to +2)."""
    top = -hh + 2
    b = [box((-w / 2 - 0.2, top - 0.6, -d / 2 - 0.2), (w + 0.4, 3.4, d + 0.4), "iron"),
         box((-w / 2 - 0.35, top + 2.6, -d / 2 - 0.35), (w + 0.7, 0.9, d + 0.7), "rust"),
         box((-0.5, top + 2.8, -d / 2 - 0.7), (1, 3.4, 0.9), "iron"),
         box((-w / 2 - 0.3, top + 3.2, -d / 2 + 1.5), (0.8, 3.2, 3.6), "iron"), box((w / 2 - 0.5, top + 3.2, -d / 2 + 1.5), (0.8, 3.2, 3.6), "iron")]
    if crest:
        b.append(box((-0.6, top - 1.8, -d / 2 + 0.5), (1.2, 1.6, d - 1), "rust"))
    return b


def draugr_eyes(w=8):
    return [rect("front", 1, 2, 2, 1, "#101820"), rect("front", w - 3, 2, 2, 1, "#101820"), rect("front", 1, 3, 2, 1, "#8ae8ff"), rect("front", w - 3, 3, 2, 1, "#8ae8ff"),
            rect("front", 2, 5, 4, 1, "#2a1c1c")]


def draugr(lord=False):
    r = Rig(PAINTS)
    big = lord
    n = r.biped("dead", cloth="leather", head_paint="dead", head=None, head_decals=draugr_eyes(), hip_y=-12, chest=(9, 7, 4.5) if big else (8, 7, 4), waist=(6, 5, 3),
                arm_len=(5, 5), stance=-50, arm_pose={"l": ((-40, 0, 6), (-30, 0, 0)), "r": ((-62, 0, -6), (-18, 0, 0))}, swing_arm="r", arm_paint="dead_dark",
                shin_paint="tunic", thigh_paint="tunic", body_paint="tunic", chest_paint="mail", hunch=7, foot_paint="leather", foot_len=5.5, shoulder=True, walk=0.8)
    # the head: skull, iron cap, nose guard, cheek plates, and a braided beard
    hb = part_of(r, "head")["boxes"]
    hb[0]["decals"] = draugr_eyes()
    hb.extend(helm(r, crest=lord, horns=lord))
    hb.append(box((-3.2, 1.2, -4.5), (6.4, 3.8, 1.2), "beard"))
    hb.append(box((-2.4, 3.6, -4.2), (4.8, 2.4, 1.0), "beard", 0.0))
    hb.append(box((-0.8, 5.4, -4.0), (1.6, 2.0, 0.8), "beard"))
    # rot on the body: a gap in the mail, ribs
    add(r, "chest", box((-3.8, -6.2, -2.4), (2.2, 3, 0.6), "dead_dark", 0.0), box((-4.6, -7.2, -2.6), (9.2, 1.6, 5.2), "pelt"))
    add(r, "body", box((-3.2, -2.2, -1.7), (6.4, 1.2, 3.4), "leather", 0.3))      # belt
    # a torn cape from the shoulders
    r.part("cape", "chest", (0, -6.4, 2.4), (8, 0, 0), [box((-4.2, 0, 0), (8.4, 12 if big else 10, 0.8), "cape" if big else "tunic_blue")])
    r.anim("cape", "sway", axis="x", amp=0.06, freq=0.08, walk_amp=0.25)
    # the weapon: an axe in the right hand, a round shield strapped on the left forearm
    if lord:
        held(r, "hand_r", "greataxe", (0, 1.2, -1), (-84, 0, 0), [box((-0.6, -1, -0.6), (1.2, 17, 1.2), "wood"), box((-0.6, -4.5, -0.6), (1.2, 3, 1.2), "leather", 0.3),
                                                                  box((-0.5, 11.2, -4.5), (1.0, 7, 5.5), "iron"), box((-0.6, 10.4, -4.8), (1.2, 1.0, 5.8), "rust"), box((-0.4, 14.0, 0.3), (0.8, 3, 2.2), "iron")])
        held(r, "forearm_l", "shield", (-3.2, 2.6, 0), (0, 90, 0), [box((-4.5, -4.5, -0.6), (9, 9, 1.2), "wood"), box((-1.2, -1.2, -1.4), (2.4, 2.4, 1.0), "iron"), box((-4.5, -0.6, -0.9), (9, 1.2, 0.5), "iron"),
                                                                     box((-0.6, -4.5, -0.9), (1.2, 9, 0.5), "iron")])
        part_of(r, "chest")["boxes"] += [box((-6.4, -7.4, -3.0), (4.0, 3.4, 6.0), "iron", 0.1), box((2.4, -7.4, -3.0), (4.0, 3.4, 6.0), "iron", 0.1)]   # pauldrons
        # a horned helm: two curving horns
        for sx in (-1, 1):
            r.part(f"horn_{'l' if sx > 0 else 'r'}0", "head", (sx * 4.2, -4.4, -0.4), (0, 0, sx * 30), [box((-0.7, -3.2, -0.7), (1.4, 3.2, 1.4), "bone")])
            r.part(f"horn_{'l' if sx > 0 else 'r'}1", f"horn_{'l' if sx > 0 else 'r'}0", (0, -3.0, 0), (-18, 0, sx * 36), [box((-0.55, -3.2, -0.55), (1.1, 3.2, 1.1), "bone")])
    else:
        held(r, "hand_r", "sword", (0, 1.2, -1), (-84, 0, 0), [box((-0.6, -1, -0.6), (1.2, 4, 1.2), "leather", 0.3), box((-2.2, 2.6, -0.6), (4.4, 0.9, 1.2), "rust"),
                                                              box((-0.7, 3.4, -0.4), (1.4, 14, 0.8), "iron"), box((-0.5, 17.2, -0.35), (1.0, 2, 0.7), "iron"), box((-0.5, 5, -0.5), (1.0, 5, 1.0), "rust", 0.0)])
        held(r, "forearm_l", "shield", (-3.2, 2.6, 0), (0, 90, 0), [box((-3.6, -3.6, -0.6), (7.2, 7.2, 1.2), "wood"), box((-1.0, -1.0, -1.4), (2, 2, 0.9), "iron"), box((-3.6, -0.5, -0.9), (7.2, 1, 0.5), "rust")])
    # rags that hang from the belt
    r.part("rag_f", "body", (0, 0.5, -1.9), (4, 0, 0), [box((-2.4, 0, -0.5), (4.8, 5, 0.9), "tunic")])
    r.part("rag_b", "body", (0, 0.5, 1.9), (-4, 0, 0), [box((-2.4, 0, -0.4), (4.8, 6, 0.9), "tunic")])
    r.anim("rag_f", "sway", axis="x", amp=0.05, freq=0.1, walk_amp=0.2)
    return r.model(0.55)


# ------------------------------------------------------------------ troll
def troll():
    r = Rig(PAINTS)
    r.biped("troll", cloth="hide", head_paint="troll", hip_y=-13, chest=(14, 9, 7), waist=(10, 6, 5), arm_len=(10, 9), leg_len=(7, 6), arm_w=5, leg_w=5.4, stance=-4,
            arm_pose={"l": ((-8, 0, 7), (-8, 0, 0)), "r": ((-6, 0, -7), (-8, 0, 0))}, swing_arm="r", arm_paint="troll", shin_paint="troll_dark", thigh_paint="hide", body_paint="troll",
            chest_paint="troll", hunch=26, foot_paint="troll_dark", foot_len=7, shoulder=False, walk=0.9, hands=True)
    # the head: a heavy jaw and brow, a flat nose, an underbite of tusks, small amber eyes, moss and stone
    set_head(r, [
        box((-4.6, -5.6, -4.8), (9.2, 6.4, 8.6), "troll", 0.0, [rect("front", 1, 3, 2, 1, "#2a1c10"), rect("front", 6, 3, 2, 1, "#2a1c10"), rect("front", 1, 4, 2, 1, "#ffc830"), rect("front", 6, 4, 2, 1, "#ffc830"),
                                                              rect("front", 0, 2, 9, 1, "#34462e")]),
        box((-4.2, 0.2, -5.4), (8.4, 3.2, 7.4), "troll_dark"), box((-1.8, -2.2, -6.2), (3.6, 3.0, 1.6), "troll_dark"),
        box((-4.9, -3.6, -4.6), (9.8, 1.6, 2.4), "troll_dark"),
        box((-2.6, -6.8, -2.0), (4.6, 1.6, 4.6), "moss"), box((1.4, -6.4, 0.6), (3.0, 1.2, 3.0), "moss"),
        box((-3.6, -1.2, -6.0), (1.0, 2.6, 0.9), "tusk"), box((2.6, -1.2, -6.0), (1.0, 2.6, 0.9), "tusk"),
        box((-3.2, 0.6, -5.6), (6.4, 1.0, 0.8), "tusk", 0.0),
        box((-5.4, -3.2, -1.4), (1.4, 2.4, 1.8), "troll"), box((4.0, -3.2, -1.4), (1.4, 2.4, 1.8), "troll"),     # ears
    ])
    # stone growing out of the back, the shoulders and the right forearm; a moss mat across the spine
    add(r, "chest", box((-6.4, -9.2, -2.0), (5.2, 3.6, 5.4), "stone", 0.2), box((1.4, -9.8, -1.0), (4.6, 3.6, 5.0), "stone", 0.2), box((-1.6, -10.4, 1.6), (4.0, 2.4, 3.6), "stone", 0.1),
        box((-5.8, -6.2, 3.0), (11.6, 1.6, 1.0), "moss"), box((-4.2, -3.4, 3.0), (8.4, 1.6, 1.0), "moss"))
    add(r, "body", box((-5.4, -4.2, -3.2), (10.8, 2.0, 6.4), "hide", 0.5), box((-1.4, -5.0, -3.3), (2.8, 3.0, 0.8), "iron"))
    add(r, "arm_r", box((-2.9, 2.0, -2.9), (5.8, 3.6, 5.8), "stone", 0.0))
    add(r, "forearm_l", box((-2.8, 3.4, -2.8), (5.6, 2.4, 5.6), "stone", 0.0))
    add(r, "leg_l", box((-3.3, 1.0, -3.3), (6.6, 2.6, 6.6), "hide", 0.0))
    add(r, "leg_r", box((-3.3, 1.0, -3.3), (6.6, 2.6, 6.6), "hide", 0.0))
    # the club: a trimmed tree, held low
    held(r, "hand_r", "club", (0, 1.2, -1), (-28, 0, 0), [box((-1.0, -2, -1.0), (2.0, 7, 2.0), "leather", 0.2), box((-1.8, 4.6, -1.8), (3.6, 14, 3.6), "wood"), box((-2.8, 12, -2.8), (5.6, 7, 5.6), "wood"),
                                                         box((-3.1, 14, -0.4), (0.8, 1.6, 0.8), "iron"), box((2.3, 13, -0.4), (0.8, 1.6, 0.8), "iron"), box((-0.4, 15.2, 2.5), (0.8, 1.6, 0.8), "iron")])
    # a loincloth and a pouch
    r.part("cloth_f", "body", (0, 0.5, -2.6), (5, 0, 0), [box((-3.4, 0, -0.5), (6.8, 6, 1.0), "hide")])
    r.part("pouch", "body", (4.4, 0, -1.0), (0, 0, 12), [box((-1.4, 0, -1.4), (2.8, 3.4, 2.8), "leather"), box((-1.5, 0, -1.5), (3, 1, 3), "hide")])
    return r.model(0.9)


# ------------------------------------------------------------------ frost giant
def jotunn():
    r = Rig(PAINTS)
    r.biped("frost", cloth="frost_cloth", head_paint="frost", hip_y=-17, chest=(12, 9, 6), waist=(9, 6, 4.5), arm_len=(8, 7), leg_len=(9, 7), arm_w=4.4, leg_w=4.4, stance=-10,
            arm_pose={"l": ((-14, 0, 6), (-26, 0, 0)), "r": ((-30, 0, -6), (-40, 0, 0))}, swing_arm="r", arm_paint="frost", shin_paint="frost_cloth", thigh_paint="frost_cloth", body_paint="frost_cloth",
            chest_paint="frost", hunch=4, foot_paint="leather", foot_len=7, shoulder=True, walk=0.8)
    set_head(r, [
        box((-4.4, -6.0, -4.4), (8.8, 7.4, 8.4), "frost", 0.0, [rect("front", 1, 3, 2, 1, "#10182a"), rect("front", 6, 3, 2, 1, "#10182a"), rect("front", 1, 4, 2, 1, "#e8f8ff"), rect("front", 6, 4, 2, 1, "#e8f8ff"),
                                                              rect("front", 0, 2, 9, 1, "#6e92b4")]),
        box((-4.0, 1.0, -4.6), (8.0, 3.0, 7.2), "frost_dark"), box((-1.2, -1.8, -5.2), (2.4, 3.0, 1.2), "frost_dark"),
        box((-4.4, -6.8, -4.4), (8.8, 2.4, 8.6), "snowpelt"), box((-4.8, -4.8, -4.4), (9.6, 2.0, 3.0), "snowpelt"),   # white brow and hair
        box((-3.6, 1.8, -5.0), (7.2, 4.6, 1.6), "snowpelt"), box((-2.6, 5.4, -4.8), (5.2, 4.0, 1.4), "snowpelt"), box((-1.4, 8.4, -4.6), (2.8, 3.0, 1.2), "snowpelt"),   # long beard
        box((-5.0, -2.2, -2.0), (1.0, 6.0, 5.6), "snowpelt"), box((4.0, -2.2, -2.0), (1.0, 6.0, 5.6), "snowpelt"),
    ])
    # a crown of ice spikes
    for i, (x, h_, tilt) in enumerate(((-3.2, 4.0, 14), (-1.1, 5.6, 4), (1.1, 5.2, -4), (3.2, 3.8, -14))):
        r.part(f"spike{i}", "head", (x, -6.6, -0.4), (0, 0, tilt), [box((-0.7, -h_, -0.7), (1.4, h_, 1.4), "ice"), box((-0.4, -h_ - 1.2, -0.4), (0.8, 1.4, 0.8), "ice")])
    # a heavy fur cloak over the shoulders, ice-armour plates, a belt of bone
    add(r, "chest", box((-7.2, -9.6, -3.8), (14.4, 4.4, 7.6), "snowpelt", 0.1), box((-6.4, -6.2, 3.2), (12.8, 7.4, 1.4), "snowpelt"), box((-6.9, -7.0, -3.2), (3.6, 3.0, 6.4), "ice", 0.2), box((3.3, -7.0, -3.2), (3.6, 3.0, 6.4), "ice", 0.2))
    add(r, "body", box((-4.2, -2.6, -2.5), (8.4, 1.6, 5.0), "leather", 0.3), box((-1.0, -2.8, -2.8), (2, 2, 0.9), "bone"))
    r.part("cloak", "chest", (0, -8.6, 3.4), (6, 0, 0), [box((-6.4, 0, 0), (12.8, 14, 1.2), "snowpelt")])
    r.anim("cloak", "sway", axis="x", amp=0.04, freq=0.07, walk_amp=0.22)
    add(r, "forearm_r", box((-2.5, 0.4, -2.5), (5, 3.6, 5), "ice", 0.1))
    add(r, "forearm_l", box((-2.5, 0.4, -2.5), (5, 3.6, 5), "ice", 0.1))
    # a hammer of ice on a long haft
    held(r, "hand_r", "hammer", (0, 1.2, -1), (-70, 0, 0), [box((-0.9, -2, -0.9), (1.8, 20, 1.8), "wood"), box((-0.9, 3.0, -0.9), (1.8, 2.2, 1.8), "leather", 0.2),
                                                           box((-4.0, 16.0, -3.4), (8.0, 8.0, 6.8), "ice"), box((-3.4, 24.0, -1.0), (6.8, 1.8, 2.0), "ice"), box((-0.9, 24.0, -0.5), (1.8, 4.0, 1.0), "ice")])
    return r.model(0.9)


# ------------------------------------------------------------------ the wolves
def wolf_extras(r, scar=False, chains=False, runes=False, spines=False):
    if spines:
        for i, z in enumerate((-9, -6, -3, 0, 3, 6)):
            r.part(f"spine{i}", "body", (0, -8.4, z), (0, 0, 0), [box((-0.5, -2.2 - (i % 2), -0.5), (1.0, 2.6 + (i % 2), 1.0), "warg_mane")])


def warg():
    r = Rig(PAINTS)
    r.quadruped("warg", belly="warg_belly", mane="warg_mane", claw="bone", nose="nose", body=(9, 8.6, 18), head=(7, 6.4, 6.2), snout=(4, 3.6, 6), leg_w=3.7, ears=(2.0, 3.0), neck_rot=62, neck=(5.6, 5, 5),
                front=(4.6, 4.4, 2.4), hind=(4.8, 5.0, 2.4), tail={"segs": [(4, 2.6, 2.6, 0), (4, 3.0, 3.0, -14), (3.5, 2.4, 2.4, -14)], "paint": "warg"}, eye_glow="#ff9a20", jaw_open=10)
    for i, z in enumerate((-8, -5, -2, 1)):             # the ridge down the spine
        r.part(f"spine{i}", "body", (0, -7.8, z), (0, 0, 0), [box((-0.5, -2.0 - (i % 2), -0.5), (1.0, 2.4 + (i % 2), 1.0), "warg_mane")])
    # torn left ear, a scar across the muzzle
    add(r, "snout", box((-2.0, -2.2, -6.2), (0.4, 1.8, 6.0), "scar", 0.0))
    return r.model(0.9)


def fenrir():
    r = Rig(PAINTS)
    r.quadruped("fenrir", belly="fenrir_belly", mane="fenrir_mane", claw="bone", nose="nose", body=(10.5, 10, 22), head=(8.4, 7.4, 7), snout=(4.8, 4.2, 7), leg_w=4.8, front=(5.0, 4.8, 2.6), hind=(5.2, 5.4, 2.6), neck_rot=62,
                tail={"segs": [(5, 3.4, 3.4, 0), (5, 4.2, 4.2, -12), (4.5, 3.4, 3.4, -12), (3.5, 2.4, 2.4, -12)], "paint": "fenrir_mane"}, eye="#ffb040", eye_glow="#ff3a20", jaw_open=14, ears=(2.4, 3.6),
                neck=(7, 5.6, 6), mane_len=0.6)
    # a great mane that runs along the spine, and the scars of a hundred fights
    for i, z in enumerate((-9, -6.5, -4, -1.5, 1)):
        r.part(f"spine{i}", "body", (0, -9.0, z), (0, 0, 0), [box((-0.7, -2.6 - (i % 2) * 1.2, -0.7), (1.4, 3.0 + (i % 2) * 1.2, 1.4), "fenrir_mane")])
    add(r, "snout", box((-2.4, -2.4, -7.2), (0.4, 2.2, 7.0), "scar", 0.0))
    add(r, "body", box((-4.6, -6.2, 2.0), (0.8, 3.4, 5.0), "scar", 0.0))
    # the shackles: a broken manacle on each leg and a length of chain trailing from the front pair
    for k in ("fl", "fr", "bl", "br"):
        add(r, f"shin_{k}", box((-2.4, 0.8, -2.4), (4.8, 1.8, 4.8), "chain", 0.1), box((-2.6, 1.2, -2.6), (5.2, 0.6, 5.2), "rust"))
    for k in ("fl", "fr"):
        prev, pv = f"shin_{k}", (0, 2.4, 0)
        for i in range(5):
            nm = f"link_{k}{i}"
            r.part(nm, prev, pv, (14 if i == 0 else -6, 0, 0), [box((-1.0, 0, -0.5), (2.0, 2.2, 1.0), "chain") if i % 2 == 0 else box((-0.5, 0, -1.0), (1.0, 2.2, 2.0), "chain")])
            r.anim(nm, "sway", axis="x", amp=0.08, freq=0.16, phase=i * 0.7, walk_amp=0.3)
            prev, pv = nm, (0, 2.0, 0)
    # a collar of chain with glowing runes around the neck
    add(r, "neck", box((-3.8, -4.6, -3.4), (7.6, 1.4, 6.8), "chain", 0.1), box((-0.8, -4.6, -3.8), (1.6, 1.4, 0.6), "rune"))
    return r.model(1.2)


# ------------------------------------------------------------------ raven (a hand-written Parrot: model only)
def raven():
    r = Rig(PAINTS)
    r.part("body", "root", (0, -8.6, 0.6), (-28, 0, 0), [box((-2.6, -2.4, -3.2), (5.2, 4.6, 8.6), "raven"), box((-2.2, -1.9, -3.0), (4.4, 1.2, 8.0), "raven_sheen", 0.0), box((-2.0, 0.6, -2.4), (4.0, 1.8, 6.0), "raven")])
    r.part("chest", "body", (0, 0.2, -3.0), (24, 0, 0), [box((-2.9, -2.6, -2.4), (5.8, 5.2, 3.6), "raven"), box((-2.5, -2.4, -2.6), (5.0, 2.4, 1.0), "raven_sheen", 0.0)])
    r.part("neck", "chest", (0, -1.6, -2.0), (-12, 0, 0), [box((-1.8, -3.0, -1.6), (3.6, 3.4, 3.4), "raven"), box((-2.2, -1.6, -1.9), (4.4, 2.6, 3.6), "raven_sheen", 0.0)])
    r.part("head", "neck", (0, -2.6, 0), (14, 0, 0), [box((-1.9, -2.6, -2.6), (3.8, 3.8, 4.6), "raven", 0.0, [rect("front", 0, 1, 1, 1, "#e8e8f0"), rect("front", 3, 1, 1, 1, "#e8e8f0")]),
                                                      box((-1.5, -3.0, -1.8), (3.0, 1.0, 3.4), "raven_sheen", 0.0)])
    r.anim("head", "look", amount=0.8)
    r.part("beak_top", "head", (0, -0.9, -2.5), (6, 0, 0), [box((-0.9, -0.8, -3.6), (1.8, 1.8, 4.0), "beak"), box((-0.6, -0.9, -4.4), (1.2, 1.0, 1.4), "beak_light", 0.0)])
    r.part("beak_low", "head", (0, 0.9, -2.4), (-3, 0, 0), [box((-0.7, 0, -3.2), (1.4, 0.8, 3.4), "beak")])
    # throat hackles and a head crest: the ruffled look of a raven
    r.part("hackle", "neck", (0, 0.8, -1.4), (28, 0, 0), [box((-1.6, 0, -0.5), (3.2, 2.8, 1.0), "raven_sheen")])
    r.anim("hackle", "sway", axis="z", amp=0.04, freq=0.12)
    # tail: a fan of five feathers
    for i, ang in enumerate((-18, -9, 0, 9, 18)):
        r.part(f"tail{i}", "body", (0, 0.2, 5.0), (64 + abs(ang) * 0.1, ang, 0), [box((-0.9, 0, -0.35), (1.8, 7.6 - abs(ang) * 0.06, 0.7), "raven_wing")])
        r.anim(f"tail{i}", "sway", axis="x", amp=0.04, freq=0.1, phase=i * 0.5)
    # wings: arm, hand and a fan of five primaries; they beat in the air and fold back to the body on the ground
    for side, sx in (("l", 1), ("r", -1)):
        r.part(f"wing_{side}", "body", (sx * 2.5, -1.8, -1.0), (0, 0, 0), [box((0 if sx > 0 else -5, -0.7, -2.4), (5, 1.4, 5.0), "raven_wing"), box((0 if sx > 0 else -4.6, -1.0, -2.2), (4.6, 0.5, 4.4), "raven_sheen", 0.0)])
        r.part(f"wing_{side}2", f"wing_{side}", (sx * 5, 0, 0), (0, 0, 0), [box((0 if sx > 0 else -5, -0.6, -2.2), (5, 1.2, 4.4), "raven_wing")])
        for i in range(5):
            ln = 8.0 - abs(i - 1.5) * 0.9
            r.part(f"prim_{side}{i}", f"wing_{side}2", (sx * 4.6, 0, 1.9 - i * 1.0), (0, sx * (-6 + i * 4), 0), [box((0 if sx > 0 else -ln, -0.35, -0.6), (ln, 0.7, 1.3), "raven_wing")])
        r.anim(f"wing_{side}", "wing", axis="z", amp=0.9 * sx, freq=1.2, phase=0, rest=sx * 0.3)            # folded: laid back along the flank
        r.anim(f"wing_{side}", "wing", axis="y", amp=0.0, rest=sx * -1.45)
        r.anim(f"wing_{side}2", "wing", axis="z", amp=0.5 * sx, freq=1.2, phase=0.9, rest=0)
        r.anim(f"wing_{side}2", "wing", axis="y", amp=0.0, rest=sx * 2.4)
    # legs and feet
    for side, sx in (("l", 1), ("r", -1)):
        r.part(f"leg_{side}", "body", (sx * 1.3, 1.2, 0.6), (8, 0, 0), [box((-0.45, 0, -0.45), (0.9, 3.6, 0.9), "claw"), box((-0.8, 0.2, -0.8), (1.6, 1.4, 1.6), "raven", 0.0)])
        r.part(f"foot_{side}", f"leg_{side}", (0, 3.4, 0), (-8, 0, 0), [box((-1.1, 0, -2.2), (2.2, 0.6, 2.8), "claw"), box((-0.2, 0, 0.4), (0.4, 0.6, 1.4), "claw")])
        r.anim(f"leg_{side}", "walk", axis="x", amp=0.8, phase=0 if sx > 0 else math.pi)
    return r.model(0.4)


def build():
    return {
        "draugr": (lambda: draugr(False), {"skin": {"model": True}}),
        "draugr_lord": (lambda: draugr(True), {}),
        "troll": (troll, {}),
        "jotunn": (jotunn, {}),
        "warg": (warg, {}),
        "fenrir": (fenrir, {}),
        "raven": (raven, {}),
    }


SPECS = {
    "draugr": {"id": "draugr", "name": "Draugr", "base": "zombie", "hostile": True,
               "attributes": {"health": 34, "damage": 5, "armor": 6, "speed": 0.21, "knockback_resistance": 0.3},
               "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
               "behaviours": [],
               "spawn": {"biomes": ["minecraft:taiga", "minecraft:old_growth_pine_taiga", "minecraft:old_growth_spruce_taiga", "minecraft:snowy_taiga", "minecraft:forest", "minecraft:birch_forest",
                                    "minecraft:windswept_hills", "minecraft:windswept_forest", "minecraft:jagged_peaks", "minecraft:stony_peaks", "minecraft:frozen_peaks", "minecraft:snowy_slopes", "minecraft:grove"],
                         "weight": 14, "min": 1, "max": 3},
               "drops": [{"item": "minecraft:bone", "min": 0, "max": 2}, {"item": "minecraft:rotten_flesh", "min": 0, "max": 2}, {"item": "minecraft:iron_nugget", "min": 1, "max": 4},
                         {"item": "asgard:rune_stone", "min": 1, "max": 2, "chance": 0.25}, {"item": "asgard:yggdrasil_sap", "min": 1, "max": 1, "chance": 0.08},
                         {"item": "minecraft:iron_ingot", "min": 1, "max": 1, "chance": 0.12}],
               "egg": ["#68807a", "#8a8e96"], "tests": {"reach_distance": 12, "reach_max_seconds": 25}},
    "draugr_lord": {"id": "draugr_lord", "name": "Draugr Lord", "base": "zombie", "hostile": True,
                    "attributes": {"health": 90, "damage": 8, "armor": 10, "speed": 0.2, "knockback_resistance": 0.5, "scale": 1.2, "follow_range": 40},
                    "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
                    "behaviours": [{"type": "knockback", "strength": 1.1, "lift": 0.4}, {"type": "on_hit_effect", "effect": "minecraft:weakness", "seconds": 8, "amplifier": 0}, {"type": "enrage", "below": 0.4, "speed_bonus": 0.3, "damage_bonus": 0.3}],
                    "spawn": {"biomes": ["minecraft:old_growth_pine_taiga", "minecraft:old_growth_spruce_taiga", "minecraft:snowy_taiga", "minecraft:windswept_hills", "minecraft:jagged_peaks", "minecraft:stony_peaks"], "weight": 2, "min": 1, "max": 1},
                    "drops": [{"item": "minecraft:bone", "min": 2, "max": 4}, {"item": "minecraft:iron_ingot", "min": 2, "max": 5}, {"item": "asgard:rune_stone", "min": 2, "max": 4},
                              {"item": "minecraft:diamond", "min": 1, "max": 1, "chance": 0.15}, {"item": "asgard:yggdrasil_sap", "min": 1, "max": 2, "chance": 0.3}],
                    "egg": ["#4a5e5a", "#d8b030"], "tests": {"reach_distance": 12, "reach_max_seconds": 25}},
    "troll": {"id": "troll", "name": "Troll", "base": "zombie", "hostile": True,
              "attributes": {"health": 70, "damage": 10, "armor": 4, "speed": 0.2, "knockback_resistance": 0.7, "scale": 1.4},
              "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
              "behaviours": [{"type": "stone_by_day"}, {"type": "knockback", "strength": 1.2, "lift": 0.45}],
              "spawn": {"biomes": ["minecraft:windswept_hills", "minecraft:windswept_forest", "minecraft:jagged_peaks", "minecraft:stony_peaks", "minecraft:frozen_peaks", "minecraft:snowy_slopes", "minecraft:grove",
                                   "minecraft:taiga", "minecraft:old_growth_pine_taiga", "minecraft:old_growth_spruce_taiga", "minecraft:snowy_taiga"], "weight": 4, "min": 1, "max": 1},
              "drops": [{"item": "minecraft:cobblestone", "min": 2, "max": 6}, {"item": "minecraft:rotten_flesh", "min": 1, "max": 3}, {"item": "minecraft:bone", "min": 0, "max": 2},
                        {"item": "minecraft:iron_ingot", "min": 1, "max": 3, "chance": 0.4}, {"item": "asgard:rune_stone", "min": 2, "max": 4, "chance": 0.5},
                        {"item": "asgard:sacred_root", "min": 1, "max": 1, "chance": 0.1}, {"item": "minecraft:emerald", "min": 1, "max": 1, "chance": 0.15}],
              "egg": ["#5c7654", "#7c7e7a"], "tests": {"reach_distance": 12, "reach_max_seconds": 30}},
    "jotunn": {"id": "jotunn", "name": "Jötunn", "base": "zombie", "hostile": True,
               "attributes": {"health": 140, "damage": 12, "armor": 6, "speed": 0.19, "knockback_resistance": 0.8, "scale": 1.6, "follow_range": 40},
               "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
               "behaviours": [{"type": "slam", "cooldown_ticks": 240, "radius": 4.5, "damage": 7}, {"type": "on_hit_effect", "effect": "minecraft:slowness", "seconds": 6, "amplifier": 1},
                              {"type": "knockback", "strength": 1.3, "lift": 0.5}],
               "spawn": {"biomes": ["minecraft:snowy_slopes", "minecraft:frozen_peaks", "minecraft:jagged_peaks", "minecraft:grove", "minecraft:snowy_taiga"], "weight": 1, "min": 1, "max": 1},
               "drops": [{"item": "minecraft:ice", "min": 2, "max": 6}, {"item": "minecraft:packed_ice", "min": 1, "max": 3}, {"item": "minecraft:bone", "min": 1, "max": 3},
                         {"item": "asgard:rune_stone", "min": 2, "max": 4, "chance": 0.6}, {"item": "minecraft:diamond", "min": 1, "max": 2, "chance": 0.25}],
               "egg": ["#a6c4dc", "#e8eef4"], "tests": {"reach_distance": 12, "reach_max_seconds": 30}},
    "warg": {"id": "warg", "name": "Warg", "base": "zombie", "hostile": True,
             "attributes": {"health": 30, "damage": 6, "armor": 2, "speed": 0.3, "knockback_resistance": 0.2, "scale": 1.0},
             "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
             "size": [1.1, 1.2],
             "behaviours": [{"type": "charge", "min": 4, "max": 12, "cooldown_ticks": 120, "seconds": 2, "amplifier": 1}],
             "spawn": {"biomes": ["minecraft:taiga", "minecraft:old_growth_pine_taiga", "minecraft:old_growth_spruce_taiga", "minecraft:snowy_taiga", "minecraft:snowy_plains", "minecraft:forest",
                                  "minecraft:windswept_hills", "minecraft:grove", "minecraft:snowy_slopes"], "weight": 8, "min": 2, "max": 4},
             "drops": [{"item": "minecraft:bone", "min": 1, "max": 3}, {"item": "minecraft:leather", "min": 0, "max": 2}, {"item": "minecraft:rotten_flesh", "min": 0, "max": 2},
                       {"item": "asgard:rune_stone", "min": 1, "max": 1, "chance": 0.08}],
             "egg": ["#3e3a38", "#ff9a20"], "tests": {"reach_distance": 12, "reach_max_seconds": 15}},
    "fenrir": {"id": "fenrir", "name": "Fenrir, the Bound Wolf", "base": "zombie", "hostile": True,
               "attributes": {"health": 320, "damage": 14, "armor": 8, "speed": 0.27, "knockback_resistance": 1.0, "scale": 2.4, "follow_range": 48},
               "flags": {"sun_sensitive": False, "converts_in_water": False, "baby": False, "reinforcements": False},
               "size": [1.1, 1.3],
               "behaviours": [{"type": "boss_bar", "color": "white"}, {"type": "enrage", "below": 0.5, "speed_bonus": 0.25, "damage_bonus": 0.35},
                              {"type": "charge", "min": 6, "max": 18, "cooldown_ticks": 200, "seconds": 3, "amplifier": 2}, {"type": "slam", "cooldown_ticks": 260, "radius": 6.0, "damage": 8},
                              {"type": "knockback", "strength": 1.5, "lift": 0.5}],
               "spawn": {"biomes": ["minecraft:frozen_peaks", "minecraft:jagged_peaks", "minecraft:snowy_slopes"], "weight": 1, "min": 1, "max": 1},
               "drops": [{"item": "minecraft:bone", "min": 4, "max": 8}, {"item": "minecraft:diamond", "min": 2, "max": 5}, {"item": "minecraft:netherite_scrap", "min": 1, "max": 2},
                         {"item": "asgard:rune_stone", "min": 4, "max": 8}, {"item": "asgard:sacred_root", "min": 1, "max": 2, "chance": 0.5}, {"item": "asgard:yggdrasil_sap", "min": 2, "max": 4}],
               "egg": ["#7a8088", "#ff3a20"], "tests": {"reach_distance": 12, "reach_max_seconds": 25}},
    "raven": {"id": "raven", "name": "Raven", "base": "zombie", "hostile": False,
              "external": {"class": "dev.shadw.asgard.Raven", "type": "dev.shadw.asgard.AsgardEntities.RAVEN"},
              "attributes": {"health": 6, "speed": 0.2},
              "drops": [{"item": "minecraft:feather", "min": 1, "max": 2}, {"item": "minecraft:ender_pearl", "min": 1, "max": 1, "chance": 0.04}],
              "egg": ["#16181f", "#4a5a90"]},
}


def main():
    (ROOT / "mobs").mkdir(exist_ok=True)
    for name, (fn, _) in build().items():
        spec = json.loads(json.dumps(SPECS[name]))
        spec["model"] = fn()
        spec["skin"] = {"model": True}
        (ROOT / "mobs" / f"{name}.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(name, len(spec["model"]["parts"]), "parts")


if __name__ == "__main__":
    main()
