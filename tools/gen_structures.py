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
GOLD_LEAVES = state("asgard:golden_leaves", distance="1", persistent="true", waterlogged="false")
VARIANTS = 6
W, H = 85, 100
CX = CZ = 42


def sphere_cells(x, y, z, r):
    for ix in range(math.floor(x - r), math.ceil(x + r) + 1):
        for iy in range(math.floor(y - r), math.ceil(y + r) + 1):
            for iz in range(math.floor(z - r), math.ceil(z + r) + 1):
                if (ix - x) ** 2 + (iy - y) ** 2 + (iz - z) ** 2 <= r * r + 0.25:
                    yield ix, iy, iz


def ellipsoid_cells(x, y, z, r, sy=0.62):
    ry = r * sy
    for ix in range(math.floor(x - r), math.ceil(x + r) + 1):
        for iy in range(math.floor(y - ry), math.ceil(y + ry) + 1):
            for iz in range(math.floor(z - r), math.ceil(z + r) + 1):
                d = ((ix - x) / r) ** 2 + ((iy - y) / ry) ** 2 + ((iz - z) / r) ** 2
                if d <= 1.0:
                    yield ix, iy, iz, d


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
            base = 8.6 + (16 - y) * 0.3
        elif y < 62:
            base = 8.6 - (y - 16) * 0.075
        else:
            base = 5.2 - (y - 62) * 0.15
        base = max(base, 3.0)
        ridge = 1.2 * math.sin(7 * th + phase + y * 0.05) + 0.6 * math.sin(13 * th + phase * 2)
        buttress = max(0, 16 - y) / 16 * 2.6 * max(0, math.sin(9 * th + phase))
        return base + ridge * (0.5 if y >= 16 else 1.0) + buttress

    # trunk
    for y in range(0, 80):
        for z in range(W):
            for x in range(W):
                dx, dz = x - CX, z - CZ
                if dx * dx + dz * dz <= 24 * 24 and math.hypot(dx, dz) <= trunk_r(y, math.atan2(dz, dx)):
                    s.put(x, y, z, log("y"))

    # roots: meandering ridges that flow out and down
    for k in range(rnd.randint(10, 13)):
        a = k * math.tau / 11 + rnd.uniform(-0.2, 0.2)
        r, y, t0 = 9.0, rnd.uniform(16, 24), 0
        for step in range(62):
            a += rnd.gauss(0, 0.05)
            r += rnd.uniform(0.75, 1.05)
            y = max(3.2, y - (0.55 if y > 8 else 0.3) * rnd.uniform(0.6, 1.4))
            rad = max(1.2, 3.0 - step * 0.045)
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
        clumps.append((pts[-1][0], pts[-1][1] + (3.2 if depth == 0 else 2.4), pts[-1][2], rnd.uniform(6, 9) if depth == 0 else rnd.uniform(4.5, 7)))
        if depth == 0:
            for uu in (0.35, 0.55, 0.78):
                p = pts[int(len(pts) * uu)]
                clumps.append((p[0], p[1] + 4.2, p[2], rnd.uniform(4.5, 6.5)))
            branch_paths.append(pts)
        return pts

    nb = rnd.randint(9, 11)
    for k in range(nb):
        a = k * math.tau / nb + rnd.uniform(-0.25, 0.25)
        y0 = 46 + (k / nb) * 20 + rnd.uniform(-2, 2)
        branch(CX + math.cos(a) * 3, y0, CZ + math.sin(a) * 3, a, 0.4, rnd.randint(28, 36), 4.2, 1.3)
    clumps.append((CX, 86, CZ, 16))            # the crown
    clumps.append((CX + rnd.uniform(-6, 6), 78, CZ + rnd.uniform(-6, 6), 11))

    # leaves: lumpy ellipsoids with gaps
    for cx_, cy_, cz_, r in clumps:
        n_off = [(rnd.uniform(-r * .4, r * .4), rnd.uniform(-r * .2, r * .2), rnd.uniform(-r * .4, r * .4), r * rnd.uniform(.55, .85)) for _ in range(4)]
        n_off.append((0, 0, 0, r))
        for ox, oy, oz, rr in n_off:
            for ix, iy, iz, dd in ellipsoid_cells(cx_ + ox, cy_ + oy * 0.5, cz_ + oz, rr):
                if 0 <= ix < W and 0 <= iy < H and 0 <= iz < W and (ix, iy, iz) not in s.blocks:
                    if hole(ix, iy, iz + seed * 31) < 7 or (dd > 0.62 and hole(ix + 3, iy, iz + seed * 17) < (dd - 0.62) / 0.38 * 100):
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
                if abs(diff) * d < 2.4 and hole(x, y // 2, z) < 86:
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
    blk, tag = chest("east", "asgard:chests/yggdrasil_hollow")
    s.put(CX - 3, 3, CZ + 1, blk, tag)

    # Valhalla: a hall on the crown, reached by a ladder up the trunk from the hollow
    PL = 80
    for y in range(PL, 96):
        for z in range(W):
            for x in range(W):
                if math.hypot(x - CX, z - CZ) <= 12.8:
                    s.remove(x, y, z)
    for z in range(W):
        for x in range(W):
            d = math.hypot(x - CX, z - CZ)
            if d <= 12.5:
                s.put(x, PL, z, state("minecraft:dark_oak_planks"))
            if 8.2 <= d <= 9.2:
                s.put(x, PL, z, state("minecraft:stone_bricks"))
            if 3.4 <= d <= 4.5:
                s.put(x, PL, z, RUNE_GLOW)
            if 11.6 <= d <= 12.5:
                s.put(x, PL + 1, z, state("minecraft:dark_oak_fence", east="false", north="false", south="false", waterlogged="false", west="false"))
                if hole(x, 7, z) < 22:
                    s.put(x, PL + 2, z, state("minecraft:lantern", hanging="false", waterlogged="false"))
    for z in range(W):
        for x in range(W):
            if 5.6 <= math.hypot(x - CX, z - CZ) <= 10.6:
                s.put(x, PL + 7, z, state("minecraft:dark_oak_planks"))
    for k in range(8):
        a = k * math.tau / 8
        px, pz = round(CX + math.cos(a) * 8.7), round(CZ + math.sin(a) * 8.7)
        for y in range(PL + 1, PL + 7):
            s.put(px, y, pz, RUNE_GLOW if y == PL + 4 else log("y"))
        s.put(px, PL + 8, pz, state("minecraft:lightning_rod", facing="up", powered="false", waterlogged="false"))
        lx, lz = round(CX + math.cos(a + math.pi / 8) * 6.6), round(CZ + math.sin(a + math.pi / 8) * 6.6)
        s.put(lx, PL + 6, lz, state("minecraft:lantern", hanging="true", waterlogged="false"))
    s.put(CX, PL + 1, CZ, state("minecraft:gold_block"))
    vblk, vtag = chest("south", "asgard:chests/valhalla")
    s.put(CX, PL + 2, CZ, vblk, vtag)
    for y in range(3, 9):
        s.put(CX, y, CZ - 2, log("y"))
    for y in range(3, PL + 1):
        s.put(CX, y, CZ - 1, state("minecraft:ladder", facing="south", waterlogged="false"))

    # finishing: strands hang from small log knots (leaves cannot support a lantern or a vine), moss on the roots
    chain = state("minecraft:chain", axis="y", waterlogged="false")
    for (x, y, z), blk in list(s.blocks.items()):
        if blk == LEAVES:
            below = (x, y - 1, z)
            r = hole(x + 5, y, z + seed)
            if below not in s.blocks and y > 20:
                if r < 5:                                   # a chain and a lantern
                    s.put(x, y, z, log("y"))
                    n = rnd.randint(1, 3)
                    for k in range(n):
                        s.put(x, y - 1 - k, z, chain)
                    s.put(x, y - 1 - n, z, state("minecraft:lantern", hanging="true", waterlogged="false"))
                elif r < 8:                                 # glowing fruit on a chain
                    s.put(x, y, z, log("y"))
                    s.put(x, y - 1, z, chain)
                    s.put(x, y - 2, z, state("minecraft:shroomlight"))
                    if hole(x, y, z + 2) < 45 and (x, y - 3, z) not in s.blocks:
                        s.put(x, y - 3, z, state("minecraft:shroomlight"))
                elif r < 15:                                # a curtain of vines
                    s.put(x, y, z, log("y"))
                    for k in range(rnd.randint(3, 8)):
                        if (x, y - 1 - k, z) in s.blocks:
                            break
                        s.put(x, y - 1 - k, z, state("minecraft:vine", up="true", north="false", south="false", east="false", west="false"))
            elif r > 98:
                s.put(x, y, z, state("minecraft:shroomlight"))
        elif blk[0] == "asgard:yggdrasil_log" and y <= 26 and (x, y + 1, z) not in s.blocks and hole(x, y, z + 3) < 30:
            s.put(x, y + 1, z, state("minecraft:moss_carpet"))
    # lanterns hung straight from the undersides of the branches
    for (x, y, z), blk in list(s.blocks.items()):
        if blk[0] == "asgard:yggdrasil_log" and 40 <= y < 80 and (x, y - 1, z) not in s.blocks and hole(x + 2, y, z + 6) < 2:
            s.put(x, y - 1, z, state("minecraft:lantern", hanging="true", waterlogged="false"))

    # glowing veins: runes creep along the root ridges and under the branches
    for (x, y, z), blk in list(s.blocks.items()):
        if blk[0] != "asgard:yggdrasil_log":
            continue
        if y <= 26 and (x, y + 1, z) not in s.blocks and hole(x + 9, y, z) < 4:
            s.put(x, y, z, RUNE_GLOW)
        elif y >= 40 and (x, y - 1, z) not in s.blocks and hole(x, y, z + 11) < 3:
            s.put(x, y, z, RUNE_GLOW)

    # invisible light: warm pockets through the canopy and a glow along the waterfalls
    light = lambda lv: state("minecraft:light", level=str(lv), waterlogged="false")
    pockets = 0
    for y in range(44, 92, 3):
        for z in range(6, W - 6, 4):
            for x in range(6, W - 6, 4):
                if (x, y, z) in s.blocks or hole(x, y, z + seed) > 22 or pockets > 260:
                    continue
                near = sum(1 for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
                           if s.blocks.get((x + d[0], y + d[1], z + d[2])) == LEAVES)
                if near >= 2:
                    s.put(x, y, z, light(11))
                    pockets += 1
    for (x, y, z), blk in list(s.blocks.items()):
        if blk[0] == "minecraft:water" and y % 5 == 0 and y > 4:
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + d[0], y, z + d[1]) not in s.blocks:
                    s.put(x + d[0], y, z + d[1], light(9))
                    break
    for (x, y, z), blk in list(s.blocks.items()):                  # golden leaves among the green
        if blk == LEAVES and hole(x + 13, y, z + seed * 5) < 7:
            s.put(x, y, z, GOLD_LEAVES)
    return s


