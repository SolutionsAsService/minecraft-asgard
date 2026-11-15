#!/usr/bin/env python3
"""Build the Asgard site (site/) from the mod's own data.

Reads src/main/resources/assets/asgard/potions.json (the six gods, their potions, ingredients and lore) and
tools/gen_assets.py (effect display names). Every figure, table row and colour check on the site is computed here.
In-game screenshots are copied from site/img/shots/ if present; a page never refers to a capture that does not exist.

    python3 _src/build_site.py

The output (site/) is committed. The deploy serves it as static files and never runs this script.
"""

import html
import importlib.util
import json
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "site"
SITE_URL = "https://minecraft-asgard.shadw.app"
ASSETS = REPO / "src/main/resources/assets/asgard"

# Minecraft's dye colours, read from the game's net.minecraft.world.item.DyeColor class (1.21.4).
# The Bifrost in the screenshots is built from stained glass in these colours; the site uses the same ones.
DYE = dict(white="#F9FFFE", orange="#F9801D", magenta="#C74EBD", light_blue="#3AB3DA", yellow="#FED83D",
           lime="#80C71F", pink="#F38BAA", gray="#474F52", light_gray="#9D9D97", cyan="#169C9C",
           purple="#8932B8", blue="#3C44AA", brown="#835432", green="#5E7C16", red="#B02E26", black="#1D1D21")

# One hue per god (from the lore), and yellow reserved for Asgard's gold: the argument and the action.
GOD_DYE = {"Thor": "light_blue", "Frigg": "white", "Heimdall": "orange", "Odin": "magenta",
           "Freyja": "pink", "Loki": "lime"}
SIGNAL = DYE["yellow"]
INK = "#0b0b0d"
SKY = "#131316"                                   # hero slab: the black dye, darkened
GROUND = DYE["black"]                             # page ground
BIFROST = ["red", "orange", "yellow", "lime", "light_blue", "blue", "purple"]


# ---------- colour: measured, not asserted ----------

def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(rgb(a), rgb(b)))


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(h):
    r, g, b = rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def lab(h):
    r, g, b = [c / 255 for c in rgb(h)]

    def f(c):
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

    r, g, b = f(r), f(g), f(b)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def t(v):
        return v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116

    return (116 * t(y) - 16, 500 * (t(x) - t(y)), 200 * (t(y) - t(z)))


def delta_e(a, b):
    return math.dist(lab(a), lab(b))


CARD = mix(GROUND, DYE["white"], 0.06)
TEXT = DYE["white"]
MUTED = DYE["light_gray"]


def readable(hue, bg, floor=4.5):
    """Mix a hue toward white until it is readable as small text on bg."""
    for step in range(0, 21):
        c = mix(hue, DYE["white"], step / 20)
        if contrast(c, bg) >= floor:
            return c
    return DYE["white"]


def check_palette():
    hues = {g: DYE[d] for g, d in GOD_DYE.items()}
    pairs = []
    names = list(hues) + ["Asgard gold"]
    cols = list(hues.values()) + [SIGNAL]
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((delta_e(cols[i], cols[j]), names[i], names[j]))
    worst = min(pairs)
    report = {
        "min_delta_e": round(worst[0], 1), "min_pair": f"{worst[1]} / {worst[2]}",
        "min_contrast_hue_on_card": round(min(contrast(c, CARD) for c in cols), 2),
        "text_on_card": round(contrast(TEXT, CARD), 2), "muted_on_card": round(contrast(MUTED, CARD), 2),
        "hues": hues,
    }
    tinted = {g: mix(GROUND, c, 0.08) for g, c in hues.items()}
    report["min_text_hue_on_tint"] = round(min(contrast(readable(hues[g], tinted[g]), tinted[g]) for g in hues), 2)
    if report["min_text_hue_on_tint"] < 4.5:
        raise SystemExit("palette fails: a god's text hue is under 4.5:1 on its tinted page ground")
    if worst[0] < 30:
        raise SystemExit(f"palette fails: {worst[1]} vs {worst[2]} ΔE {worst[0]:.1f} < 30")
    if report["min_contrast_hue_on_card"] < 3 or report["text_on_card"] < 4.5 or report["muted_on_card"] < 4.5:
        raise SystemExit(f"palette fails contrast: {report}")
    return report


# ---------- data ----------

def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def effect_names():
    spec = importlib.util.spec_from_file_location("gen_assets", REPO / "tools/gen_assets.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EFFECT_NAMES


_MORE = []


def load():
    data = read_json(ASSETS / "potions.json")
    manifest = read_json(REPO / "shadw.mod.json")
    gods = []
    for p in data["potions"]:
        if p["god"] not in GOD_DYE:
            continue
        gods.append({**p, "slug": p["god"].lower(), "dye": GOD_DYE[p["god"]], "hue": DYE[GOD_DYE[p["god"]]]})
    _MORE[:] = [p for p in data["potions"] if p["god"] not in GOD_DYE]
    return data, manifest, gods


def esc(v):
    return html.escape(str(v), quote=True)


def roman(n):
    return {1: "I", 2: "II", 3: "III", 4: "IV"}.get(n, str(n))


def dur(s):
    return f"{s // 60}:{s % 60:02d}"


def fx_text(names, e):
    return f"{names.get(e['effect'], e['effect'])} {roman(e['amplifier'] + 1)} for {dur(e['seconds'])}"


def shot(name):
    """Path of an in-game screenshot if it exists, else None."""
    return f"/img/shots/{name}.png" if (SITE / "img/shots" / f"{name}.png").exists() else None


# ---------- pixel art: emblems and the bottle, drawn as SVG ----------

class Grid:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.px[(x, y)] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(16):
            for x in range(16):
                if math.hypot(x - cx, y - cy) <= r:
                    self.put(x, y, c)

    def erase_disc(self, cx, cy, r):
        for k in [k for k in self.px if math.hypot(k[0] - cx, k[1] - cy) <= r]:
            del self.px[k]

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = max(abs(x1 - x0), abs(y1 - y0)) * 2 or 1
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            y = round(y0 + (y1 - y0) * i / n)
            for dx in range(thick):
                for dy in range(thick):
                    self.put(x + dx, y + dy, c)

    def outline(self, c=INK):
        add = {}
        for (x, y) in self.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                k = (x + dx, y + dy)
                if k not in self.px and 0 <= k[0] < 16 and 0 <= k[1] < 16:
                    add[k] = c
        self.px.update(add)

    def svg(self, size=64, label=""):
        rects = []
        for y in range(16):
            run = None
            for x in range(17):
                c = self.px.get((x, y)) if x < 16 else None
                if run and c == run[1]:
                    continue
                if run:
                    rects.append(f'<rect x="{run[0]}" y="{y}" width="{x - run[0]}" height="1" fill="{run[1]}"/>')
                run = (x, c) if c else None
        role = f'role="img" aria-label="{esc(label)}"' if label else 'aria-hidden="true"'
        return (f'<svg class="px" viewBox="0 0 16 16" width="{size}" height="{size}" {role} '
                f'shape-rendering="crispEdges">{"".join(rects)}</svg>')


def emblem(god, size=64, label=""):
    g = Grid()
    W, LG, GR, BR, Y, O = DYE["white"], DYE["light_gray"], DYE["gray"], DYE["brown"], DYE["yellow"], DYE["orange"]
    hue = DYE[GOD_DYE[god]]
    if god == "Thor":                                     # Mjolnir with a bolt
        g.rect(3, 2, 12, 6, LG); g.rect(3, 2, 12, 2, W); g.rect(3, 6, 12, 6, GR)
        g.rect(7, 3, 8, 5, hue); g.put(6, 4, hue); g.put(9, 4, hue)
        g.rect(7, 7, 8, 14, BR); g.rect(6, 14, 9, 14, GR)
    elif god == "Frigg":                                  # distaff and spindle
        g.line(4, 14, 11, 5, BR, 2)
        g.disc(11, 4, 3, W); g.put(10, 3, LG); g.put(12, 5, LG)
        g.disc(6, 10, 2, LG); g.put(6, 10, GR)
        g.line(10, 7, 8, 9, W)
    elif god == "Heimdall":                               # Gjallarhorn
        g.disc(7, 8, 6, Y); g.erase_disc(10, 5, 5)
        g.rect(11, 2, 13, 4, O); g.put(12, 3, Y)
        g.line(2, 10, 5, 13, O)
    elif god == "Odin":                                   # the eye given at Mimir's well
        for y in range(16):
            for x in range(16):
                if ((x - 7.5) / 6.8) ** 2 + ((y - 8) / 3.6) ** 2 <= 1:
                    g.put(x, y, W)
        g.disc(7.5, 8, 2.7, hue); g.disc(7.5, 8, 1.2, INK); g.put(6, 7, W)
        g.line(2, 5, 13, 5, LG)
    elif god == "Freyja":                                 # Brisingamen, the necklace
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7)
                if 4.2 <= d <= 5.8 and y < 13:
                    g.put(x, y, Y)
        g.disc(7.5, 13, 1.7, hue); g.put(7, 12, W)
        g.put(7, 1, hue); g.put(8, 1, hue)
    elif god == "Loki":                                   # the serpent
        for t in range(0, 118):
            s = t / 9
            g.rect(round(8 + 4 * math.sin(s * 0.95)), round(2 + s), round(8 + 4 * math.sin(s * 0.95)) + 1,
                   round(2 + s) + 1, hue)
        g.rect(7, 1, 10, 3, hue); g.put(8, 2, DYE["red"]); g.put(9, 2, DYE["red"])
        g.put(8, 0, DYE["red"]); g.put(10, 0, DYE["red"])
    g.outline()
    return g.svg(size, label)


