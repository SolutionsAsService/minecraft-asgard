# DESIGN-LOG: the Asgard site (DADA run)

Status: **INCOMPLETE.** Rounds A1 (8 seats) and A2 (8 seats) were run and resolved. Round A3 was started with the four
seats that objected in A2; two filed (Shklovsky, Johnson), one never reported (Mace: the agent died on a rate limit),
and one was never launched (Bringhurst, after the limit). S2 and S3 are not met. Resume point at the end.

## 1. Traversal Plan

**Brief, restated (owner's words):** "the Asgard site needs work like a good Asgard plus Minecraft theme redo this, show
screenshot, pantheon vibe." A deployable site for the Asgard mod (the six gods as potions), in its own repository.

**Mode: Adaptive.** It serves Minecraft players and mod developers, a public audience.
**Run type: Full.** A new site. R0 was **not** a panel round: the inherited artifact was the plain Asgard page inside
the shadw-modding site (a table, no theme), which I judged myself from a screenshot.
**Design pack:** none adopted; the packs carry their own palettes and would override the topic palette below.

**Tooling inventory.** Used: `scripts/pick_panel.py`; sub-agents for the panel (one per seat, three at a time);
Playwright Chromium for measurement and rendering; Xvfb with a real Minecraft 1.21.4 client joined to a Fabric
dedicated server for the screenshots; RCON to build the test scene; `javap` on the game's jars to read the dye colours.
No graph renderer. `import_log.py` and `rate_seats.py` were **not run**.

**Seed (labels copied from `references/anchor-graph.md`):**
- Stance: "Steal Like an Artist (Austin Kleon)" (borrow Minecraft's own interface vocabulary)
- Rules: "Interaction of Color (Josef Albers)"; "Visual Hierarchy (Arnheim, Dondis)"
- Breaker: "The Medium Is the Massage (Marshall McLuhan, Quentin Fiore)" (the game is the message)
- Counterpoint (dotted edge from Albers, "experiential counterpoint to"): "The Art of Color (Johannes Itten)"

**Panel (from `pick_panel.py --mode adaptive --run-type full --project minecraft-asgard`):** Debord, Shklovsky, Holmes,
Mace, Cairo, Krug, Bringhurst, and Johnson (the rotation seat). Dotted pairs: Debord -.- Krug, Shklovsky -.- Krug.

**Palette (Decision Record).** Source: Minecraft's dye colours, read from `net.minecraft.world.item.DyeColor` in the
1.21.4 jar (all 16 hexes extracted with `javap`). The Bifrost in the screenshots is stained glass in these colours.
One hue per god, from the lore: Thor light blue, Frigg white, Heimdall orange, Odin magenta, Freyja pink, Loki lime;
yellow reserved for the action. Chosen by search: of the 9 dyes that reach 3:1 on the card ground, this set has the
largest minimum difference. **Measured at build (gated):** smallest CIE76 difference ΔE 44.1 (Odin / Freyja); smallest
god-hue contrast on the card ground 3.54:1; smallest hue used as TEXT on a god page's tinted ground 4.76:1 (a mixed-
toward-white text hue; the raw Odin hue was 3.87:1). Dark only. The light-mode check was not run.

**Frontier**

| Candidate | Status |
|---|---|
| The real in-game hall as the hero, the pillars as links (M1, BREAK) | TAKEN |
| Pixel-art emblems and recipe figure drawn in code (M2) | TAKEN |
| Palette from the game's dye colours (M3) | TAKEN |
| Photo-led gods index; alternating god-page composition (M4, after A1/A2) | TAKEN |
| Break the uniform grid on the gods index; vary crop and pitch per god (Shklovsky A2/A3 F1) | DEFERRED (needs new per-god camera angles) |
| Let a god page change its section order, not only the photo position (Shklovsky A3 F2) | DEFERRED |
| Light theme | DEFERRED (owner decision) |
| A pixel display face (Bringhurst) | DEFERRED (no font file available offline) |
| A real brew and a real drink captured in the game (Debord) | DEFERRED (needs input automation or a game test) |
| Mace re-check of the A2 fixes; Bringhurst re-check | OPEN (seats did not report; resume) |

## 2. Decision Records

### M1: the real hall as the hero, the pillars as links (BREAK)
Anchors: Stance Kleon | Rule Visual Hierarchy | Breaker McLuhan | Counterpoint Itten (the colour is read in the real
photograph, not drawn). Intent: the first screen is the subject itself, a Minecraft scene built from stained glass, with
six chips (emblem, god, effect) as the navigation. Alternatives rejected: a vector colonnade over a darkened photo (round
A1: it doubled the arc, hid the strong image, and was a costume); a card grid. Consequence: the hero is a staged test
world, so the image carries a visible caption ("built with server commands, not part of the mod; the labels are the
site's"). Fence: the hero stays unretouched (no scrim), so the chips are opaque.
Measured: hall bottom edge y=778 of 800 at 1280x800; chips inside the image, gaps 15-30px.

### M2: pixel emblems and bottles drawn in code
Hammer, distaff, horn, eye, necklace, serpent as 16x16 SVG; a potion bottle for the recipe. Honest labelling: the page
says the bottles are illustrations and the bottle colour is a design choice.

### M3: palette from the game
See section 1.

### M4: photo-led index, alternating compositions
Answers Shklovsky A1 F4/A2 F1-F2 in part; judged inadequate in A3 (F1, F2).

## 3. A bug this run found (in the mod, not the site)

The first in-game capture showed every ingredient as the purple-and-black **missing model**, in the item frames, the
hotbar and the hand. Cause: Minecraft 1.21.4 draws an item from `assets/<ns>/items/<id>.json`; the mod shipped models
only. The generator now writes the definitions, and the second capture shows the ingredients correctly. The same fix was
applied to every mod in the shadw-modding stack (template, examples, Pantheon Potions).

## 4. Panel Reports and resolutions

### Round A1 (WHOLE, 8 seats; evidence `panel-A1/EVIDENCE.md`): all 8 OBJECT

| Seat | Principal objections |
|---|---|
| Debord | hero illustration over a darkened capture undisclosed; "brewed from its own ingredient" unqualified; no real brew shown; epithets unlabelled |
| Krug | a god on the first screen was name only; pillars did not look clickable; Install looked disabled; stat row filler |
| Cairo | text hue under 4.5:1 on a god page (Odin 3.87); hotbar caption; developer-page fields; Gradle note |
| Shklovsky | hero costume not device; real hall buried; gods index a table |
| Holmes | SVG link names; alt text duplicated the caption; jargon; dark only |
| Mace | skip link did not move focus; pillar ring hard-coded; ring lost on the rainbow's yellow |
| Johnson | faint photo doubled the vector arc; cap colours tied to arc bands; yellow not reserved; emblems weak on white |
| Bringhurst | measure, apostrophes, runts, figures, scale |

#### Resolutions, round A1

| Finding | Resolution |
|---|---|
| Shklovsky F1-F3 + Debord F1 + Johnson F2-F3 + Krug F1-F2: hero | ADAPT (M1: the real capture as the hero, pillars as chip links, vector arc removed, disclosure on the image) |
| Krug F6 + Shklovsky F1: stat row | ADAPT (removed) |
| Krug F4: Install looked disabled | ADAPT (white button; third button "For developers") |
| Debord F2: unqualified brewing claim | ADAPT (wording and a note beside the tagline) |
| Debord F3: no real brew captured | DEFERRED (needs input automation) |
| Debord F4: epithets unlabelled | ADAPT (flavour-text note on gods and god pages) |
| Cairo F3: text hue 3.87:1 | ADAPT (text hue mixed toward white; build gate at 4.5:1; minimum now 4.76) |
| Cairo F7, F9, F10, F11 | ADAPT (caption, bottle note, developer fields, Gradle and Bedrock notes) |
| Holmes F1, F2, F3, F5 | ADAPT (HTML chip links, short alt text, sign text in captions, glosses) |
| Holmes F6: light theme | DEFERRED |
| Mace F1-F3 | ADAPT (`tabindex="-1"` on main; chip focus rings; forced-colors rule) |
| Johnson F4: yellow not reserved | ADAPT (eyebrow muted, brand mark white) |
| Bringhurst F1-F4, F7, F8 | ADAPT (measure, apostrophes, tabular figures, case, scale) |
| Bringhurst F5-F6: display face | DEFERRED |

### Round A2 (WHOLE, 8 seats; evidence `panel-A2/EVIDENCE.md`): Debord, Krug, Cairo, Holmes PASS; Shklovsky, Mace, Johnson, Bringhurst OBJECT

#### Resolutions, round A2

| Finding | Resolution |
|---|---|
| Shklovsky F3 + Krug F4: hall shown twice | ADAPT (once, in the hero; "In the game" shows two close-ups) |
| Shklovsky F1: gods index a card grid | PARTLY ADAPT (photo-led entries); judged inadequate again in A3 |
| Shklovsky F2: one template with the hue swapped | PARTLY ADAPT (two compositions by parity); judged inadequate in A3 |
| Mace F1: focus halo covered neighbouring chips (gaps 4-10px) | ADAPT (chips capped at 92px; gaps now 15-30px; smaller shadow) |
| Mace F2: forced-colors ring had one edge | ADAPT (real border plus Highlight outline) |
| Johnson F2: chips the lowest, smallest element | PARTLY ADAPT (bigger type, lifted, bevelled); OVERRULE the scrim: the hero stays unretouched (judged defensible in A3) |
| Johnson F4: 2px frames | ADAPT (3px) |
| Bringhurst F1: measure 75-83 characters | ADAPT (34em) |
| Bringhurst F2: straight apostrophes | ADAPT (the pass now covers raw and escaped apostrophes; none remain in prose) |
| Bringhurst F3: footer runt | ADAPT (46em, balanced, bound words) |
| Bringhurst F4: shadow on small caps | ADAPT (brand lost its shadow; headings 30px and up keep it) |
| Bringhurst F5: two voices | DEFERRED |
| Krug F1, F3; Holmes F1-F2; Debord F2-F3 | ADAPT (phone tiles show the effect; "For developers"; glosses; chip text 13px in lighter ink; labels-are-the-site's caption; recipe caveat) |

### Round A3 (partial): Shklovsky OBJECT, Johnson OBJECT (phone only), Mace NOT REPORTED, Bringhurst NOT LAUNCHED

Reports filed: `panel-A3/crit_prov_shklovsky.md`, `panel-A3/crit_perc_johnson.md`. The Mace agent died on a rate limit with
no file; Bringhurst was not launched. Neither verdict is reconstructed.

#### Resolutions, round A3

| Finding | Resolution |
|---|---|
| Johnson F4: phone tiles split words ("Regeneratio / n II") | ADAPT (smaller tile emblem; break only between words). Measured after: every tile's longest word fits its box; applied, not re-judged |
| Johnson F5: the no-scrim overrule | Judged defensible by the seat |
| Johnson F3: Odin and Freyja frames close at a glance | DEFERRED (identity rests on the name; optional distinct frame shape) |
| Shklovsky F1: gods index is still uniform cards | DEFERRED (Frontier) |
| Shklovsky F2: god pages vary by parity only | DEFERRED (Frontier) |
| Shklovsky F3: hall shown once | Resolved |

## 5. Anchor Ledger

| Anchor | Role | Status | Evidence |
|---|---|---|---|
| Steal Like an Artist (Austin Kleon) | Stance | KEEP | the site borrows the game's interface and the game's own scene; survived "costume" (Shklovsky A1) by moving the game scene to the hero |
| Interaction of Color (Josef Albers) | Rule | ADAPT | the text-hue gate (Cairo A1 F3) and the dye-colour palette |
| Visual Hierarchy (Arnheim, Dondis) | Rule | KEEP | first-glance order confirmed by Krug and Johnson (A2) |
| The Medium Is the Massage (McLuhan, Fiore) | Breaker | KEEP | the real hall as the hero; the pushed move (S4) |
| The Art of Color (Johannes Itten) | Counterpoint (dotted) | applied | colour read in the real photograph (chips carry the god hue as frames) |

## 6. Measured state (final)

Chromium, all 10 pages at 1280x800 and 375x812 (20 page-viewports): no sideways scroll; no link or button under 44px
high; no text under 12px. Home desktop: hall image bottom edge y=778 of 800. Home phone: tiles end y=672, last button
y=796 of 812. Chips: inside the image, none overlapping, gaps 15-30px. No straight apostrophes outside code blocks.
Palette gates as in section 1. The build fails if any gate breaks.

## 7. Stop test

- **S1.** Frontier: DEFERRED items have reasons; "Mace and Bringhurst re-check" is OPEN. Not met.
- **S2.** A WHOLE round with PASS from every required critic. Not met (A2: 4 of 8 PASS; A3 partial).
- **S3.** Two consecutive quiet WHOLE rounds. Not met.
- **S4.** Ambition push, measured. Met: the hero moved from a vector colonnade over a darkened photo (hall figure bottom
  y=715, two arcs visible) to the unretouched capture with link chips (bottom y=778; one arc); the chips' effect labels
  were then cut to the effect name so they stop wrapping (heights uniform at 90px).
- **S5.** Dotted edges: Itten applied; McLuhan -.-> Carson declined (the site does not imitate Carson's layouts).

**Result: incomplete.** Resume: re-seat Mace and Bringhurst on the current state, re-judge the phone-tile fix, and take
Shklovsky's gods-index and god-page composition findings or decline them with a reason; then two quiet WHOLE rounds.

## 8. Double loop

The criterion and the panel held. The graph failed once: the seed's Breaker (McLuhan) pointed at "the medium is the
message", and the first design (a vector colonnade) honoured the words and missed the medium: only the real game scene
is the medium. Graph amendment: when the subject is a game, add a required move that puts a real capture of the game on
the first screen before any drawn figure. The strongest single finding of the run was not a critic's: it was the
purple-and-black item in the first capture, which no panel could have seen from the code.

## 9. Compliance Check

- [x] Tooling inventory (section 1)
- [x] Mode stated with the reason
- [x] Panel from `pick_panel.py`; seats briefed from their files; the rate-limit loss stated
- [x] Seed with exact labels and a dotted-edge counterpoint; living Frontier
- [x] Run type stated (Full); R0 not a panel round, said so
- [x] Mobile Floor measured at the final state (`check_floor.py` NOT run; Playwright measurements instead)
- [x] Shadw- and Vercel-configured: root and inner `vercel.json`, `fluid.json` with the `/` static route, root redirect, root-anchored `.vercelignore`, absolute `og:image` on `https://minecraft-asgard.shadw.app`. The build script does not check these; checked by hand. Not deployed.
- [x] Palette derived from the topic (the game's dye colours), one hue per god, ΔE and contrast measured and gated; light mode not checked
- [x] Landing leads with one bold graphic that summarises every topic (the six gods), complete in the first viewport at both sizes
- [x] At least one BREAK move taken (M1)
- [x] Decision Records before moves (M1-M3; M4 recorded after A2)
- [x] Panel Reports per round
- [x] Every OBJECT resolved (ADAPT, OVERRULE, DEFERRED with reason)
- [ ] WHOLE rounds run to the stop conditions: A1 and A2 run; A3 partial; S1-S3 not met
- [x] Figures re-measured at the final state (section 6)
- [x] Anchor Ledger; Double-loop paragraph
- [ ] Run recorded in the ledger (`import_log.py`, `rate_seats.py` not run; the dada repository is not at hand for this)
- [x] Final reply states the mode, the tools, the stop conditions and what was skipped

**Skipped:** the R0 panel; `check_floor.py`; the light-mode contrast check; the A3 reports of Mace and Bringhurst; the
ledger import. No grade was given, so none is recorded.


## Run 2: Extend (Norse content, relics and structures)

**Brief:** Yggdrasil and the other Norse structures belong in Asgard, not only the potions; Thor's hammer should spawn
in the game; expand the mod and the site. Mode: Adaptive. Run type: Extend (new pages in the existing system; the
palette, type and hall are unchanged).

**Moves**
- X1: Relics page: one card per item with its real sprite, numbers read from `content.json`, loot chances computed from
  the loot tables (Mjölnir 2 in 5 shrine chests). Damage stated as the stored modifier and the total with the base 1.
- X2: Structures page: real in-game captures, facts read from the NBT header, structure set and biome tags.
- X3: Home: tagline widened to the whole mod; a second gallery band with Yggdrasil and the shrine.

**Found by looking at the captures (not by a panel):** the Yggdrasil trunk rendered black under a solid canopy
(light), and the bark was too dark. Fixed in the structure (sun shafts, hanging lanterns) and the texture; retaken.

**Not done, stated plainly:** no critic panel was run on these pages; item use, brewing and natural structure
spawning are untested; the `/locate` check failed for the structures and for a vanilla village alike, so it proved
nothing; the captures use a flat test world and `/place template` for framing; light mode and the pixel font stay
deferred. Layout measured with Playwright at 1280 by 800 and 375 by 812: no horizontal scroll on the three pages.


## Run 3: Extend (every creature gets its own model; four more creatures)

**Brief:** give the Draugr, Troll and Raven the same model treatment as the Olympia and Khemet creatures, and add more creatures from the
design list, a big wolf for sure. Mode: Adaptive. Run type: Extend (the site's system is unchanged; the Creatures page grows).

**Moves**
- X1: the three existing creatures were rebuilt on the shared model system (`tools/gen_models.py`): the draugr (iron cap, nose guard, braided beard,
  mail, shield, sword), the troll (stooped, long arms, tusks, stone and moss, club) and the raven (a model-only "external" creature: its hand-written
  parrot class stays, the generator writes only its model, texture, egg, loot and language).
- X2: four new creatures: Draugr Lord, Jötunn (frost giant), Warg (a big wolf) and Fenrir (the boss wolf), the last two on a new quadruped builder
  (`Rig.quadruped`) in the shared figure kit.
- X3: the Creatures page is read from `mobs/*.json`; the pictures are composed from the six-angle photographs (`tools/creature_shots.py`).

**Found by looking at the photographs, not by a panel:** the first wolf stood on stilts with its head high (leg and neck angles), the sword and club hung
toward the ground (the held-item rotation was added to the arm's instead of opposing it), and the first raven fold hung its wings straight down like legs.
Each was fixed and photographed again.

**Not done, stated plainly:** no critic panel was run; the animation was checked in still photographs only (the raven's flight beat was not photographed);
nothing was hand-played; each mobtest is a single run (a first batch gave empty reach times for the warg and the draugr lord that a repeat did not, so
the table uses the repeats); natural spawning, the troll's daylight rule over a full day, and the advancements were not watched.


## Run 4: Polish (2.0: faces and the raven's beak)

**Brief:** clean up the rough details, faces looking off; the models are mostly A minus; the raven's beak is a B. Mode: Adaptive. Run type: Polish (the
creatures, their behaviour and the page system are frozen; only model details change).

**Found by the face close-ups:** the frost giant's brow box lay in the same plane as its face and hid the eyes, nose and mouth (a blank mask); the draugr cap
covered its eye rows (a visor with no eyes); the troll's mouth read as a smile because its tusks ran across it; the wolves' eye pixels were on the wrong rows;
the raven's beak was a straight duck-bill block. The face cameras for wolves and the raven pointed at the belly or the sky (head position is now a parameter).
**Fixed:** a `face()` helper in the shared kit lays out brow, eyes with a pupil, nose, nostrils, cheek hollows, mouth and teeth on the front of a head box; the
raven has a deep tapering beak with a ridge, a hooked tip, a finer lower half, nostril bristles and eyes on the side of the head.

**Not done:** animation still checked in stills only; one pass; no panel.
