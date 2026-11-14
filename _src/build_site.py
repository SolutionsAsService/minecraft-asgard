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


def load():
    data = read_json(ASSETS / "potions.json")
    manifest = read_json(REPO / "shadw.mod.json")
    gods = []
    for p in data["potions"]:
        gods.append({**p, "slug": p["god"].lower(), "dye": GOD_DYE[p["god"]], "hue": DYE[GOD_DYE[p["god"]]]})
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

NAV = [("index.html", "Home", "home"), ("gods.html", "Gods", "gods"), ("install.html", "Install", "install"),
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
    body = f"""
<section class="hero" aria-labelledby="h1">
  <div class="hero-inner">
    <div class="hero-title"><p class="eyebrow">Minecraft mod · Nordic Pantheon</p><h1 id="h1" class="mc">ASGARD</h1></div>
    <div class="hero-tag"><p class="tag">The six gods as potions. Each has its own ingredient and brewing recipe.</p>
    <p class="meta">The recipes are registered in code; brewing in a world is not yet tested.</p></div>
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
"""
    return page("Asgard: the six gods as Minecraft potions", "A Minecraft mod: Thor, Frigg, Heimdall, Odin, Freyja and Loki as potions, each with its own ingredient.", body, "home", "index.html")


def build_gods(data, gods, palette, names):
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
  <p>Copy the jar into your <code>mods</code> folder and start the game. The server log line <code>Asgard loaded: {len(gods)} potions, {len(gods)} brewing recipes, 0 unknown effects skipped</code> confirms the registration.</p>
  <h2>Status</h2>
  <p>Builds on Fabric Loom 1.11.8 and Gradle 8. Loaded on a Fabric dedicated server for 1.21.4, and a client joined that server and showed the ingredients and potions (the screenshots on the home page). Brewing in a stand and drinking the potions are not yet tested.</p>
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
    import shutil
    out = SITE / "img/items"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    for g in gods:
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
    write("index.html", build_index(data, gods, palette, names))
    write("gods.html", build_gods(data, gods, palette, names))
    for i, g in enumerate(gods):
        write(f"gods/{g['slug']}.html", build_god(i, g, gods, palette, names))
    write("install.html", build_install(data, gods, manifest))
    write("developers.html", build_developers(data, gods, manifest))
    pages = len(list(SITE.rglob("*.html")))
    shots = sorted(p.stem for p in (SITE / "img/shots").glob("*.png")) if (SITE / "img/shots").exists() else []
    print(f"site written: {pages} pages; palette ΔE {palette['min_delta_e']} ({palette['min_pair']}); "
          f"min hue contrast {palette['min_contrast_hue_on_card']}; god text on tint {palette['min_text_hue_on_tint']}; "
          f"screenshots: {', '.join(shots) or 'none'}")


if __name__ == "__main__":
    main()