def bottle(hue, size=64, label=""):
    g = Grid()
    G = "#c9d6dc"
    g.rect(6, 0, 9, 1, DYE["brown"]); g.rect(6, 2, 9, 4, G)
    g.rect(4, 5, 11, 6, G)
    g.rect(3, 7, 12, 14, G)
    g.rect(4, 8, 11, 13, hue)
    g.rect(4, 8, 11, 8, mix(hue, "#ffffff", 0.35))
    g.put(5, 10, "#ffffff")
    g.outline()
    return g.svg(size, label)


# ---------- page shell ----------

NAV = [("index.html", "Home", "home"), ("gods.html", "Gods", "gods"), ("relics.html", "Relics", "relics"),
       ("structures.html", "Structures", "structures"), ("shrines.html", "Shrines", "shrines"), ("creatures.html", "Creatures", "creatures"), ("install.html", "Install", "install"),
       ("developers.html", "Developers", "developers")]


def typo(markup):
    """Real apostrophes everywhere in prose and attributes; <pre> and <code> keep straight ones."""
    out = []
    for part in re.split(r"(<pre.*?</pre>|<code>.*?</code>)", markup, flags=re.S):
        if part.startswith("<pre") or part.startswith("<code>"):
            out.append(part)
            continue
        part = part.replace("&#x27;", "'")
        # text between tags and quoted attribute values: swap ' for the right single quote
        part = re.sub(r"'", "\u2019", part) if "<style" not in part else part
        out.append(part)
    return "".join(out)


def page(title, desc, body, active, path, hue=None, image="/img/og.png", hue_text=None):
    nav = "".join(f'<a href="/{h}"{" aria-current=\"page\"" if k == active else ""}>{t}</a>' for h, t, k in NAV)
    style = f' style="--hue:{hue};--hue-text:{hue_text or hue}"' if hue else ""
    return typo(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(SITE_URL + '/' + path)}">
<meta property="og:image" content="{SITE_URL}{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/img/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css">
</head>
<body{style}>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="/index.html"><span class="brand-mark" aria-hidden="true"></span>ASGARD</a>
  <nav aria-label="Primary">{nav}</nav>
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer class="foot">
  <p>A Minecraft mod for the Nordic Pantheon pack. Source: <a href="https://github.com/SolutionsAsService/minecraft-asgard">minecraft-asgard</a>. Built with <a href="https://github.com/SolutionsAsService/shadw-modding">shadw-modding</a>. Credit: SolutionsAsService. Dark&nbsp;theme&nbsp;only. English&nbsp;only.</p>
</footer>
</body>
</html>
""")


# ---------- the signature figure: the real hall, the pillars as links ----------

# World x of each pillar in the test scene, and pixels per block at the pillars' depth in hall.png
# (measured from the two central gold capitals at x=566 and x=711 in the 1280x720 capture).
PILLAR_X = [-15, -9, -3, 3, 9, 15]
PX_PER_BLOCK = (711 - 566) / 6


def headline_effect(names, g):
    e = g["effects"][0]
    return f"{names.get(e['effect'], e['effect'])} {roman(e['amplifier'] + 1)}"


def headline_name(names, g):
    e = g["effects"][0]
    return names.get(e["effect"], e["effect"])


def hall_figure(gods, names):
    """Wide screens: the unretouched capture with each pillar a link. Narrow screens: tiles."""
    img = shot("hall")
    spots = ""
    if img:
        for g, wx in zip(gods, PILLAR_X):
            pct = (640 + PX_PER_BLOCK * wx) / 1280 * 100
            spots += (f'<a class="spot" style="--x:{pct:.1f}%;--hue:{g["hue"]}" href="/gods/{g["slug"]}.html">'
                      f'{emblem(g["god"], 36)}<span class="spot-name">{esc(g["god"])}</span>'
                      f'<span class="spot-fx">{esc(headline_name(names, g))}</span></a>')
        hall = (f'<figure class="hall"><img class="hall-img" src="{img}" width="1280" height="720" '
                f'alt="The hall in Minecraft: six quartz pillars with gold capitals under an arch of rainbow-coloured stained glass, '
                f'each pillar with an item frame and a sign.">{spots}'
                f'<p class="hall-note">Photo: a test world built with server commands, not part of the mod. The labels are the site\'s.</p></figure>')
    else:
        hall = ""
    tiles = "".join(
        f'<li><a class="tile" style="--hue:{g["hue"]}" href="/gods/{g["slug"]}.html">{emblem(g["god"], 56)}'
        f'<span class="tile-text"><span class="tile-name">{esc(g["god"])}</span>'
        f'<span class="tile-meta">{esc(headline_effect(names, g))}</span></span></a></li>' for g in gods)
    bands = "".join(f'<span style="background:{DYE[n]}"></span>' for n in BIFROST)
    return hall, f'<div class="bifrost" aria-hidden="true">{bands}</div><ol class="tiles" aria-label="The six gods">{tiles}</ol>'


# ---------- pages ----------

def recipe(g, names):
    return f"""<figure class="recipe" aria-label="Brewing recipe: Awkward Potion plus {esc(g['ingredient'].replace('_', ' ').title())} gives {esc(g['name'])}">
  <span class="rslot">{bottle("#5d7bb0", 48)}<span class="rcap">Awkward Potion</span></span>
  <span class="rop" aria-hidden="true">+</span>
  <span class="rslot"><img class="px" src="/img/items/{esc(g['ingredient'])}.png" alt="" width="48" height="48"><span class="rcap">{esc(g['ingredient'].replace('_', ' ').title())}</span></span>
  <span class="rop" aria-hidden="true">=</span>
  <span class="rslot">{bottle(g['hue'], 48)}<span class="rcap">{esc(g['name'])}</span></span>
