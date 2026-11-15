#!/usr/bin/env python3
"""Generate the three Norse structures as Minecraft structure files (data/asgard/structure/*.nbt).

    python3 tools/gen_structures.py

Yggdrasil (a giant hollow tree), Thor's shrine, and a rune circle. Everything is deterministic: the same run writes
the same bytes. The structures are placed in the world by the worldgen data (structure, structure set, template pool,
biome tags) in src/main/resources/data/asgard/. Stdlib only.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbt  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "src/main/resources/data/asgard/structure"
DATA_VERSION = 4189  # Minecraft 1.21.4

AIR = ("minecraft:air", ())


def state(name, **props):
    return (name, tuple(sorted(props.items())))


class Structure:
    def __init__(self, sx, sy, sz):
        self.size = (sx, sy, sz)
        self.blocks = {}
        self.nbt = {}

    def put(self, x, y, z, block, tag=None):
        sx, sy, sz = self.size
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            self.blocks[(x, y, z)] = block
            if tag:
                self.nbt[(x, y, z)] = tag

    def fill(self, x0, y0, z0, x1, y1, z1, block):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    self.put(x, y, z, block)

    def remove(self, x, y, z):
        self.blocks.pop((x, y, z), None)

    def dumps(self):
        palette, index = [], {}
        for blk in self.blocks.values():
            if blk not in index:
                index[blk] = len(palette)
                palette.append(blk)
        pal = []
        for name, props in palette:
            c = {"Name": (nbt.STRING, name)}
            if props:
                c["Properties"] = (nbt.COMPOUND, {k: (nbt.STRING, v) for k, v in props})
            pal.append(c)
        blocks = []
        for (x, y, z), blk in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
            c = {"pos": (nbt.LIST, (nbt.INT, [x, y, z])), "state": (nbt.INT, index[blk])}
            tag = self.nbt.get((x, y, z))
            if tag:
                c["nbt"] = (nbt.COMPOUND, {k: (nbt.STRING, v) for k, v in tag.items()})
            blocks.append(c)
        root = {
            "DataVersion": (nbt.INT, DATA_VERSION),
            "size": (nbt.LIST, (nbt.INT, list(self.size))),
            "palette": (nbt.LIST, (nbt.COMPOUND, pal)),
            "blocks": (nbt.LIST, (nbt.COMPOUND, blocks)),
            "entities": (nbt.LIST, (nbt.COMPOUND, [])),
        }
        return nbt.dumps(root)


def log(axis="y"):
    return state("asgard:yggdrasil_log", axis=axis)


LEAVES = state("asgard:yggdrasil_leaves", distance="1", persistent="true", waterlogged="false")
RUNE = state("asgard:rune_stone")


def chest(facing, loot):
    return state("minecraft:chest", facing=facing, type="single", waterlogged="false"), {
        "id": "minecraft:chest", "LootTable": loot}


def hole(x, y, z):
    """Deterministic scatter in [0, 100)."""
    return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) % 100


# ---------- Yggdrasil: a giant hollow tree ----------

def yggdrasil():
    W, H = 41, 50
    s = Structure(W, H, W)
    cx = cz = 20

    def dist(x, z):
        return math.hypot(x - cx, z - cz)

    # trunk, tapering from 4.6 to about 3.3 blocks
    for y in range(0, 44):
        r = 5.0 if y < 3 else 4.6 - (y - 3) * 0.032
        if y >= 33:
            r = 2.4
        for z in range(W):
            for x in range(W):
                if dist(x, z) <= r:
                    s.put(x, y, z, log("y"))
    # roots: eight arms flaring out and down
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        for t in range(0, 13):
            rx = cx + math.cos(a) * (4 + t)
            rz = cz + math.sin(a) * (4 + t)
            ry = max(0, int(5 - t * 0.4))
            axis = "x" if abs(math.cos(a)) >= abs(math.sin(a)) else "z"
            for yy in range(0, ry + (1 if t < 7 else 0) + 1):
                s.put(round(rx), yy, round(rz), log(axis))
                if t < 6:
                    s.put(round(rx), yy, round(rz) + 1, log(axis))
    # main branches, rising outward from the upper trunk
    for k in range(6):
        a = k * math.pi / 3 + 0.26
        y0 = 24 + (k % 3) * 3
        for t in range(0, 15):
            bx = cx + math.cos(a) * (3 + t)
            bz = cz + math.sin(a) * (3 + t)
            by = int(y0 + t * 0.6)
            axis = "x" if abs(math.cos(a)) >= abs(math.sin(a)) else "z"
            s.put(round(bx), by, round(bz), log(axis))
            if t < 5:
                s.put(round(bx), by + 1, round(bz), log(axis))
                s.put(round(bx) + 1, by, round(bz), log(axis))
    # canopy: a wide ellipsoid with gaps, and a lower skirt around the branches
    for cy, rx, ry, floor in ((38, 19, 10, 0.45), (30, 14, 5, 0.35)):
        for y in range(H):
            for z in range(W):
                for x in range(W):
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rx) ** 2
                    if d > 1.0 or (x, y, z) in s.blocks:
                        continue
                    if d > floor and hole(x, y, z) < 12:
                        continue
                    s.put(x, y, z, LEAVES)
    # sun shafts: open columns through the canopy so light reaches the trunk, and lanterns hung under the branches
    for ring_r, count in ((6.5, 8), (12.5, 12)):
        for k in range(count):
            a = k * 2 * math.pi / count + (0.3 if ring_r > 10 else 0.0)
            sx, sz = round(cx + math.cos(a) * ring_r), round(cz + math.sin(a) * ring_r)
            for y in range(H):
                for ox in (0, 1):
                    for oz in (0, 1):
                        if s.blocks.get((sx + ox, y, sz + oz)) == LEAVES:
                            s.remove(sx + ox, y, sz + oz)
    for k in range(10):
        a = k * 2 * math.pi / 10 + 0.15
        lx, lz = round(cx + math.cos(a) * 9), round(cz + math.sin(a) * 9)
        for y in range(34, 24, -1):
            if s.blocks.get((lx, y + 1, lz)) == LEAVES and (lx, y, lz) not in s.blocks:
                s.put(lx, y, lz, state("minecraft:lantern", hanging="true", waterlogged="false"))
                break
    # the hollow at the foot: a doorway to the south, a chest, a hanging lantern
    for y in range(4, 7):
        for z in range(W):
            for x in range(W):
                if dist(x, z) <= 2.2:
                    s.remove(x, y, z)
    for y in (4, 5):
        for z in range(cz + 1, cz + 7):
            for x in (cx - 1, cx, cx + 1):
                s.remove(x, y, z)
    blk, tag = chest("south", "asgard:chests/yggdrasil_hollow")
    s.put(cx, 4, cz - 1, blk, tag)
    s.put(cx, 6, cz, state("minecraft:lantern", hanging="true", waterlogged="false"))
    return s


# ---------- Thor's shrine ----------

def thors_shrine():
    s = Structure(13, 12, 13)
    s.fill(0, 0, 0, 12, 0, 12, state("minecraft:stone_bricks"))
    s.fill(1, 1, 1, 11, 1, 11, state("minecraft:polished_andesite"))
    for i in range(1, 12):
        for edge in (1, 11):
            s.put(i, 1, edge, state("minecraft:stone_bricks"))
            s.put(edge, 1, i, state("minecraft:stone_bricks"))
    for i in range(2, 11):                       # a cross of rune stones
        s.put(6, 1, i, RUNE)
        s.put(i, 1, 6, RUNE)
    for px, pz in ((2, 2), (10, 2), (2, 10), (10, 10)):   # four pillars with lightning rods
        s.put(px, 2, pz, state("minecraft:chiseled_stone_bricks"))
        for y in (3, 4, 5):
            s.put(px, y, pz, state("minecraft:stone_bricks"))
        s.put(px, 6, pz, state("minecraft:chiseled_stone_bricks"))
        s.put(px, 7, pz, state("minecraft:lightning_rod", facing="up", powered="false", waterlogged="false"))
    s.fill(5, 2, 5, 7, 2, 7, state("minecraft:smooth_stone"))      # the altar
    s.put(6, 2, 6, state("minecraft:gold_block"))
    blk, tag = chest("south", "asgard:chests/thors_shrine")
    s.put(6, 3, 6, blk, tag)
    for y in range(4, 10):                                          # the spire
        s.put(6, y, 6, state("minecraft:lightning_rod", facing="up", powered="false", waterlogged="false"))
    return s


# ---------- the rune circle ----------

def rune_circle():
    s = Structure(13, 6, 13)
    c = 6
    for z in range(13):
        for x in range(13):
            d = math.hypot(x - c, z - c)
            if d <= 6.3:
                s.put(x, 0, z, state("minecraft:mossy_cobblestone") if hole(x, 0, z) < 30
                      else state("minecraft:polished_andesite"))
    for k in range(8):
        a = k * math.pi / 4
        px, pz = c + round(math.cos(a) * 5), c + round(math.sin(a) * 5)
        for y in (1, 2, 3):
            s.put(px, y, pz, RUNE)
        s.put(px, 4, pz, state("minecraft:stone_brick_slab", type="bottom", waterlogged="false"))
    s.put(c, 0, c, state("minecraft:mossy_stone_bricks"))
    blk, tag = chest("south", "asgard:chests/rune_circle")
    s.put(c, 1, c, blk, tag)
    s.put(c, 2, c, state("minecraft:soul_lantern", hanging="false", waterlogged="false"))
    return s


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in (("yggdrasil", yggdrasil), ("thors_shrine", thors_shrine), ("rune_circle", rune_circle)):
        st = build()
        data = st.dumps()
        (OUT / f"{name}.nbt").write_bytes(data)
        back = nbt.loads(data)
        n = len(back["blocks"][1][1])
        assert n == len(st.blocks), name
        print(f"{name}: size {st.size}, {n} blocks, {len(back['palette'][1][1])} states, {len(data)} bytes")