# ---------- Thor's shrine: three variants ----------

SHRINE_VARIANTS = 3
CIRCLE_VARIANTS = 3
ROD = state("minecraft:lightning_rod", facing="up", powered="false", waterlogged="false")


def weathered(seed, x, y, z):
    r = hole(x + seed * 5, y, z)
    if r < 14:
        return state("minecraft:cracked_stone_bricks")
    if r < 26:
        return state("minecraft:mossy_stone_bricks")
    return state("minecraft:stone_bricks")


def thors_shrine(seed):
    rnd = random.Random(seed * 104729 + 7)
    N, c = 21, 10
    s = Structure(N, 17, N)
    for z in range(N):
        for x in range(N):
            s.put(x, 0, z, weathered(seed, x, 0, z))
            dx, dz = abs(x - c), abs(z - c)
            if max(dx, dz) <= 9:
                s.put(x, 1, z, weathered(seed, x, 1, z) if max(dx, dz) == 9 else state("minecraft:polished_andesite"))
            if max(dx, dz) <= 7:
                s.put(x, 2, z, weathered(seed, x, 2, z) if max(dx, dz) == 7 else state("minecraft:smooth_stone"))
    for i in range(-6, 7):                                   # a glowing rune cross and ring
        s.put(c + i, 2, c, RUNE_GLOW)
        s.put(c, 2, c + i, RUNE_GLOW)
    for z in range(N):
        for x in range(N):
            if 3.6 <= math.hypot(x - c, z - c) <= 4.5 and (x, 2, z) in s.blocks and s.blocks[(x, 2, z)] != RUNE_GLOW:
                s.put(x, 2, z, RUNE)
    broken = rnd.randrange(4)
    for k, (sx, sz) in enumerate(((-6, -6), (6, -6), (-6, 6), (6, 6))):
        px, pz = c + sx, c + sz
        h = rnd.randint(7, 10)
        if k == broken:
            h = rnd.randint(2, 4)
            for _ in range(5):
                s.put(px + rnd.randint(-2, 2), 3, pz + rnd.randint(-2, 2), weathered(seed, px, 3, pz))
        for y in range(3, 3 + h):
            s.put(px, y, pz, RUNE_GLOW if (y == 3 + h - 3 and k != broken) else weathered(seed, px, y, pz))
        if k != broken:
            s.put(px, 3 + h, pz, state("minecraft:chiseled_stone_bricks"))
            s.put(px, 4 + h, pz, ROD)
    s.put(c, 3, c + 5, state("asgard:thor_altar"))
    for bx, bz in ((c - 8, c), (c + 8, c), (c, c - 8), (c, c + 8)):      # braziers
        s.put(bx, 3, bz, state("minecraft:campfire", facing="north", lit="true", signal_fire="false", waterlogged="false"))
    s.fill(c - 1, 3, c - 1, c + 1, 3, c + 1, state("minecraft:gold_block"))
    blk, tag = chest("south", "asgard:chests/thors_shrine")
    s.put(c, 4, c, blk, tag)
    for y in range(5, 5 + rnd.randint(7, 9)):                           # the spire
        s.put(c, y, c, ROD)
    return s