</figure>"""


def build_index(data, gods, palette, names):
    hall, tiles = hall_figure(gods, names)
    ingame = [(n, a, c) for n, a, c in (
        ("thor", "Thor's pillar in Minecraft, seen from below: an item frame holding a light-blue ingredient above a sign.",
         "Thor's pillar. The item frame holds Thunder Iron, and the sign reads 'Thor'."),
        ("odin", "Odin's pillar in Minecraft, seen from below: an item frame holding a magenta ingredient above a sign.",
         "Odin's pillar. The item frame holds Mimir Glass, and the sign reads 'Odin'. The other four pillars read their god's name.")) if shot(n)]
    gallery = ""
    if ingame:
        figs = "".join(f'<figure class="shot"><img src="{shot(n)}" alt="{esc(a)}" width="1280" height="720" loading="lazy"><figcaption>{esc(c)}</figcaption></figure>' for n, a, c in ingame)
        gallery = (f'<section class="band"><h2>In the game</h2><div class="shots two">{figs}</div>'
                   f'<p class="meta">Captured from a Minecraft 1.21.4 client joined to a Fabric dedicated server with this mod. The pillars, the arch, the item frames and the signs were built with server commands in a flat test world; only the items and potions are the mod.</p></section>')
    world = ""
    if shot("yggdrasil-dusk") and shot("shrine"):
        world = (f'<section class="band"><h2>Out in the world</h2><div class="shots two">'
                 f'<figure class="shot"><img src="{shot("yggdrasil-dusk")}" alt="Yggdrasil at dusk: a giant tree with root ridges and two waterfalls under an orange sky." width="854" height="480" loading="lazy"><figcaption>Yggdrasil at dusk, 100 blocks high. <a href="/structures.html#yggdrasil">The structures</a></figcaption></figure>'
                 f'<figure class="shot"><img src="{shot("shrine")}" alt="Thor\'s shrine: four lightning-rod pillars around a spire." width="854" height="480" loading="lazy"><figcaption>Thor\'s shrine holds Mjölnir. <a href="/relics.html">The relics</a></figcaption></figure></div>'
                 f'<p class="meta">Captured in a flat test world on a Minecraft 1.21.4 client; the structures and items are the mod, the grass and sky are vanilla.</p></section>')
    body = f"""
<section class="hero" aria-labelledby="h1">
  <div class="hero-inner">
    <div class="hero-title"><p class="eyebrow">Minecraft mod · Nordic Pantheon</p><h1 id="h1" class="mc">ASGARD</h1></div>
    <div class="hero-tag"><p class="tag">The Norse world in Minecraft: six gods as potions, Mjölnir and two more relics, and structures to find them in.</p>
    <p class="meta">Registered in code and loaded on a real server. Brewing, using the relics and natural structure spawning are not yet tested.</p></div>
    <p class="action"><a class="btn" href="/gods.html">Meet the gods</a> <a class="btn btn-alt" href="/install.html">Install</a> <a class="btn btn-quiet" href="/developers.html">For developers</a></p>
    <div class="hero-fig">{hall}{tiles}</div>
  </div>
</section>
<section class="band">
  <h2>How a draught is made</h2>
  <p>In a brewing stand, put an <em>Awkward Potion</em> (the base potion: a water bottle brewed with Nether Wart, a plant item from the Nether) in a bottle slot and one god's ingredient on top. Each god has one ingredient, one potion, and a line of lore on the ingredient's tooltip.</p>
  {recipe(gods[0], names)}
  <p class="meta">The picture shows Thor's Valor. The bottles are illustrations, not captures from the game, and the potion's bottle colour here is a design choice. A brew in a world is not yet tested.</p>
</section>
{gallery}
{world}
"""
    return page("Asgard: the Norse world in Minecraft", "A Minecraft mod: the six gods as potions, Mjölnir and two more relics, Yggdrasil, Thor's shrine and rune circles.", body, "home", "index.html")


def more_potion_card(pt, names):
    fx = "".join(f"<li>{esc(fx_text(names, e))}</li>" for e in pt["effects"])
    ing = pt["ingredient"].replace("_", " ").title()
    return (f'<article class="relic"><div class="relic-art">{sprite(pt["ingredient"], 80, ing)}</div>'
            f'<div><h3>{esc(pt["name"])}</h3><p class="meta">{esc(pt["god"])}, {esc(pt["epithet"])} · {esc(pt["domain"])}</p>'
            f'<ul class="fx">{fx}</ul><p class="meta">Brewed from an Awkward Potion and {esc(ing)}. {esc(pt["lore"])}</p></div></article>')


def build_gods(data, gods, palette, names):
    more_cards = "".join(more_potion_card(pt, names) for pt in _MORE)
    roll = ""
    for g in gods:
        pic = shot(g["slug"])
        photo = (f'<a class="roll-photo" href="/gods/{g["slug"]}.html" tabindex="-1" aria-hidden="true"><img src="{pic}" alt="" width="1280" height="720" loading="lazy"></a>') if pic else ""
        roll += f"""<article class="roll" style="--hue:{g['hue']}">
  {photo}
  <div class="roll-body">
    <div class="roll-emblem">{emblem(g['god'], 56)}</div>
    <div>
      <h2><a href="/gods/{g['slug']}.html">{esc(g['god'])}</a></h2>
      <p class="epithet-line">{esc(g['epithet'])} · {esc(g['domain'])}</p>
      <p><b>{esc(g['name'])}</b>: {', '.join(esc(fx_text(names, e)) for e in g['effects'])}</p>
    </div>
  </div>
</article>"""
    body = f"""
<section class="page wide">
  <p class="eyebrow">Gods</p>
  <h1 class="mc-h">The six gods</h1>
  <p class="lede">Six pillars, six gods, six draughts. Each page has the potion, its effects and durations, the ingredient and its lore, and the recipe.</p>
  <p class="meta">The photographs are close-ups of the test-world pillars. The epithets, domains and lore lines are the mod's own flavour text, not scholarship. The potion effects are game design.</p>
  <div class="rolls">{roll}</div>
  <h2>The wider pantheon</h2>
  <p>Five more draughts, from the shrines and the world tree. Their ingredients are found in shrine chests; Yggdrasil's Essence is crafted.</p>
  <div class="relics">{more_cards}</div>
  <p class="meta">Honest limits: the design asks for crop growth, extra experience and knockback resistance. Vanilla potion effects cannot do those, so Freyr's Blessing gives Luck and Saturation, Mimir's Knowledge gives Night Vision and Luck, and Tyr's Courage gives Strength and Resistance. The brew recipes are registered; brewing in a world is not yet tested.</p>
  <h2>Colours</h2>
  <p>Each god has one colour, taken from Minecraft's dye colours: {', '.join(esc(g['god']) + ' ' + esc(g['dye'].replace('_', ' ')) for g in gods)}. The colour is never the only cue: every god also has a name and an emblem. The smallest difference between any two god colours (CIE76) is ΔE {palette['min_delta_e']}, between {esc(palette['min_pair'])}. The build fails below 30.</p>
