#!/usr/bin/env python3
"""Generate block loot tables, block tags and crafting recipes for the world tree materials and the altars.

    python3 tools/gen_data.py

Everything is derived from this script; edit it, not the output. Stdlib only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src/main/resources/data"
GODS = ["thor", "odin", "freyja", "loki", "freyr", "tyr", "heimdall"]


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def drops_self(name):
    return {"type": "minecraft:block", "random_sequence": f"asgard:blocks/{name}", "pools": [{
        "rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:survives_explosion"}],
        "entries": [{"type": "minecraft:item", "name": f"asgard:{name}"}]}]}


def chance_drop(name, item, chance):
    return {"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:random_chance", "chance": chance}],
            "entries": [{"type": "minecraft:item", "name": item}]}


def tag(path, values):
    p = DATA / "minecraft/tags/block" / path
    cur = json.loads(p.read_text())["values"] if p.exists() else []
    write(p, {"replace": False, "values": sorted(set(cur) | set(values))})


def main():
    loot = DATA / "asgard/loot_table/blocks"
    for n in ["yggdrasil_heartwood", "ancient_bark"] + [f"{g}_altar" for g in GODS]:
        write(loot / f"{n}.json", drops_self(n))
    write(loot / "golden_leaves.json", {"type": "minecraft:block", "random_sequence": "asgard:blocks/golden_leaves", "pools": [
        chance_drop("golden_leaves", "asgard:yggdrasil_sap", 0.12),
        chance_drop("golden_leaves", "asgard:yggdrasil_leaf", 0.2),
        chance_drop("golden_leaves", "asgard:yggdrasil_fruit", 0.08)]})
    # the world tree's logs now sometimes give sap
    log = {"type": "minecraft:block", "random_sequence": "asgard:blocks/yggdrasil_log", "pools": [
        {"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:survives_explosion"}],
         "entries": [{"type": "minecraft:item", "name": "asgard:yggdrasil_log"}]},
        chance_drop("yggdrasil_log", "asgard:yggdrasil_sap", 0.06)]}
    write(loot / "yggdrasil_log.json", log)

    tag("leaves.json", ["asgard:golden_leaves"])
    tag("mineable/hoe.json", ["asgard:golden_leaves"])
    tag("mineable/axe.json", ["asgard:yggdrasil_heartwood", "asgard:ancient_bark"])
    tag("mineable/pickaxe.json", [f"asgard:{g}_altar" for g in GODS])

    rec = DATA / "asgard/recipe"
    write(rec / "yggdrasil_heartwood.json", {"type": "minecraft:crafting_shapeless", "category": "building", "ingredients": [
        "asgard:yggdrasil_log", "asgard:yggdrasil_log", "asgard:yggdrasil_log", "asgard:yggdrasil_log", "asgard:yggdrasil_sap"],
        "result": {"id": "asgard:yggdrasil_heartwood", "count": 4}})
    write(rec / "ancient_bark.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["LL", "LL"],
        "key": {"L": "asgard:yggdrasil_log"}, "result": {"id": "asgard:ancient_bark", "count": 3}})
    write(rec / "divine_essence.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
        "asgard:yggdrasil_sap", "minecraft:golden_apple", "minecraft:nether_wart", "asgard:rune_stone"],
        "result": {"id": "asgard:divine_essence", "count": 1}})
    print("data written")


if __name__ == "__main__":
    main()