# ---------- the other gods' shrines ----------

GODS_SHRINES = ("odin_shrine", "freyja_shrine", "loki_shrine", "freyr_shrine", "tyr_shrine", "heimdall_shrine")
SHRINE_SEEDS = 2
SLAB = state("minecraft:stone_brick_slab", type="bottom", waterlogged="false")
CHAIN = state("minecraft:chain", axis="y", waterlogged="false")
LANTERN_HANG = state("minecraft:lantern", hanging="true", waterlogged="false")
WALL = state("minecraft:stone_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false")


def odin_shrine(seed):
    rnd = random.Random(seed * 31337 + 11)
    N, c = 19, 9
    s = Structure(N, 18, N)
    for z in range(N):
        for x in range(N):
            if math.hypot(x - c, z - c) <= 9.4:
                s.put(x, 0, z, weathered(seed, x, 0, z))
                if 5.5 <= math.hypot(x - c, z - c) <= 6.4:
                    s.put(x, 0, z, RUNE)
    for y in range(1, 11):                                              # the monolith
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                s.put(c + dx, y, c - 4 + dz, weathered(seed, c + dx, y, c - 4 + dz))
    for y in (4, 7):
        for dx in (-1, 0, 1):
            s.put(c + dx, y, c - 4 + 2, RUNE_GLOW if dx == 0 else RUNE)
    s.put(c, 11, c - 4, state("minecraft:chiseled_stone_bricks"))
    s.fill(c - 1, 1, c - 1, c + 1, 1, c + 1, state("minecraft:smooth_stone"))         # the statue of Odin
    s.put(c, 2, c, state("minecraft:stone_bricks")); s.put(c, 3, c, state("minecraft:stone_bricks"))
    s.put(c - 1, 3, c, state("minecraft:stone_brick_stairs", facing="west", half="bottom", shape="straight", waterlogged="false"))
    s.put(c + 1, 3, c, state("minecraft:stone_brick_stairs", facing="east", half="bottom", shape="straight", waterlogged="false"))
    s.put(c, 4, c, state("minecraft:chiseled_stone_bricks"))
    s.put(c, 4, c + 1, RUNE_GLOW)                                                      # the one eye
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            s.put(c + dx, 5, c + dz, SLAB)                                             # the wide hat
    s.put(c, 5, c, state("minecraft:stone_bricks"))
    ravens = ((c - 5, c + 3), (c + 5, c + 3)) if seed % 2 == 0 else ((c - 5, c - 1), (c + 5, c + 4))
    for rx, rz in ravens:
        for y in (1, 2, 3):
            s.put(rx, y, rz, state("minecraft:stone_bricks"))
        s.put(rx, 4, rz, state("minecraft:black_concrete"))
        s.put(rx, 5, rz, state("minecraft:black_concrete"))
        s.put(rx, 5, rz + 1, state("minecraft:orange_terracotta"))
        s.put(rx - 1, 4, rz, state("minecraft:blackstone_slab", type="bottom", waterlogged="false"))
        s.put(rx + 1, 4, rz, state("minecraft:blackstone_slab", type="bottom", waterlogged="false"))
    for px, pz in ((c - 7, c - 7), (c + 7, c - 7), (c - 7, c + 7), (c + 7, c + 7)):    # hanging lanterns on posts
        for y in range(1, 8):
            s.put(px, y, pz, weathered(seed, px, y, pz))
        s.put(px, 8, pz, state("minecraft:stone_brick_slab", type="bottom", waterlogged="false"))
        s.put(px, 7, pz + (1 if pz < c else -1), CHAIN)
    for px, pz in ((c - 7, c - 7), (c + 7, c - 7), (c - 7, c + 7), (c + 7, c + 7)):
        s.put(px + (1 if px < c else -1), 8, pz, state("minecraft:stone_brick_slab", type="bottom", waterlogged="false"))
        s.put(px + (1 if px < c else -1), 7, pz, CHAIN)
        s.put(px + (1 if px < c else -1), 6, pz, LANTERN_HANG)
    s.put(c, 1, c + 5, state("asgard:odin_altar"))
    blk, tag = chest("north", "asgard:chests/odin_shrine")
    s.put(c + 3, 1, c - 4, blk, tag)
    return s