</section>"""
    return page("The six gods of Asgard", "Thor, Frigg, Heimdall, Odin, Freyja and Loki: their potions, effects and ingredients.", body, "gods", "gods.html")


def build_god(i, g, gods, palette, names):
    prev_g, next_g = gods[i - 1], gods[(i + 1) % len(gods)]
    banner = shot(g["slug"])
    ing = g["ingredient"].replace("_", " ").title()
    pic = (f'<figure class="shot wide"><img src="{banner}" alt="Minecraft: {esc(g["god"])}\'s pillar seen from below, an item frame holding {esc(ing)} above a sign, the rainbow arch behind." width="1280" height="720"><figcaption>In the game: {esc(g["god"])}\'s pillar in a test world. The item frame holds {esc(ing)}, and the sign reads \'{esc(g["god"])}\'.</figcaption></figure>') if banner else ""
    fx = "".join(f"<li>{esc(fx_text(names, e))}</li>" for e in g["effects"])
    tinted = mix(GROUND, g["hue"], 0.08)
    hue_text = readable(g["hue"], tinted)
    alt = " alt" if i % 2 else ""
    gloss = {"heimdall": "The Bifrost is the burning rainbow bridge between Asgard and the world of humans."}.get(g["slug"], "")
    gloss_p = f'<p class="meta">{esc(gloss)}</p>' if gloss else ""
    body = f"""
<section class="page god{alt}">
  <p class="eyebrow">God of Asgard</p>
  <div class="god-head">
    <div class="god-emblem">{emblem(g['god'], 128, g['god'] + ' emblem')}</div>
    <div>
      <h1 class="mc-h">{esc(g['god'])}</h1>
      <p class="epithet">{esc(g['epithet'])}</p>
      <p class="meta">Domain: {esc(g['domain'])}</p>
      {gloss_p}
    </div>
  </div>
  <div class="god-body">
  {pic}
  <div class="cols">
    <section>
      <h2>{esc(g['name'])}</h2>
      <ul class="fx big">{fx}</ul>
      <p class="meta">Durations are from the mod's data. Levels count from I.</p>
    </section>
    <section>
      <h2>The ingredient</h2>
      <p class="ing"><img class="px" src="/img/items/{esc(g['ingredient'])}.png" alt="" width="64" height="64"> <b>{esc(ing)}</b></p>
      <blockquote>{esc(g['lore'])}</blockquote>
    </section>
  </div>
  </div>
  <h2>Brew it</h2>
  {recipe(g, names)}
  <p class="meta">Brewing stand: an Awkward Potion in a bottle slot, the ingredient on top. The recipe is registered in code and counted in the server log; a brew in a world is not yet tested.</p>
  <p class="pager"><a href="/gods/{prev_g['slug']}.html">← {esc(prev_g['god'])}</a> <a href="/gods.html">All gods</a> <a href="/gods/{next_g['slug']}.html">{esc(next_g['god'])} →</a></p>
</section>"""
    return page(f"{g['god']}: {g['name']}", f"{g['god']}, {g['epithet']}: the potion {g['name']}, its effects, ingredient and lore.", body, "gods", f"gods/{g['slug']}.html", hue=g["hue"], hue_text=hue_text)


# ---------- relics and structures: every figure is read from the mod's own data ----------

DATA = REPO / "src/main/resources/data/asgard"


def content():
    return read_json(ASSETS / "content.json")


def nbt_facts(name):
    if not (DATA / "structure" / f"{name}.nbt").exists():
        name = f"{name}_0"
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    import nbt
    root = nbt.loads((DATA / "structure" / f"{name}.nbt").read_bytes())
    return {"size": tuple(root["size"][1][1]), "blocks": len(root["blocks"][1][1])}


def spread(name):
    return read_json(DATA / "worldgen/structure_set" / f"{name}.json")["placement"]


def biomes(name):
    vals = read_json(DATA / "tags/worldgen/biome/has_structure" / f"{name}.json")["values"]
    return [v.replace("#minecraft:is_", "").replace("#minecraft:", "").replace("minecraft:", "").replace("_", " ") for v in vals]


def chest_chance(chest, item):
    """Chance that a chest's first pool gives `item`: weight over the pool's total weight (one roll)."""
    entries = read_json(DATA / "loot_table/chests" / f"{chest}.json")["pools"][0]["entries"]
    total = sum(e["weight"] for e in entries)
    mine = sum(e["weight"] for e in entries if e.get("name") == item)
    return mine, total


def pct(a, b):
    return f"{round(100 * a / b)}%"


def sprite(name, size=96, label=""):
    return (f'<img class="px" src="/img/items/{name}.png" width="{size}" height="{size}" alt="{esc(label)}">')


def copy_content_items():
    import shutil
    for n in ("mjolnir", "gungnir", "gjallarhorn", "yggdrasil_leaf", "yggdrasil_fruit", "yggdrasil_sap", "sacred_root"):
        shutil.copyfile(ASSETS / "textures/item" / f"{n}.png", SITE / "img/items" / f"{n}.png")
    for n in ("rune_stone", "yggdrasil_log", "yggdrasil_leaves", "yggdrasil_rune", "yggdrasil_heartwood", "ancient_bark", "golden_leaves"):
        shutil.copyfile(ASSETS / "textures/block" / f"{n}.png", SITE / "img/items" / f"{n}.png")


def relic_card(name, title, god, lines, sprite_name):
    li = "".join(f"<li>{x}</li>" for x in lines)
    return (f'<article class="relic"><div class="relic-art">{sprite(sprite_name, 96, title)}</div>'
            f'<div><h3>{esc(title)}</h3><p class="meta">{esc(god)}</p><ul class="fx">{li}</ul></div></article>')


def build_relics(data, gods, manifest):
    c = content()
    mj, gu, gj, fr, bl = c["mjolnir"], c["gungnir"], c["gjallarhorn"], c["yggdrasil_fruit"], c["blessing"]
    sw, st = chest_chance("thors_shrine", "asgard:mjolnir"), chest_chance("rune_circle", "asgard:gungnir")
    sg = chest_chance("yggdrasil_hollow", "asgard:gjallarhorn")
    hit = lambda d: f"{d:g} attack damage plus the 1 of an empty hand (about {d + 1:g} per swing)"
    body = f"""
