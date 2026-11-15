#!/usr/bin/env python3
"""Generate the three Norse structures as Minecraft structure files (data/asgard/structure/*.nbt).

    python3 tools/gen_structures.py

Yggdrasil (a giant hollow tree), Thor's shrine, and a rune circle. Everything is deterministic: the same run writes
the same bytes. The structures are placed in the world by the worldgen data (structure, structure set, template pool,
biome tags) in src/main/resources/data/asgard/. Stdlib only.
"""

import math
import random
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


# ---------- Yggdrasil: the world tree, six seeded variants ----------

RUNE_GLOW = state("asgard:yggdrasil_rune")
VARIANTS = 6
W, H = 85, 100
CX = CZ = 42


def sphere_cells(x, y, z, r):
    for ix in range(math.floor(x - r), math.ceil(x + r) + 1):
        for iy in range(math.floor(y - r), math.ceil(y + r) + 1):
            for iz in range(math.floor(z - r), math.ceil(z + r) + 1):
                if (ix - x) ** 2 + (iy - y) ** 2 + (iz - z) ** 2 <= r * r + 0.25:
                    yield ix, iy, iz


def axis_of(dx, dy, dz):
    if abs(dy) > max(abs(dx), abs(dz)):
        return "y"
    return "x" if abs(dx) >= abs(dz) else "z"


