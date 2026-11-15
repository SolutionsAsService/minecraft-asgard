# Asgard

The gods of Asgard as potions, for Minecraft Java Edition (Fabric, 1.21.4). Six gods, six ingredients, six
draughts. Each potion is brewed from an Awkward Potion and one ingredient that belongs to Asgard.

Version 0.2 adds the rest of the Norse world:

- **Relics**: Mjölnir (right-click calls lightning where you look), Gungnir (what it hits glows), Gjallarhorn
  (a horn that reveals what is near). Their numbers live in
  [`content.json`](src/main/resources/assets/asgard/content.json), which the site reads too.
- **Yggdrasil**: log, leaves (drop a leaf or a fruit), a fruit to eat, and the Potion of Blessing (leaf on Awkward
  Potion).
- **Structures** in new worlds: Yggdrasil (an 85 by 85 by 100 world tree in six random variants: gold rune spiral, root ridges, branches, a lantern walkway, waterfalls, vines, an amethyst hollow), Thor's shrine, and the rune circle,
  each with a chest that can hold a relic. Yggdrasil has a ladder up the trunk to Valhalla, a hall on the crown with its
  own chest; the shrine and circle come in three variants each.
- **Advancements**: a small tree from the rune circle to Mjölnir, Gungnir and the Gjallarhorn. Rune stone is a craftable block; the glowing Yggdrasil Rune is found on the tree.

Version 0.3 starts the [expansion design](design/expand.md) (Phase 1):

- **Seven god shrines**, each with its own look: Thor (thunder dais), Odin (monolith, one-eyed statue, ravens), Freyja
  (flower garden, crystals, cats), Loki (a hidden underground altar), Freyr (a golden-wheat farm and totems), Tyr (crossed
  swords, shields, banners) and Heimdall (a rainbow watchtower). Each comes in variants, has a chest of god-themed loot,
  and an **offering altar**: hold the offering, use the altar, and receive the god's blessing.
- **Five more divine potions** (Freyr's Blessing, Tyr's Courage, Idunn's Elixir, Mimir's Knowledge, Yggdrasil's Essence),
  Yggdrasil Sap, Sacred Root, Heartwood, Ancient Bark and Golden World Tree Leaves, with crafting recipes.

Version 0.4 adds the first creatures (Phase 2): the **Draugr** (an undead Norse warrior that never burns), the **Troll**
(large, hits hard, and turns to stone in daylight) and **Odin's Raven** (a tameable black bird). They reuse the zombie and
parrot models with their own skins, spawn naturally in taiga, forest and mountain biomes and in the shrines and Yggdrasil, drop
runes, bones and feathers, and have spawn eggs and advancements. Not yet built: Ratatoskr, other beasts, bosses.

Not yet built from the design: creatures, the Nine Realms, bosses and events, armour, rune magic, the three wells.

Status: the mod builds and loads on a 1.21.4 Fabric server; all three structures generate with `/place structure`;
the icons and structures show in a real client. Using the relics, brewing, and natural spawning in a fresh survival world
are not yet tested (`/locate` was inconclusive on the test seed). Regenerate the generated files with
`python3 tools/gen_structures.py`, `python3 tools/gen_content.py` and `python3 tools/gen_assets.py`.

Part of the **Nordic Pantheon** mod pack, built with the SHADW modding stack
([shadw-modding](https://github.com/SolutionsAsService/shadw-modding)).

## The six draughts

| God | Potion | Ingredient | Effects |
|---|---|---|---|
| Thor | Thor's Valor | Thunder Iron | Strength II for 3:00; Resistance I for 1:00 |
| Frigg | Aegis of Frigg | Spindle Thread | Resistance II for 3:00; Absorption I for 1:00 |
| Heimdall | Bifrost Spark | Rainbow Shard | Speed II for 2:00; Haste I for 1:00 |
| Odin | All-Father's Eye | Mimir Glass | Night Vision I for 5:00; Luck I for 5:00 |
| Freyja | Hall Mead | Valhalla Honey | Regeneration II for 0:45; Absorption I for 2:00 |
| Loki | Trickster's Draught | Serpent Scale | Invisibility I for 2:00; Speed I for 1:00 |

Every ingredient has a one-line lore tooltip. The lore, the effects and the durations are in
[`potions.json`](src/main/resources/assets/asgard/potions.json).

## Requirements

Minecraft 1.21.4, Fabric Loader 0.16 or later, Fabric API, Java 21.

## Build

With the SHADW stack (`tools/shadw-mod` from a checkout of shadw-modding):

```sh
tools/shadw-mod validate /path/to/minecraft-asgard
tools/shadw-mod build /path/to/minecraft-asgard
```

Or with Gradle directly, from this folder: `gradle build`. The jar lands in `build/libs/`.

## Add or change a potion

Potions are data. Edit `src/main/resources/assets/asgard/potions.json`, then regenerate the language file, item
models, item definitions and sprites (a potion may set its own sprite colour with `hue`):

```sh
python3 tools/gen_assets.py
```

An unknown effect id is logged and skipped, not a crash. The data format (`pantheon.potions/1`) is shared with
the other Nordic Pantheon mods. It is described on the developers page of the modding site.

## Site

`python3 _src/build_site.py` writes `site/` from `potions.json`: the home page with the hall of six pillars, a page per
god, install and developer pages. Colours are Minecraft's dye colours, read from the game's `DyeColor` class, one per
god, with yellow kept for actions. The build fails if two god colours differ by less than ΔE 30 or any is under 3:1 on
the card ground. The in-game screenshots in `site/img/shots/` were captured from a Minecraft 1.21.4 client joined to a
Fabric dedicated server with this mod, in a flat test world built with server commands (the pillars and the Bifrost
are not part of the mod). `site/img/hero.png` is the hall capture with the crosshair smoothed out and the HUD cropped
off. The deploy serves the committed `site/` as static files.

## Status

- Item models need item definitions in Minecraft 1.21.4 (`assets/asgard/items/<id>.json`). An early build shipped
  models only, and every ingredient drew as the purple-and-black missing model in the game. The generator now writes
  the definitions, and the ingredients draw correctly in the hall captures.

- Builds with Fabric Loom 1.11.8 on Gradle 8.
- Loads on a Fabric dedicated server for 1.21.4. The log line is
  `Asgard loaded: 6 potions, 6 brewing recipes, 0 unknown effects skipped`.
- A client joined the server and showed the ingredients (as item-frame displays and in the hotbar) and the potions.
- **Not yet tested in a world:** a brew in a brewing stand, and drinking the potions. The brewing recipes are
  registered in code and counted in the log.

## Credit

All work in this repository is credited to SolutionsAsService.