<section class="page">
  <p class="eyebrow">Relics</p>
  <h1 class="mc-h">Three relics and the world tree</h1>
  <p class="lede">Mjölnir, Gungnir and Gjallarhorn are found in the Norse structures, not crafted. Yggdrasil gives a leaf for one more potion and a fruit to eat.</p>
  <div class="relics">
  {relic_card("mjolnir", "Mjölnir", "Thor's hammer", [
      f"Heavy weapon: +{mj['damage']:g} attack damage ({mj['damage'] + 1:g} with the base 1), attack speed modifier {mj['attack_speed_modifier']:g} (a slow swing), {mj['durability']} durability.",
      f"Right-click: lightning strikes where you look, up to {mj['lightning_range']:g} blocks away. Costs {mj['durability_cost']} durability and has a {mj['cooldown_ticks'] / 20:g}-second cooldown.",
      f"Found in Thor's shrine chests: {sw[0]} in {sw[1]} chests ({pct(*sw)}) hold it."], "mjolnir")}
  {relic_card("gungnir", "Gungnir", "Odin's spear", [
      f"Spear: +{gu['damage']:g} attack damage ({gu['damage'] + 1:g} with the base 1), attack speed modifier {gu['attack_speed_modifier']:g}, {gu['durability']} durability.",
      f"What it hits glows for {gu['glow_seconds']} seconds, through walls.",
      f"Found in rune circle chests: {st[0]} in {st[1]} chests ({pct(*st)}) hold it."], "gungnir")}
  {relic_card("gjallarhorn", "Gjallarhorn", "Heimdall's horn", [
      f"Right-click: a horn blast. Everything living within {gj['radius']:g} blocks glows for {gj['glow_seconds']} seconds, and you run (Speed {roman(gj['speed_amplifier'] + 1)}) for {gj['speed_seconds']} seconds.",
      f"{gj['cooldown_ticks'] / 20:g}-second cooldown, {gj['durability']} uses.",
      f"Found in Yggdrasil's hollow: {sg[0]} in {sg[1]} chests ({pct(*sg)}) hold it."], "gjallarhorn")}
  {relic_card("yggdrasil_fruit", "Yggdrasil Fruit", "Fruit of the world tree", [
      f"Food: restores {fr['nutrition']} hunger. A little saturation ({fr['saturation_modifier']:g}), nothing else.",
      "Dropped by Yggdrasil leaves (5% of the time) and found in its hollow."], "yggdrasil_fruit")}
  {relic_card("yggdrasil_leaf", "Yggdrasil Leaf", "Ingredient", [
      f"Brew it onto an Awkward Potion for the Potion of Blessing: Regeneration {roman(bl['amplifier'] + 1)} for {dur(bl['regeneration_seconds'])}.",
      "Dropped by Yggdrasil leaves (25% of the time) and found in its hollow."], "yggdrasil_leaf")}
  </div>
  <h2>World tree materials</h2>
  <div class="relics">
  {relic_card("yggdrasil_sap", "Yggdrasil Sap", "Ingredient", ["Amber sap. Yggdrasil's logs drop it 6% of the time, golden leaves 12%, and shrine chests hold it.", "Crafted into heartwood and divine essence."], "yggdrasil_sap")}
  {relic_card("sacred_root", "Sacred Root", "Ingredient", ["Found in the god shrines' chests, never grown. Kept for the later recipes in the design doc."], "sacred_root")}
  </div>
  <h2>Recipes</h2>
  <table class="data"><caption class="sr">Crafting recipes</caption><tbody>
  <tr><th scope="row">Yggdrasil Heartwood &times;4</th><td>4 Yggdrasil Logs and 1 Yggdrasil Sap, shapeless</td></tr>
  <tr><th scope="row">Ancient Bark &times;3</th><td>4 Yggdrasil Logs in a 2 by 2 square</td></tr>
  <tr><th scope="row">Divine Essence</th><td>1 Yggdrasil Sap, 1 Golden Apple, 1 Nether Wart, 1 Rune Stone, shapeless. The brewing ingredient for Yggdrasil's Essence.</td></tr>
  <tr><th scope="row">Rune Stone &times;4</th><td>4 Stone Bricks and 1 Gold Nugget, shapeless</td></tr>
  </tbody></table>
  <h2>Blocks</h2>
  <div class="relics">
  {relic_card("yggdrasil_log", "Yggdrasil Log", "Block", ["A log: it burns, an axe breaks it fastest, and it is in the logs tag."], "yggdrasil_log")}
  {relic_card("yggdrasil_leaves", "Yggdrasil Leaves", "Block", ["Leaves that do not decay. They drop a leaf or a fruit, and now and then a gold mote drifts from the underside."], "yggdrasil_leaves")}
  {relic_card("yggdrasil_rune", "Yggdrasil Rune", "Block", ["A glowing gold rune set in the world tree's bark: light level 12, and it sheds sparks. Axe-mineable; found on Yggdrasil, not crafted."], "yggdrasil_rune")}
  {relic_card("yggdrasil_heartwood", "Yggdrasil Heartwood", "Block", ["A dense building block crafted from logs and sap. Axe-mineable."], "yggdrasil_heartwood")}
  {relic_card("ancient_bark", "Ancient Bark", "Block", ["Weathered grey bark. Craft three from four logs."], "ancient_bark")}
  {relic_card("golden_leaves", "Golden World Tree Leaves", "Block", ["Light level 9, and golden motes drift from them often. They drop sap, a leaf or a fruit. Found among Yggdrasil's green leaves."], "golden_leaves")}
  {relic_card("rune_stone", "Rune Stone", "Block", ["Craft four from 4 stone bricks and 1 gold nugget. Found building the shrine and the rune circle."], "rune_stone")}
  </div>
  <p class="meta">Status: the items load, their icons show in a Minecraft 1.21.4 client, and the numbers above are read from the mod's own data file. Using them (the lightning, the horn, the spear's glow) and brewing the Blessing are not yet tested in a world.</p>