def yggdrasil(seed):
    rnd = random.Random(seed * 7919 + 13)
    s = Structure(W, H, W)
    phase = rnd.random() * math.tau

    def trunk_r(y, th):
        if y < 16:
            base = 8.6 + (16 - y) * 0.5
        elif y < 62:
            base = 8.6 - (y - 16) * 0.075
        else:
            base = 5.2 - (y - 62) * 0.15
        base = max(base, 3.0)
        ridge = 1.2 * math.sin(7 * th + phase + y * 0.05) + 0.6 * math.sin(13 * th + phase * 2)
        buttress = max(0, 16 - y) / 16 * 3.4 * max(0, math.sin(9 * th + phase))
        return base + ridge * (0.5 if y >= 16 else 1.0) + buttress

    # trunk
    for y in range(0, 80):
        for z in range(W):
            for x in range(W):
                dx, dz = x - CX, z - CZ
                if dx * dx + dz * dz <= 24 * 24 and math.hypot(dx, dz) <= trunk_r(y, math.atan2(dz, dx)):
                    s.put(x, y, z, log("y"))

    # roots: meandering ridges that flow out and down
    for k in range(rnd.randint(14, 18)):
        a = k * math.tau / 16 + rnd.uniform(-0.2, 0.2)
        r, y, t0 = 7.0, rnd.uniform(17, 26), 0
        for step in range(62):
            a += rnd.gauss(0, 0.05)
            r += rnd.uniform(0.75, 1.05)
            y = max(3.2, y - (0.55 if y > 8 else 0.3) * rnd.uniform(0.6, 1.4))
            rad = max(1.2, 3.7 - step * 0.055)
            x, z = CX + math.cos(a) * r, CZ + math.sin(a) * r
            if not (4 <= x < W - 4 and 4 <= z < W - 4) or r > 38:
                break
            ax = axis_of(math.cos(a), -0.4, math.sin(a))
            for ix, iy, iz in sphere_cells(x, y, z, rad):
                if iy >= 0:
                    s.put(ix, iy, iz, log(ax))

    # branches: curving tubes, sub-branches, leaf clumps
    clumps, branch_paths = [], []

    def branch(sx, sy, sz, ang, elev, length, r0, r1, depth=0):
        pts, x, y, z = [], sx, sy, sz
        next_sub = rnd.randint(4, 7)
        for tstep in range(length):
            u = tstep / length
            ang += rnd.gauss(0, 0.04)
            x += math.cos(ang)
            z += math.sin(ang)
            y += elev * (1 - 1.5 * u)
            rad = r0 + (r1 - r0) * u
            ax = axis_of(math.cos(ang), elev, math.sin(ang))
            for ix, iy, iz in sphere_cells(x, y, z, rad):
                s.put(ix, iy, iz, log(ax))
            pts.append((x, y, z, rad, ang))
            if depth == 0 and tstep >= next_sub and tstep < length - 6:
                next_sub = tstep + rnd.randint(4, 7)
                side = rnd.choice((-1, 1)) * rnd.uniform(0.7, 1.2)
                branch(x, y, z, ang + side, rnd.uniform(0.2, 0.5), rnd.randint(11, 17), 1.7, 0.8, 1)
        clumps.append((pts[-1][0], pts[-1][1] + 1, pts[-1][2], rnd.uniform(6, 9) if depth == 0 else rnd.uniform(4.5, 7)))
        if depth == 0:
            for uu in (0.35, 0.55, 0.78):
                p = pts[int(len(pts) * uu)]
                clumps.append((p[0], p[1] + 2.5, p[2], rnd.uniform(5, 7.5)))
            branch_paths.append(pts)
        return pts

    nb = rnd.randint(9, 11)
    for k in range(nb):
        a = k * math.tau / nb + rnd.uniform(-0.25, 0.25)
        y0 = 46 + (k / nb) * 20 + rnd.uniform(-2, 2)
        branch(CX + math.cos(a) * 3, y0, CZ + math.sin(a) * 3, a, 0.4, rnd.randint(28, 36), 4.2, 1.3)
    clumps.append((CX, 88, CZ, 16))            # the crown
    clumps.append((CX + rnd.uniform(-6, 6), 78, CZ + rnd.uniform(-6, 6), 11))

    # leaves: lumpy ellipsoids with gaps
    for cx_, cy_, cz_, r in clumps:
        n_off = [(rnd.uniform(-r * .4, r * .4), rnd.uniform(-r * .2, r * .2), rnd.uniform(-r * .4, r * .4), r * rnd.uniform(.55, .85)) for _ in range(4)]
        n_off.append((0, 0, 0, r))
        for ox, oy, oz, rr in n_off:
            for ix, iy, iz in sphere_cells(cx_ + ox, cy_ + oy, cz_ + oz, rr):
                if 0 <= ix < W and 0 <= iy < H and 0 <= iz < W and (ix, iy, iz) not in s.blocks:
                    if hole(ix, iy, iz + seed * 31) < 7:
                        continue
                    s.put(ix, iy, iz, LEAVES)

    # the glowing rune spiral winding up the trunk
    a0 = rnd.random() * math.tau
    for (x, y, z), blk in list(s.blocks.items()):
        if blk[0] != "asgard:yggdrasil_log" or not 14 <= y <= 68:
            continue
        dx, dz = x - CX, z - CZ
        d = math.hypot(dx, dz)
        if d > trunk_r(y, math.atan2(dz, dx)) - 0.5 or d > 11:
            for off in (0.0, math.pi):
                ang = a0 + y * 0.21 + off
                diff = (math.atan2(dz, dx) - ang + math.pi) % math.tau - math.pi
                if abs(diff) * d < 1.8 and hole(x, y // 2, z) < 86:
                    s.put(x, y, z, RUNE_GLOW)

    # a walkway along the top of one long branch: planks, fences, lanterns
    path = max(branch_paths, key=len)
    for i, (x, y, z, rad, ang) in enumerate(path[3:-4], 3):
        px, pz = -math.sin(ang), math.cos(ang)
        top = math.ceil(y + rad) + (0 if rad > 1.9 else 1)
        for w in (-1, 0, 1):
            bx, bz = round(x + px * w), round(z + pz * w)
            for yy in range(top + 1, top + 4):
                if s.blocks.get((bx, yy, bz)) == LEAVES:
                    s.remove(bx, yy, bz)
            s.put(bx, top, bz, state("minecraft:dark_oak_planks"))
            if abs(w) == 1 and i % 3 == 0:
                s.put(bx, top + 1, bz, state("minecraft:dark_oak_fence", east="false", north="false", south="false", waterlogged="false", west="false"))
                if i % 6 == 0:
                    s.put(bx, top + 2, bz, state("minecraft:lantern", hanging="false", waterlogged="false"))

    # waterfalls from two branches into stone-ringed pools
    for bi in rnd.sample(range(len(branch_paths)), 2):
        pts = branch_paths[bi]
        x, y, z, rad, _ = pts[int(len(pts) * 0.72)]
        wx, wz = round(x), round(z)
        if not (5 <= wx < W - 5 and 5 <= wz < W - 5):
            continue
        for yy in range(math.floor(y - rad) - 1, 2, -1):
            if (wx, yy, wz) not in s.blocks or s.blocks[(wx, yy, wz)] == LEAVES:
                s.put(wx, yy, wz, state("minecraft:water", level="0"))
        for dz in range(-4, 5):
            for dx in range(-4, 5):
                d = math.hypot(dx, dz)
                if d <= 2.6:
                    for yy in (2, 3):
                        s.put(wx + dx, yy, wz + dz, state("minecraft:water", level="0"))
                elif d <= 3.6:
                    for yy in (2, 3, 4):
                        s.put(wx + dx, yy, wz + dz, state("minecraft:mossy_stone_bricks"))

    # the hollow at the foot: an amethyst cave, a doorway to the south, a chest
    for y in range(3, 9):
        for z in range(W):
            for x in range(W):
                if math.hypot(x - CX, z - CZ) <= 4.2 and s.blocks.get((x, y, z), ("",))[0] == "asgard:yggdrasil_log":
                    s.remove(x, y, z)
    for y in range(3, 7):
        for z in range(CZ, W):
            for x in (CX - 1, CX, CX + 1):
                s.remove(x, y, z)
    for k in range(7):
        a = k * math.tau / 7 + 0.4
        s.put(round(CX + math.cos(a) * 3.2), 3, round(CZ + math.sin(a) * 3.2), state("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
    s.put(CX - 3, 3, CZ + 1, state("minecraft:amethyst_block"))
    s.put(CX + 3, 3, CZ - 1, state("minecraft:amethyst_block"))
    for k in range(4):
        a = k * math.tau / 4 + 0.8
        s.put(round(CX + math.cos(a) * 2.6), 8, round(CZ + math.sin(a) * 2.6), state("minecraft:soul_lantern", hanging="true", waterlogged="false"))
    blk, tag = chest("south", "asgard:chests/yggdrasil_hollow")
    s.put(CX, 3, CZ - 2, blk, tag)

    # finishing: lanterns, glow fruit and vines hanging under the leaves, moss on the roots
    for (x, y, z), blk in list(s.blocks.items()):
        if blk == LEAVES:
            below = (x, y - 1, z)
            r = hole(x + 5, y, z + seed)
            if below not in s.blocks:
                if r < 4:
                    s.put(*below, state("minecraft:lantern", hanging="true", waterlogged="false"))
                elif r < 12:
                    for n in range(rnd.randint(2, 6)):
                        if (x, y - 1 - n, z) in s.blocks:
                            break
                        s.put(x, y - 1 - n, z, state("minecraft:vine", up="true", north="false", south="false", east="false", west="false"))
            elif r > 98:
                s.put(x, y, z, state("minecraft:shroomlight"))
        elif blk[0] == "asgard:yggdrasil_log" and y <= 26 and (x, y + 1, z) not in s.blocks and hole(x, y, z + 3) < 30:
            s.put(x, y + 1, z, state("minecraft:moss_carpet"))
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
    for old in OUT.glob("yggdrasil*.nbt"):
        old.unlink()
    builds = [(f"yggdrasil_{i}", (lambda i=i: yggdrasil(i))) for i in range(VARIANTS)]
    builds += [("thors_shrine", thors_shrine), ("rune_circle", rune_circle)]
    for name, build in builds:
        st = build()
        data = st.dumps()
        (OUT / f"{name}.nbt").write_bytes(data)
        back = nbt.loads(data)
        n = len(back["blocks"][1][1])
        assert n == len(st.blocks), name
        print(f"{name}: size {st.size}, {n} blocks, {len(back['palette'][1][1])} states, {len(data)} bytes")
