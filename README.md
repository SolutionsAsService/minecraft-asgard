# Asgard

The gods of Asgard as potions, for Minecraft Java Edition (Fabric, 1.21.4). Six gods, six ingredients, six
draughts. Each potion is brewed from an Awkward Potion and one ingredient that belongs to Asgard.

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
models and sprites:

```sh
python3 tools/gen_assets.py
```

An unknown effect id is logged and skipped, not a crash. The data format (`pantheon.potions/1`) is shared with
the other Nordic Pantheon mods. It is described on the developers page of the modding site.

## Status

- Builds with Fabric Loom 1.11.8 on Gradle 8.
- Loads on a Fabric dedicated server for 1.21.4. The log line is
  `Asgard loaded: 6 potions, 6 brewing recipes, 0 unknown effects skipped`.
- **Not yet tested in a world:** a brew in a brewing stand, and drinking the potions. The brewing recipes are
  registered in code and counted in the log.

## Credit

All work in this repository is credited to SolutionsAsService.