</section>"""
    return page("Relics: Mjölnir, Gungnir and Gjallarhorn", "The Asgard mod's three relics, the Yggdrasil items and blocks, with their numbers and where to find them.", body, "relics", "relics.html")


def structure_card(slug, title, blurb, chest, relic_item, shot_names, extra):
    n = nbt_facts(slug)
    s = spread(slug)
    sx, sy, sz = n["size"]
    chance = chest_chance(chest, relic_item)
    figs = "".join(f'<figure class="shot"><img src="{shot(nm)}" alt="{esc(al)}" width="854" height="480" loading="lazy"><figcaption>{esc(cap)}</figcaption></figure>'
                   for nm, al, cap in shot_names if shot(nm))
    rows = (f"<tr><th scope=\"row\">Size</th><td>{sx} by {sz} blocks, {sy} high (about {n['blocks']:,} blocks{', six variants' if slug == 'yggdrasil' else ''})</td></tr>"
            f"<tr><th scope=\"row\">Spacing</th><td>One in every {s['spacing']} by {s['spacing']} chunks, at least {s['separation']} chunks from the next</td></tr>"
            f"<tr><th scope=\"row\">Biomes</th><td>{esc(', '.join(biomes(slug)))}</td></tr>"
            f"<tr><th scope=\"row\">Chest</th><td>{esc(extra)} {chance[0]} in {chance[1]} chests ({pct(*chance)}) hold the relic.</td></tr>")
    return (f'<section class="struct" id="{slug}"><h2>{esc(title)}</h2><p>{esc(blurb)}</p><div class="shots two">{figs}</div>'
            f'<table class="data"><caption class="sr">{esc(title)}: facts</caption><tbody>{rows}</tbody></table></section>')


def advancement_titles():
    out = []
    for f in sorted((DATA / "advancement").glob("*.json")):
        d = read_json(f)
        if f.stem != "root":
            out.append(d["display"]["title"]["text"])
    return out


def build_structures(data, gods, manifest):
    adv_list = ", ".join(esc(x) for x in advancement_titles())
    cards = "".join([
        structure_card("yggdrasil", "Yggdrasil", "The world tree: a buttressed trunk with a gold rune spiral, root ridges that run out along the ground, sprawling branches under raised leaf clusters, a walkway with lanterns along one branch, vines, hanging lanterns and glowing fruit, and two waterfalls falling into stone-ringed pools. An amethyst hollow at its foot has a doorway and a chest, and a ladder climbs the trunk from the hollow to Valhalla, a hall on the crown with a chest of its own. Six variants are in the world pool, so no two trees need match.",
                       "yggdrasil_hollow", "asgard:gjallarhorn",
                       [("yggdrasil", "Yggdrasil by day: a huge tree with root ridges, two waterfalls and a wide canopy.", "By day. A flat test world; the grass and sky are vanilla."),
                        ("yggdrasil-dusk", "Yggdrasil at dusk against an orange sky.", "At dusk."),
                        ("yggdrasil-top", "The crown of Yggdrasil from the side, with the roofed hall of Valhalla at the top.", "The crown, with Valhalla at the top."),
                        ("valhalla", "Inside Valhalla: a ring of pillars, a roof with an open centre, lanterns, and a chest on a gold block.", "Inside Valhalla."),
                        ("yggdrasil-glow", "Looking up the trunk: a spiral of gold runes beside a waterfall.", "Looking up the trunk, along the rune spiral."),
                        ("yggdrasil-lanterns", "Under a branch: glowing gold runes set into the wood, with leaves and the sunset beyond.", "Rune veins under a branch."),
                        ("yggdrasil-door", "The root ridges and the doorway at the foot of the tree.", "The foot of the tree and its doorway.")],
                       "The hollow holds the Gjallarhorn, fruit, leaves and a golden apple. Valhalla, up the ladder, holds a relic more often."),
        structure_card("thors_shrine", "Thor's shrine", "A three-tier stone dais with four lightning-rod pillars, glowing rune inlays, braziers at the four sides and a tall lightning-rod spire over a gold altar and chest. Three variants: one pillar is broken in each, and the stone is cracked and mossy to different degrees.",
                       "thors_shrine", "asgard:mjolnir",
                       [("shrine", "Thor's shrine by day: tiered stone dais, four pillars topped with lightning rods and a central spire.", "By day."),
                        ("shrine-dusk", "Thor's shrine at dusk, with braziers lit and rune inlays glowing.", "At dusk.")],
                       "The altar chest holds Mjölnir, metal and rune stone."),
        structure_card("rune_circle", "Rune circle", "Eight to eleven rune-stone pillars of uneven height around a floor of mossy stone, a glowing rune ring, soul lanterns on some capitals and a chest at the centre. Three variants; some pillars have fallen.",
                       "rune_circle", "asgard:gungnir",
                       [("rune-circle", "A rune circle by day: pillars carved with gold runes around a mossy floor.", "By day."),
                        ("rune-circle-dusk", "The rune circle at dusk, its runes glowing.", "At dusk.")],
                       "The chest holds Gungnir, ingredients for the gods' potions and rune stone."),
    ])
    body = f"""
<section class="page">
  <p class="eyebrow">Structures</p>
  <h1 class="mc-h">Norse structures in the world</h1>
  <p class="lede">Three structures generate in new worlds. Each hides a relic in its chest. Walk, look, and bring a sword. Yggdrasil is the largest.</p>
  {cards}
  <h2>Advancements</h2>
  <p>The mod adds a small tree of advancements: {adv_list}.</p>
  <p class="meta">Status: the structures generate with the game's <code>/place structure</code> command on a Minecraft 1.21.4 server (Yggdrasil, the shrine and the circle were each placed that way; the variants and Valhalla's ladder and chest were placed as templates for the captures, and nobody has climbed the ladder yet). The advancements load without errors but none has been earned in play, and the captures above are from that client in a flat test world (the stone, trees and sky are vanilla). That the structures appear on their own in a fresh survival world is not yet confirmed: the game's <code>/locate</code> found nothing near spawn on the test seed, and the same search for a vanilla village also found nothing, so that test proved neither way.</p>
</section>"""
    return page("Structures: Yggdrasil, Thor's shrine and the rune circle", "The three Norse structures in the Asgard mod, where they generate and what is in their chests.", body, "structures", "structures.html")



# ---------- the Shrines page: seven gods, their altars, offerings and chests ----------

SHRINES = [  # god key, shrine slug, display name, epithet, blurb, shot names (day, dusk)
    ("thor", "thors_shrine", "Thor", "God of Thunder", "The first shrine: a tiered stone dais, lightning-rod pillars, braziers and a spire over a gold altar.", ("shrine", "shrine-dusk")),
    ("odin", "odin_shrine", "Odin", "Allfather", "A stone monolith with glowing runes, a one-eyed statue under a wide hat, two raven statues, and lanterns hanging from carved posts.", ("shrine-odin", "shrine-odin-dusk")),
    ("freyja", "freyja_shrine", "Freyja", "Goddess of Love and Magic", "A garden of golden and pink flowers, crystals that glow, a cherry pergola and quartz cat statues.", ("shrine-freyja", "shrine-freyja-dusk")),
    ("loki", "loki_shrine", "Loki", "God of Mischief", "A hidden underground altar under a hatch: green froglight flames, strange statues, cobwebs and slime.", ("shrine-loki",)),
    ("freyr", "freyr_shrine", "Freyr", "God of Prosperity", "A walled farm of ripe golden wheat watered by two channels, with carved totems and hay-bale seats around the altar.", ("shrine-freyr",)),
    ("tyr", "tyr_shrine", "Tyr", "God of War", "A battlefield monument: two huge crossed swords, a wall of shields (target blocks) and red banners.", ("shrine-tyr",)),
    ("heimdall", "heimdall_shrine", "Heimdall", "Guardian of the Bifrost", "A 34-block watchtower with golden corner pillars, rainbow glass windows, a ladder inside and a lookout of rainbow crystals.", ("shrine-heimdall", "shrine-heimdall-dusk")),
]


def item_label(rid):
    return rid.split(":")[-1].replace("_", " ").title()


def chest_contents(slug):
    pools = read_json(DATA / "loot_table/chests" / f"{slug}.json")["pools"]
    names = []
    for pool in pools:
        for e in pool["entries"]:
            if e.get("type") == "minecraft:empty":
                continue
            if e.get("name") == "minecraft:potion":
                pid = e["functions"][0]["id"]
                label = "Potion of " + next((q["name"] for q in read_json(ASSETS / "potions.json")["potions"] if "asgard:" + q["id"] == pid), item_label(pid))
            else:
                label = item_label(e["name"])
            if label not in names:
                names.append(label)
    return names


def shrine_section(god, slug, name, epithet, blurb, shots, names):
    alt = content()["altars"][god]
    fx = ", ".join(f"{names.get(e[0], e[0].split(':')[-1].replace('_', ' ').title())} {roman(e[2] + 1)} for {dur(e[1])}" for e in alt["effects"])
    figs = "".join(f'<figure class="shot"><img src="{shot(n)}" alt="{esc(name)}\'s shrine." width="854" height="480" loading="lazy"><figcaption>{esc(name)}\'s shrine.</figcaption></figure>' for n in shots if shot(n))
    n0 = nbt_facts(slug)
    sx, sy, sz = n0["size"]
    s = spread(slug)
    variants = len(list((DATA / "structure").glob(f"{slug}_*.nbt")))
    rows = (f"<tr><th scope=\"row\">Size</th><td>{sx} by {sz} blocks, {sy} high; {variants} variants</td></tr>"
            f"<tr><th scope=\"row\">Spacing</th><td>One in every {s['spacing']} by {s['spacing']} chunks</td></tr>"
            f"<tr><th scope=\"row\">Biomes</th><td>{esc(', '.join(biomes(slug)))}</td></tr>"
            f"<tr><th scope=\"row\">Altar</th><td>Hold {alt['count']} {esc(item_label(alt['offering']))} and use the altar: {esc(fx)}.</td></tr>"
            f"<tr><th scope=\"row\">Chest</th><td>{esc(', '.join(chest_contents(slug)))}</td></tr>")
    return (f'<section class="struct" id="{slug}"><p class="eyebrow">{esc(epithet)}</p><h2>{esc(name)}</h2><p>{esc(blurb)}</p>'
            f'<div class="shots two">{figs}</div><table class="data"><caption class="sr">{esc(name)}\'s shrine: facts</caption><tbody>{rows}</tbody></table></section>')


def build_shrines(data, gods, manifest, names):
    secs = "".join(shrine_section(g, sl, n, e, b, sh, names) for g, sl, n, e, b, sh in SHRINES)
    body = f"""