def freyja_shrine(seed):
    rnd = random.Random(seed * 2741 + 5)
    N, c = 21, 10
    s = Structure(N, 13, N)
    flowers = ["minecraft:dandelion", "minecraft:poppy", "minecraft:allium", "minecraft:pink_tulip", "minecraft:azure_bluet",
               "minecraft:cornflower", "minecraft:oxeye_daisy", "minecraft:red_tulip", "minecraft:lily_of_the_valley"]
    for z in range(N):
        for x in range(N):
            d = math.hypot(x - c, z - c)
            if d <= 10.3:
                s.put(x, 0, z, state("minecraft:grass_block", snowy="false"))
                if 3.3 <= d <= 4.8 or x == c or z == c:
                    s.put(x, 0, z, state("minecraft:polished_diorite"))
                elif d > 4.8 and rnd.random() < 0.55:
                    r = rnd.random()
                    if r < 0.12:
                        s.put(x, 1, z, state("minecraft:sunflower", half="lower")); s.put(x, 2, z, state("minecraft:sunflower", half="upper"))
                    elif r < 0.22:
                        s.put(x, 1, z, state("minecraft:pink_petals", flower_amount="3", facing="north"))
                    else:
                        s.put(x, 1, z, state(rnd.choice(flowers)))
    for k in range(7):                                                  # crystals
        a = k * math.tau / 7 + 0.3
        cx_, cz_ = c + round(math.cos(a) * 7.5), c + round(math.sin(a) * 7.5)
        mat = rnd.choice(("minecraft:pink_stained_glass", "minecraft:purple_stained_glass", "minecraft:amethyst_block"))
        for y in range(1, rnd.randint(3, 6)):
            s.put(cx_, y, cz_, state(mat))
            if y == 1:
                s.put(cx_, 0, cz_, state("minecraft:amethyst_block"))
        s.put(cx_, 6, cz_, state("minecraft:amethyst_cluster", facing="up", waterlogged="false")) if False else None
        top = max(y for (xx, y, zz) in s.blocks if xx == cx_ and zz == cz_ and y >= 1 and s.blocks[(xx, y, zz)][0] != "minecraft:air")
        s.put(cx_, top + 1, cz_, state("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
        s.put(cx_, 1, cz_ + 1, state("minecraft:light", level="9", waterlogged="false")) if (cx_, 1, cz_ + 1) not in s.blocks else None
    for px, pz in ((c - 3, c - 3), (c + 3, c - 3), (c - 3, c + 3), (c + 3, c + 3)):   # the pergola
        for y in range(1, 5):
            s.put(px, y, pz, state("minecraft:cherry_log", axis="y"))
    for z in range(c - 3, c + 4):
        for x in range(c - 3, c + 4):
            if max(abs(x - c), abs(z - c)) == 3 or x == c or z == c:
                s.put(x, 5, z, state("minecraft:cherry_slab", type="bottom", waterlogged="false"))
                if hole(x, 5, z + seed) < 40 and max(abs(x - c), abs(z - c)) == 3:
                    s.put(x, 4, z, state("minecraft:flowering_azalea_leaves", distance="7", persistent="true", waterlogged="false"))
    for cat in ((c - 6, c + 6), (c + 6, c + 6)) if seed % 2 == 0 else ((c - 6, c - 6), (c + 6, c - 6)):   # cat statues
        s.put(cat[0], 1, cat[1], state("minecraft:quartz_block")); s.put(cat[0], 2, cat[1], state("minecraft:chiseled_quartz_block"))
        s.put(cat[0], 1, cat[1] + 1, state("minecraft:quartz_slab", type="bottom", waterlogged="false"))
        s.put(cat[0], 3, cat[1], state("minecraft:quartz_slab", type="bottom", waterlogged="false"))
    s.put(c, 0, c, state("minecraft:gold_block"))
    s.put(c, 1, c, state("asgard:freyja_altar"))
    blk, tag = chest("south", "asgard:chests/freyja_shrine")
    s.put(c + 1, 1, c - 1, blk, tag)
    return s


def loki_shrine(seed):
    rnd = random.Random(seed * 1597 + 9)
    N, c = 13, 6
    s = Structure(N, 15, N)
    for y in range(0, 8):
        for z in range(N):
            for x in range(N):
                edge = max(abs(x - c), abs(z - c))
                if y in (0, 7) or edge == 6:
                    s.put(x, y, z, state("minecraft:deepslate_bricks") if hole(x, y, z + seed) > 18 else state("minecraft:cracked_deepslate_bricks"))
                else:
                    s.put(x, y, z, AIR)
    for z in range(N):
        for x in range(N):
            if 2.4 <= math.hypot(x - c, z - c) <= 3.4:
                s.put(x, 0, z, state("minecraft:polished_deepslate"))
    for y in range(8, 15):                                              # the shaft to the surface
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                s.put(c + dx, y, 2 + dz, state("minecraft:mossy_cobblestone") if (dx or dz) else AIR)
        s.put(c, y, 2, AIR)
    for y in range(1, 15):
        s.put(c, y, 2, state("minecraft:ladder", facing="south", waterlogged="false"))
    for y in range(1, 4):
        s.put(c, y, 1, state("minecraft:deepslate_bricks"))
    s.put(c, 7, 2, AIR); s.put(c, 7, 3, AIR)
    s.put(c, 14, 2, state("minecraft:spruce_trapdoor", facing="north", half="bottom", open="false", powered="false", waterlogged="false"))
    for bx, bz in ((2, 4), (10, 4), (2, 10), (10, 10)):                 # green flames
        s.put(bx, 1, bz, WALL); s.put(bx, 2, bz, WALL)
        s.put(bx, 3, bz, state("minecraft:verdant_froglight", axis="y"))
    for k, (sx, sz) in enumerate(((2, 7), (10, 7), (c - 3, 10), (c + 3, 10))):   # strange statues
        s.put(sx, 1, sz, state("minecraft:smooth_basalt")); s.put(sx, 2, sz, state("minecraft:chiseled_deepslate"))
        s.put(sx, 3, sz, state("minecraft:chiseled_deepslate"))
        s.put(sx, 4, sz, state("minecraft:green_glazed_terracotta", facing=("north", "east", "south", "west")[(k + seed) % 4]))
    for cx_, cz_ in ((1, 1), (11, 1), (1, 11), (11, 11)):
        s.put(cx_, 6, cz_, state("minecraft:cobweb")); s.put(cx_, 5, cz_, state("minecraft:cobweb"))
    for k in range(3):
        s.put(rnd.randint(2, 10), 1, rnd.randint(5, 10), state("minecraft:slime_block")) if rnd.random() < 0.7 else None
    s.put(c, 1, 7, state("asgard:loki_altar"))
    blk, tag = chest("north", "asgard:chests/loki_shrine")
    s.put(c, 1, 10, blk, tag)
    return s


def freyr_shrine(seed):
    rnd = random.Random(seed * 4073 + 3)
    N, c = 17, 8
    s = Structure(N, 10, N)
    for z in range(N):
        for x in range(N):
            if max(abs(x - c), abs(z - c)) <= 7:
                dx, dz = x - c, z - c
                if dx == 0 or dz == 0:
                    s.put(x, 0, z, state("minecraft:water", level="0")) if max(abs(dx), abs(dz)) > 1 else s.put(x, 0, z, state("minecraft:hay_block", axis="y"))
                else:
                    s.put(x, 0, z, state("minecraft:farmland", moisture="7"))
                    s.put(x, 1, z, state("minecraft:wheat", age="7"))
                if max(abs(dx), abs(dz)) == 7:
                    s.put(x, 0, z, state("minecraft:stripped_spruce_log", axis="y")) if (dx + dz) % 2 == 0 else s.put(x, 0, z, state("minecraft:spruce_planks"))
                    s.put(x, 1, z, state("minecraft:spruce_fence", east="false", north="false", south="false", west="false", waterlogged="false")) if (x + z) % 3 == 0 else None
    for k, (tx, tz) in enumerate(((c - 5, c - 5), (c + 5, c - 5), (c - 5, c + 5), (c + 5, c + 5))):   # carved totems
        for y in range(1, 6):
            kind = ("minecraft:stripped_dark_oak_log", "minecraft:carved_pumpkin", "minecraft:stripped_dark_oak_log")[y % 3]
            s.put(tx, y, tz, state(kind, **({"facing": ("south", "south", "north", "north")[k]} if "pumpkin" in kind else {"axis": "y"})))
        s.put(tx - 1, 3, tz, state("minecraft:spruce_slab", type="bottom", waterlogged="false"))
        s.put(tx + 1, 3, tz, state("minecraft:spruce_slab", type="bottom", waterlogged="false"))
        s.put(tx, 6, tz, state("minecraft:lantern", hanging="false", waterlogged="false"))
    s.fill(c - 1, 1, c - 1, c + 1, 1, c + 1, state("minecraft:hay_block", axis="y"))
    s.put(c, 2, c, state("asgard:freyr_altar"))
    for bx, bz in ((c - 2, c + 2), (c + 2, c - 2)):
        s.put(bx, 1, bz, state("minecraft:hay_block", axis="y")); s.put(bx, 2, bz, state("minecraft:gold_block") if rnd.random() < 0.3 else state("minecraft:hay_block", axis="y"))
    blk, tag = chest("south", "asgard:chests/freyr_shrine")
    s.put(c + 2, 2, c + 2, blk, tag)
    return s


def tyr_shrine(seed):
    rnd = random.Random(seed * 8191 + 1)
    N, c = 19, 9
    s = Structure(N, 15, N)
    for z in range(N):
        for x in range(N):
            if math.hypot(x - c, z - c) <= 9.4:
                s.put(x, 0, z, weathered(seed, x, 0, z) if hole(x, 0, z) > 20 else state("minecraft:coarse_dirt"))
    for i in range(10):                                                 # two great swords, crossed
        s.put(c - 5 + i, 2 + i, c, state("minecraft:iron_block"))
        s.put(c + 5 - i, 2 + i, c, state("minecraft:iron_block"))
        s.put(c - 5 + i, 2 + i, c + 1, state("minecraft:polished_andesite"))
        s.put(c + 5 - i, 2 + i, c + 1, state("minecraft:polished_andesite"))
    for hx in (c - 6, c + 6):
        s.put(hx, 1, c, state("minecraft:gold_block")); s.put(hx, 2, c, state("minecraft:gold_block"))
    s.put(c - 4, 11, c, state("minecraft:gold_block")); s.put(c + 4, 11, c, state("minecraft:gold_block"))
    for y in range(1, 3):
        s.put(c, y, c, state("minecraft:iron_block")); s.put(c, y, c + 1, state("minecraft:iron_block"))
    for k in range(10):                                                 # a shield wall of targets and banners
        a = math.pi * (0.1 + 0.8 * k / 9)
        sx, sz = c + round(math.cos(a) * 7.5), c + 3 + round(math.sin(a) * 6.5)
        s.put(sx, 1, sz, weathered(seed, sx, 1, sz)); s.put(sx, 2, sz, state("minecraft:target"))
        if k % 3 == 0:
            for y in range(3, 7):
                s.put(sx, y, sz, WALL)
            s.put(sx, 7, sz, state("minecraft:red_banner", rotation=str((k * 2 + seed * 4) % 16)))
    for k in range(5):
        s.put(c + rnd.randint(-6, 6), 1, c + rnd.randint(-7, -3), state("minecraft:iron_bars"))
    s.put(c, 1, c + 5, state("asgard:tyr_altar"))
    blk, tag = chest("south", "asgard:chests/tyr_shrine")
    s.put(c + 3, 1, c + 5, blk, tag)
    return s


def heimdall_shrine(seed):
    rnd = random.Random(seed * 6007 + 17)
    N, c, H = 13, 6, 34
    s = Structure(N, H, N)
    glass = ["red", "orange", "yellow", "lime", "light_blue", "blue", "purple"]
    s.fill(0, 0, 0, 12, 0, 12, state("minecraft:stone_bricks"))
    for y in range(1, 25):
        for z in range(2, 11):
            for x in range(2, 11):
                edge = (x in (2, 10)) or (z in (2, 10))
                corner = (x in (2, 10)) and (z in (2, 10))
                if corner:
                    s.put(x, y, z, state("minecraft:gold_block") if y % 6 else state("minecraft:chiseled_stone_bricks"))
                elif edge:
                    s.put(x, y, z, weathered(seed, x, y, z))
                else:
                    s.put(x, y, z, AIR)
    for y in range(4, 24):                                              # the rainbow windows
        col = glass[((y - 4) // 3 + seed) % 7]
        for off in (-1, 0, 1):
            s.put(c + off, y, 2, state(f"minecraft:{col}_stained_glass")); s.put(c + off, y, 10, state(f"minecraft:{col}_stained_glass"))
            s.put(2, y, c + off, state(f"minecraft:{col}_stained_glass")); s.put(10, y, c + off, state(f"minecraft:{col}_stained_glass"))
    for y in range(1, 4):
        s.put(c, y, 10, AIR) if y < 3 else None
    for y in range(1, 25):
        s.put(c, y, 3, state("minecraft:ladder", facing="south", waterlogged="false"))
    s.put(c, 25, 3, AIR)
    for z in range(0, 13):                                              # the lookout
        for x in range(0, 13):
            s.put(x, 25, z, state("minecraft:gold_block") if max(abs(x - c), abs(z - c)) == 6 else state("minecraft:polished_andesite"))
            if max(abs(x - c), abs(z - c)) == 6:
                s.put(x, 26, z, state("minecraft:stone_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false"))
    s.put(c, 25, 3, AIR)
    for k, (cx_, cz_) in enumerate(((2, 2), (10, 2), (2, 10), (10, 10))):   # rainbow crystals
        for y in range(26, 26 + 5):
            s.put(cx_, y, cz_, state(f"minecraft:{glass[(k * 2 + (y - 26) + seed) % 7]}_stained_glass"))
        s.put(cx_, 31, cz_, state("minecraft:sea_lantern"))
    s.put(c, 26, c, state("minecraft:gold_block")); s.put(c, 27, c, state("minecraft:sea_lantern"))
    s.put(c + 2, 26, c, state("asgard:heimdall_altar"))
    blk, tag = chest("west", "asgard:chests/heimdall_shrine")
    s.put(c - 2, 26, c, blk, tag)
    for k in range(7):
        s.put(c - 3 + k, 28 + (k % 2), c + 3 - 6 + 0, state(f"minecraft:{glass[k]}_stained_glass")) if False else None
    return s


# ---------- the rune circle: three variants ----------

def rune_circle(seed):
    rnd = random.Random(seed * 15485863 + 3)
    N, c = 17, 8
    s = Structure(N, 9, N)
    for z in range(N):
        for x in range(N):
            d = math.hypot(x - c, z - c)
            if d <= 8.3:
                r = hole(x + seed * 7, 0, z)
                s.put(x, 0, z, state("minecraft:mossy_cobblestone") if r < 28 else state("minecraft:polished_andesite") if r < 70
                      else state("minecraft:stone_bricks"))
            if 3.4 <= d <= 4.5:
                s.put(x, 0, z, RUNE_GLOW)
    n = rnd.randint(8, 11)
    for k in range(n):
        a = k * math.tau / n + rnd.uniform(-0.1, 0.1)
        px, pz = c + round(math.cos(a) * 7), c + round(math.sin(a) * 7)
        h = rnd.randint(3, 6)
        if rnd.random() < 0.25:
            h = rnd.randint(1, 2)
            s.put(px + rnd.choice((-1, 1)), 1, pz + rnd.choice((-1, 1)), RUNE)
        for y in range(1, h + 1):
            s.put(px, y, pz, RUNE)
        if h >= 3:
            s.put(px, h + 1, pz, state("minecraft:stone_brick_slab", type="bottom", waterlogged="false") if k % 3 else RUNE_GLOW)
            if k % 3 == 1:
                s.put(px, h + 2, pz, state("minecraft:soul_lantern", hanging="false", waterlogged="false"))
    s.put(c, 0, c, state("minecraft:mossy_stone_bricks"))
    blk, tag = chest("south", "asgard:chests/rune_circle")
    s.put(c, 1, c, blk, tag)
    s.put(c, 2, c, state("minecraft:soul_lantern", hanging="false", waterlogged="false"))
    return s


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for pattern in ("yggdrasil*.nbt", "thors_shrine*.nbt", "rune_circle*.nbt", "*_shrine_*.nbt"):
        for old in OUT.glob(pattern):
            old.unlink()
    builds = [(f"yggdrasil_{i}", (lambda i=i: yggdrasil(i))) for i in range(VARIANTS)]
    builds += [(f"thors_shrine_{i}", (lambda i=i: thors_shrine(i))) for i in range(SHRINE_VARIANTS)]
    builds += [(f"rune_circle_{i}", (lambda i=i: rune_circle(i))) for i in range(CIRCLE_VARIANTS)]
    fns = dict(odin_shrine=odin_shrine, freyja_shrine=freyja_shrine, loki_shrine=loki_shrine, freyr_shrine=freyr_shrine,
               tyr_shrine=tyr_shrine, heimdall_shrine=heimdall_shrine)
    for nm, fn in fns.items():
        builds += [(f"{nm}_{i}", (lambda fn=fn, i=i: fn(i))) for i in range(SHRINE_SEEDS)]
    for name, build in builds:
        st = build()
        data = st.dumps()
        (OUT / f"{name}.nbt").write_bytes(data)
        back = nbt.loads(data)
        n = len(back["blocks"][1][1])
        assert n == len(st.blocks), name
        print(f"{name}: size {st.size}, {n} blocks, {len(back['palette'][1][1])} states, {len(data)} bytes")
