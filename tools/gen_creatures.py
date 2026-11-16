#!/usr/bin/env python3
"""Generate the creatures' advancements. Their models, skins, spawn eggs, loot tables and language come from mobs/*.json
(tools/gen_models.py writes those; `shadw-mod mob . gen` generates from them).

    python3 tools/gen_creatures.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src/main/resources/data/asgard"


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def adv(name, parent, icon, title, desc, trigger, conditions, frame="task"):
    write_json(DATA / "advancement" / f"{name}.json", {"parent": f"asgard:{parent}", "display": {
        "icon": {"id": icon}, "title": {"text": title}, "description": {"text": desc}, "frame": frame, "show_toast": True,
        "announce_to_chat": True, "hidden": False}, "criteria": {"c": {"trigger": trigger, "conditions": conditions}}})


def kind(t):
    return {"entity": [{"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"type": f"asgard:{t}"}}]}


def main():
    adv("draugr", "rune_circle", "minecraft:iron_axe", "Restless Dead", "Put a draugr back in its mound.", "minecraft:player_killed_entity", kind("draugr"))
    adv("troll", "thors_shrine", "minecraft:cobblestone", "Under the Bridge", "Fell a mountain troll.", "minecraft:player_killed_entity", kind("troll"), "challenge")
    adv("raven", "odin_shrine", "minecraft:feather", "Hugin or Munin", "Tame one of Odin's ravens.", "minecraft:tame_animal", kind("raven"))
    adv("draugr_lord", "draugr", "minecraft:netherite_axe", "Lord of the Mound", "Cut down a draugr lord and its greataxe.", "minecraft:player_killed_entity", kind("draugr_lord"))
    adv("warg", "draugr", "minecraft:bone", "Wolf at the Door", "Kill a warg.", "minecraft:player_killed_entity", kind("warg"))
    adv("jotunn", "troll", "minecraft:blue_ice", "Giant Slayer", "Bring down a frost giant of Jötunheimr.", "minecraft:player_killed_entity", kind("jotunn"), "challenge")
    adv("fenrir", "tyr_shrine", "minecraft:chain", "The Bound Wolf", "Kill Fenrir, who bit off Tyr's hand and broke Gleipnir.", "minecraft:player_killed_entity", kind("fenrir"), "challenge")
    print("creature advancements written")


if __name__ == "__main__":
    main()