<section class="page">
  <p class="eyebrow">Shrines</p>
  <h1 class="mc-h">Seven shrines, seven altars</h1>
  <p class="lede">Each god has a shrine in the world and an altar block to make an offering at. Hold the offering, use the altar, and the blessing is yours.</p>
  {secs}
  <h2>Not built yet</h2>
  <p>The <a href="https://github.com/SolutionsAsService/minecraft-asgard/blob/main/design/expand.md">expansion design</a> also names rewards this phase does not have: Seidr magic and the feathered cloak (Freyja), the Trickster's Ring (Loki), sacred farming tools and extra crop growth (Freyr), Tyr's Shield, Bifrost fragments, and Gungnir fragments. They are planned for the later phases.</p>
  <p class="meta">Status: the shrines were placed in a Minecraft 1.21.4 test world with the game's template command and photographed from a client; the offering altars load, but no offering has been made in play and no advancement earned. Natural spawning in a fresh survival world is not yet confirmed.</p>
</section>"""
    return page("Shrines: seven gods, seven altars", "The seven god shrines in the Asgard mod, their altars and offerings, and what their chests hold.", body, "shrines", "shrines.html")



# ---------- creatures: stats are read from the entity classes, loot from the loot tables ----------

JAVA = REPO / "src/main/java/dev/shadw/asgard"


def entity_attrs(cls):
    src = (JAVA / f"{cls}.java").read_text()
    out = {}
    for key, name in (("MAX_HEALTH", "health"), ("ATTACK_DAMAGE", "damage"), ("ARMOR", "armour"), ("MOVEMENT_SPEED", "speed"),
                      ("KNOCKBACK_RESISTANCE", "knockback"), ("SCALE", "scale")):
        m = re.search(rf"Attributes\.{key},\s*([0-9.]+)", src)
        if m:
            out[name] = float(m.group(1))
    return out


def spawn_rules():
    src = (JAVA / "AsgardEntities.java").read_text()
    rules = {}
    for m in re.finditer(r"BiomeModifications\.addSpawn\((.*?),\s*MobCategory\.(\w+),\s*(\w+),\s*(\d+),\s*(\d+),\s*(\d+)\)", src, re.S):
        tags = re.findall(r"BiomeTags\.IS_(\w+)", m.group(1))
        rules[m.group(3)] = dict(biomes=[x.lower() for x in tags], weight=int(m.group(4)), lo=int(m.group(5)), hi=int(m.group(6)))
    return rules


def entity_loot(name):
    d = read_json(DATA / "loot_table/entities" / f"{name}.json")
    out = []
    for pool in d["pools"]:
        for e in pool["entries"]:
            label = item_label(e["name"])
            if label not in out:
                out.append(label)
    return out


CREATURES = [  # key, class, name, blurb, shot, in-structure note
    ("draugr", "Draugr", "Draugr", "An undead Norse warrior in a rusted iron helm, with a glowing blue stare. It is tougher and slower than a zombie, never burns in sunlight, and carries an iron axe or sword. It uses the zombie model with its own skin.", "creature-draugr", "Also haunts the rune circle and Tyr's shrine."),
    ("troll", "Troll", "Troll", "A hulking mountain troll, one and a half times a player's size, with stone patches, moss and tusks. It hits hard and shrugs off knockback, and in open daylight it turns to stone: it stops moving and attacking until night, or until it is under cover. It uses the zombie model, scaled up.", "creature-troll", "Also guards Tyr's shrine, rarely."),
    ("raven", "Raven", "Raven", "Odin's black bird. It flies, can be tamed with seeds, and mimics the sounds around it like a parrot. It uses the parrot model with a black skin.", "creature-raven", "Lives around Yggdrasil and Odin's shrine."),
]


def build_creatures(data, gods, manifest, names):
    rules = spawn_rules()
    cards = ""
    for key, cls, name, blurb, shot_name, where in CREATURES:
        a = entity_attrs(cls) if (JAVA / f"{cls}.java").exists() and cls != "Raven" else {}
        rule = rules.get(key.upper(), {})
        stats = ""
        if a:
            stats = (f"<tr><th scope=\"row\">Stats</th><td>{a['health']:g} health ({a['health'] / 2:g} hearts), {a['damage']:g} attack damage, {a['armour']:g} armour"
                     + (f", knockback resistance {a['knockback']:g}" if 'knockback' in a else "") + (f", {a['scale']:g} times scale" if 'scale' in a else "") + "</td></tr>")
        else:
            stats = "<tr><th scope=\"row\">Stats</th><td>The parrot's: 6 health, flies, tameable with seeds.</td></tr>"
        spawn = (f"<tr><th scope=\"row\">Spawns</th><td>{esc(', '.join(rule.get('biomes', [])))} biomes; groups of {rule.get('lo', '?')} to {rule.get('hi', '?')}, spawn weight {rule.get('weight', '?')}. {esc(where)}</td></tr>") if rule else ""
        fig = (f'<figure class="shot"><img src="{shot(shot_name)}" alt="A {esc(name)} in a flat Minecraft test world." width="854" height="480" loading="lazy"><figcaption>{esc(name)}, in a flat test world.</figcaption></figure>') if shot(shot_name) else ""
        cards += (f'<section class="struct" id="{key}"><h2>{esc(name)}</h2><p>{esc(blurb)}</p>{fig}'
                  f'<table class="data"><caption class="sr">{esc(name)}: facts</caption><tbody>{stats}{spawn}'
                  f'<tr><th scope="row">Drops</th><td>{esc(", ".join(entity_loot(key)))}</td></tr>'
                  f'<tr><th scope="row">Spawn egg</th><td>In the Spawn Eggs tab, and <code>/summon asgard:{key}</code></td></tr></tbody></table></section>')
    hero = shot("creatures")
    group = (f'<figure class="shot wide"><img src="{hero}" alt="A troll between two draugr, with two ravens, in a flat Minecraft test world." width="854" height="480"><figcaption>All three, summoned in a flat test world with their AI switched off for the photograph.</figcaption></figure>') if hero else ""
    body = f"""
