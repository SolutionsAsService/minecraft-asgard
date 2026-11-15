#!/usr/bin/env python3
"""Generate the worldgen data, chest loot and advancements for the six god shrines (Odin, Freyja, Loki, Freyr, Tyr, Heimdall).

    python3 tools/gen_worldgen.py

The structures themselves come from tools/gen_structures.py. Everything here is derived from this script. Stdlib only.
"""
import json
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "src/main/resources/data/asgard"
VARIANTS = 2

# name: (spacing, separation, salt, start_height, biomes, god title)
SHRINES = {
    "odin_shrine":     (30, 10, 7123401, 0,   ["#minecraft:is_mountain", "#minecraft:is_taiga", "minecraft:windswept_hills"]),
    "freyja_shrine":   (28, 10, 7123402, 0,   ["minecraft:flower_forest", "minecraft:meadow", "minecraft:cherry_grove", "minecraft:plains", "minecraft:sunflower_plains"]),
    "loki_shrine":     (32, 10, 7123403, -14, ["#minecraft:is_forest", "#minecraft:is_taiga", "minecraft:plains", "minecraft:swamp", "minecraft:dark_forest"]),
    "freyr_shrine":    (28, 10, 7123404, 0,   ["minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:forest"]),
    "tyr_shrine":      (30, 10, 7123405, 0,   ["minecraft:plains", "minecraft:savanna", "#minecraft:is_badlands", "minecraft:windswept_hills"]),
    "heimdall_shrine": (34, 12, 7123406, 0,   ["#minecraft:is_mountain", "#minecraft:is_hill", "minecraft:windswept_hills"]),
}


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def item(name, weight, lo=None, hi=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    if lo is not None:
        e["functions"] = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e


def potion(pid, weight):
    return {"type": "minecraft:item", "name": "minecraft:potion", "weight": weight,
            "functions": [{"function": "minecraft:set_potion", "id": pid}]}


LOOT = {
    "odin_shrine": [item("asgard:mimir_glass", 4, 1, 2), item("minecraft:ender_eye", 4, 2, 4), item("minecraft:experience_bottle", 5, 2, 6),
                    item("minecraft:gold_ingot", 4, 2, 6), item("asgard:rune_stone", 4, 3, 8), item("asgard:yggdrasil_sap", 3, 1, 2),
                    item("asgard:sacred_root", 1), potion("asgard:allfathers_eye", 2), potion("asgard:mimirs_knowledge", 1)],
    "freyja_shrine": [item("asgard:valhalla_honey", 4, 1, 3), item("minecraft:pink_petals", 5, 4, 12), item("minecraft:peony", 4, 1, 3),
                      item("minecraft:amethyst_shard", 5, 3, 9), item("minecraft:gold_ingot", 3, 2, 5), item("asgard:yggdrasil_sap", 3, 1, 2),
                      item("asgard:sacred_root", 1), potion("asgard:hall_mead", 2), potion("asgard:idunns_elixir", 1)],
    "loki_shrine": [item("asgard:serpent_scale", 4, 1, 3), item("minecraft:fermented_spider_eye", 4, 1, 3), item("minecraft:ender_pearl", 4, 1, 3),
                    item("minecraft:gold_ingot", 4, 2, 6), item("minecraft:slime_ball", 4, 3, 8), item("asgard:yggdrasil_sap", 3, 1, 2),
                    item("asgard:sacred_root", 1), potion("asgard:trickster_draught", 2)],
    "freyr_shrine": [item("asgard:golden_sheaf", 5, 1, 3), item("minecraft:wheat", 6, 6, 16), item("minecraft:golden_carrot", 4, 2, 6),
                     item("minecraft:bread", 4, 3, 8), item("minecraft:hay_block", 3, 1, 3), item("asgard:yggdrasil_sap", 3, 1, 2),
                     item("asgard:sacred_root", 1), potion("asgard:freyrs_blessing", 2)],
    "tyr_shrine": [item("asgard:oath_stone", 4, 1, 2), item("minecraft:iron_ingot", 6, 3, 9), item("minecraft:diamond", 1, 1, 2),
                   item("minecraft:shield", 2), item("minecraft:gold_ingot", 3, 2, 5), item("asgard:yggdrasil_sap", 3, 1, 2),
                   item("asgard:sacred_root", 1), potion("asgard:tyrs_courage", 2), potion("asgard:thors_valor", 1)],
    "heimdall_shrine": [item("asgard:rainbow_shard", 4, 1, 3), item("minecraft:amethyst_shard", 5, 3, 9), item("minecraft:spyglass", 2),
                        item("minecraft:gold_ingot", 4, 2, 6), item("minecraft:experience_bottle", 3, 2, 5), item("asgard:yggdrasil_sap", 3, 1, 2),
                        item("asgard:sacred_root", 1), potion("asgard:bifrost_spark", 2)],
}

SPAWNS = {
    "odin_shrine": {"creature": {"bounding_box": "full", "spawns": [{"type": "asgard:raven", "weight": 10, "minCount": 2, "maxCount": 3}]}},
    "tyr_shrine": {"monster": {"bounding_box": "piece", "spawns": [{"type": "asgard:draugr", "weight": 10, "minCount": 2, "maxCount": 3},
                                                                    {"type": "asgard:troll", "weight": 2, "minCount": 1, "maxCount": 1}]}},
}

ADV = {  # name: (parent, icon, title, description, frame)
    "odin_shrine": ("rune_circle", "asgard:odin_altar", "The Allfather's Monument", "Find Odin's shrine.", "task"),
    "freyja_shrine": ("rune_circle", "asgard:freyja_altar", "A Garden of Gold and Crystal", "Find Freyja's shrine.", "task"),
    "loki_shrine": ("rune_circle", "asgard:loki_altar", "Under the Ground, Smiling", "Find Loki's hidden altar.", "task"),
    "freyr_shrine": ("rune_circle", "asgard:freyr_altar", "The Harvest Lord", "Find Freyr's shrine.", "task"),
    "tyr_shrine": ("rune_circle", "asgard:tyr_altar", "Where the Oath Was Kept", "Find Tyr's shrine.", "task"),
    "heimdall_shrine": ("rune_circle", "asgard:heimdall_altar", "The Watchman's Tower", "Find Heimdall's shrine.", "task"),
}


def main():
    for name, (spacing, sep, salt, start, biomes) in SHRINES.items():
        write(D / "worldgen/structure" / f"{name}.json", {
            "type": "minecraft:jigsaw", "biomes": f"#asgard:has_structure/{name}", "step": "surface_structures",
            "spawn_overrides": SPAWNS.get(name, {}), "terrain_adaptation": "beard_thin", "start_pool": f"asgard:{name}", "size": 1,
            "start_height": {"absolute": start}, "project_start_to_heightmap": "WORLD_SURFACE_WG",
            "max_distance_from_center": 40, "use_expansion_hack": False})
        write(D / "worldgen/template_pool" / f"{name}.json", {"fallback": "minecraft:empty", "elements": [
            {"weight": 1, "element": {"element_type": "minecraft:single_pool_element", "location": f"asgard:{name}_{i}",
                                      "processors": "minecraft:empty", "projection": "rigid"}} for i in range(VARIANTS)]})
        write(D / "worldgen/structure_set" / f"{name}.json", {
            "structures": [{"structure": f"asgard:{name}", "weight": 1}],
            "placement": {"type": "minecraft:random_spread", "spacing": spacing, "separation": sep, "salt": salt}})
        write(D / "tags/worldgen/biome/has_structure" / f"{name}.json", {"values": biomes})
        write(D / "loot_table/chests" / f"{name}.json", {"type": "minecraft:chest", "pools": [
            {"rolls": {"type": "minecraft:uniform", "min": 4, "max": 7}, "entries": LOOT[name]}]})
        parent, icon, title, desc, frame = ADV[name]
        write(D / "advancement" / f"{name}.json", {
            "parent": f"asgard:{parent}",
            "display": {"icon": {"id": icon}, "title": {"text": title}, "description": {"text": desc}, "frame": frame,
                        "show_toast": True, "announce_to_chat": True, "hidden": False},
            "criteria": {"c": {"trigger": "minecraft:location", "conditions": {"player": [{
                "condition": "minecraft:entity_properties", "entity": "this",
                "predicate": {"location": {"structures": f"asgard:{name}"}}}]}}}})
    print("worldgen data written for", len(SHRINES), "shrines")


if __name__ == "__main__":
    main()