<section class="page">
  <p class="eyebrow">Creatures</p>
  <h1 class="mc-h">Draugr, trolls and ravens</h1>
  <p class="lede">The first three creatures of the design's Phase 2. They reuse Minecraft's zombie and parrot models with skins painted for the mod.</p>
  {group}
  {cards}
  <h2>Not built yet</h2>
  <p>The design also lists Ratatoskr, other mythical beasts, companions and bosses. Creatures with their own models and animations need custom model code and are planned for later.</p>
  <p class="meta">Status: all three load and render in a Minecraft 1.21.4 client when summoned. Their spawn rules, drops and the troll's daylight petrification are written but not yet watched over a full day and night, and no advancement has been earned in play.</p>
</section>"""
    return page("Creatures: draugr, trolls and ravens", "The first creatures of the Asgard mod: the draugr, the troll and Odin's raven, with stats, spawns and drops.", body, "creatures", "creatures.html")


def build_install(data, gods, manifest):
    body = f"""
<section class="page">
  <p class="eyebrow">Install</p>
  <h1 class="mc-h">Install Asgard</h1>
  <p class="lede">Asgard is a Fabric mod for Minecraft {esc(', '.join(manifest['game_versions']))}. No release jar is published yet, so you build it.</p>
  <h2>You need</h2>
  <ul><li>Minecraft Java Edition {esc(manifest['game_versions'][0])} (not Bedrock)</li><li><a href="https://fabricmc.net">Fabric</a>, the mod loader: Fabric Loader 0.16 or later, and Fabric API</li><li>Java 21</li><li>Gradle 8, the build tool (the repository has no Gradle wrapper)</li></ul>
  <h2>Build</h2>
  <pre><code>git clone https://github.com/SolutionsAsService/minecraft-asgard
cd minecraft-asgard
gradle build
# the jar is in build/libs/asgard-{esc(manifest['version'])}.jar</code></pre>
  <p>Copy the jar into your <code>mods</code> folder and start the game. The server log line <code>Asgard loaded: {len(data['potions']) + 1} potions ({len(data['potions'])} from data, plus Blessing), {len(data['potions']) + 1} brewing recipes, 0 unknown effects skipped; 3 relics, {len(list((ASSETS / 'blockstates').glob('*.json')))} blocks, 3 creatures</code> confirms the registration.</p>
  <h2>Status</h2>
  <p>Builds on Fabric Loom 1.11.8 and Gradle 8. Loaded on a Fabric dedicated server for 1.21.4, and a client joined that server and showed the ingredients, potions, relics and structures (the screenshots on this site). Brewing in a stand, drinking the potions, using the relics and natural structure spawning are not yet tested.</p>
</section>"""
    return page("Install Asgard", "How to build and install the Asgard Minecraft mod.", body, "install", "install.html")


def build_developers(data, gods, manifest):
    sample = json.dumps(data["potions"][0], indent=2, ensure_ascii=False)
    body = f"""
<section class="page">
  <p class="eyebrow">Developers</p>
  <h1 class="mc-h">Add a god, or a potion</h1>
  <p class="lede">The potions are data. The mod reads <code>potions.json</code> at startup, registers one ingredient item and one potion per entry, and adds the brewing recipe from Awkward Potion. An unknown effect id is logged and skipped.</p>
  <h2>One entry</h2>
  <pre><code>{esc(sample)}</code></pre>
  <dl class="fields">
    <dt><code>id</code></dt><dd>The potion's path. The loader uses it to register the potion.</dd>
    <dt><code>ingredient</code></dt><dd>The item path of the brewing ingredient. Each ingredient is one registry entry, so it must be unique.</dd>
    <dt><code>effects</code></dt><dd>List of <code>effect</code> (a registry id such as <code>minecraft:strength</code>), <code>seconds</code>, <code>amplifier</code> (0 is level I).</dd>
    <dt><code>name</code></dt><dd>Used by <code>tools/gen_assets.py</code> for the language file: the potion shows as "Potion of &lt;name&gt;" (and "Splash &lt;name&gt;", "Lingering &lt;name&gt;").</dd>
    <dt><code>lore</code></dt><dd>One line for the ingredient's tooltip (also written by the generator).</dd>
    <dt><code>hue</code></dt><dd>Optional. The ingredient sprite's colour. Without it the sprite takes the realm's colour.</dd>
    <dt><code>realm</code></dt><dd>A realm id from the <code>realms</code> list. The generator uses it for the default sprite colour.</dd>
    <dt><code>god</code>, <code>epithet</code>, <code>domain</code></dt><dd>Optional. Used by this site; the mod ignores them.</dd>
  </dl>
  <h2>Regenerate and build</h2>
  <pre><code>python3 tools/gen_assets.py      # language file, item models, item definitions, sprites
gradle build
python3 _src/build_site.py       # this site</code></pre>
  <p>The loader and the data format are shared with the other Nordic Pantheon mods, built with the <a href="https://github.com/SolutionsAsService/shadw-modding">shadw-modding</a> stack.</p>
</section>"""
    return page("Developers: add a god or a potion", "The data format behind the Asgard mod, and how to add a potion.", body, "developers", "developers.html")


def copy_items(gods):
    global _ALL_POTIONS
    import shutil
    out = SITE / "img/items"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    for g in gods + _MORE:
        shutil.copyfile(ASSETS / "textures/item" / f"{g['ingredient']}.png", out / f"{g['ingredient']}.png")


def write(rel, text):
    path = SITE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    data, manifest, gods = load()
    palette = check_palette()
    names = effect_names()
    SITE.mkdir(exist_ok=True)
    copy_items(gods)
    copy_content_items()
    write("index.html", build_index(data, gods, palette, names))
    write("gods.html", build_gods(data, gods, palette, names))
    for i, g in enumerate(gods):
        write(f"gods/{g['slug']}.html", build_god(i, g, gods, palette, names))
    write("relics.html", build_relics(data, gods, manifest))
    write("structures.html", build_structures(data, gods, manifest))
    write("shrines.html", build_shrines(data, gods, manifest, names))
    write("creatures.html", build_creatures(data, gods, manifest, names))
    write("install.html", build_install(data, gods, manifest))
    write("developers.html", build_developers(data, gods, manifest))
    pages = len(list(SITE.rglob("*.html")))
    shots = sorted(p.stem for p in (SITE / "img/shots").glob("*.png")) if (SITE / "img/shots").exists() else []
    print(f"site written: {pages} pages; palette ΔE {palette['min_delta_e']} ({palette['min_pair']}); "
          f"min hue contrast {palette['min_contrast_hue_on_card']}; god text on tint {palette['min_text_hue_on_tint']}; "
          f"screenshots: {', '.join(shots) or 'none'}")


if __name__ == "__main__":
    main()
