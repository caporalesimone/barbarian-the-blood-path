"""Names and descriptions of every tile and every glyph for the graphics atlas (tools/atlas/gen_atlas.py, 10/11; English
since 11/11).

Rule of the owner (10/11): in the atlas every tile and every glyph has its name and its description. Whoever adds a
tile (tools/build/gen_gfx.py: TILES, TOWN_TILES, TRONO_NAMES), a glyph of the UI font (tools/build/gen_font.py, constant CH_* in
src/game/ui.asm) or a HUD glyph (HUD_A/HUD_B/HUD_WARN in tools/build/gen_gfx.py) adds its entry here: without it gen_atlas.py
stops with an error (the build fails)."""

# ------------------------------------------------------------------ tiles: internal name -> (name, description)
TILE = {
    # dungeon (files GFX1/GFX2, slots 0..26)
    "WALL": ("wall", "dungeon wall seen from above (solid)"),
    # (18/11, TODO M11) grotte (capitolo 3, tools/build/cave_gfx.py): stessi posti, roccia al posto dei mattoni
    "CAVE:WALL": ("rock", "cave rock seen from above (solid); snow flecks on level 11 (palette 9)"),
    "CAVE:WALLFACE": ("rock face", "rock face above a floor: snowy (palette 9) or pale crest, strata, shade at the bottom"),
    "CAVE:FLOOR": ("cave floor", "dark earth with gravel"),
    "CAVE:FLOORB": ("cave floor, stone", "cave floor with a stone (random variant set by post_walls, 1/8)"),
    "CAVE:FLOORC": ("cave floor, pebbles", "cave floor with pebbles (random variant set by post_walls, 1/8)"),
    "WALLFACE": ("wall face", "wall with its face showing: post_walls puts it above a floor"),
    "FLOOR": ("floor", "dungeon floor"),
    "FLOORB": ("floor B", "cracked floor (random variant set by post_walls, 1/8)"),
    "FLOORC": ("floor C", "floor with stones (random variant set by post_walls, 1/8)"),
    "STAIRSD": ("stairs down", "down to the next level"),
    "STAIRSU": ("stairs up", "up to the previous level (from level 1: to the village)"),
    "DHOME": ("inn door", "door of the inn (fire: the chest, module OVLT); in the throne room the slot holds the lever"),
    "FREE8": ("free 8", "free slot in the dungeons (06/11: items on the floor removed); in the village it holds a gravestone"),
    "FREE9": ("free 9", "free slot in the dungeons; in the village it holds the stone cross"),
    "FREE10": ("free 10", "free slot in the dungeons; in the village it holds the left side of the crypt"),
    "FREE11": ("free 11", "free slot in the dungeons; in the village it holds the right side of the crypt"),
    "GRASSA": ("grass A", "grass with a few blades (the most common)"),
    "GRASSB": ("grass B", "grass with tufts"),
    "PATH": ("path", "dirt path (minimap: road)"),
    "BWALL": ("house wall", "brick wall of the houses (solid)"),
    "BROOF": ("roof A", "roof with horizontal stripes (solid)"),
    "DSMITH": ("smith door", "door of the smith (fire: shop, shop_id 0)"),
    "DALCH": ("alchemist door", "door of the alchemist (fire: shop, shop_id 1)"),
    "SIGNL": ("alchemist sign", "sign with the flask above the alchemist's door (09/11: in the slot left by the armorer)"),
    "FOUNTAIN": ("fountain rim", "rim of the basin: walking on it restores full hp"),
    "PORTAL": ("portal", "stone arch with the glowing oval: shown when the portal is open (village) and in the dungeons"),
    "TREE": ("tree", "tree (map border, groves; solid)"),
    "TSTAIRS": ("crypt door", "entrance of the dungeon: down to level 1"),
    "CHEST": ("chest", "dungeon chest, one tile for every type (10/11): normal, key, golden, epic; the type is in ch_t and "
                       "the top bar says it (chest, locked chest, golden chest, epic chest)"),
    "FREE25": ("free 25", "free slot in the dungeons (10/11: it was the locked chest, removed); in the village it holds the crypt gable"),
    "FREE26": ("free 26", "free slot in the dungeons (10/11: it was the golden chest, removed); in the village it holds the right roof of the crypt"),
    "COBBLE": ("cobblestones", "stone paving of the square and of the portal square"),
    "FOUNT0": ("fountain top-left", "2x2 fountain, top-left quarter (solid)"),
    "FOUNT1": ("fountain top-right", "2x2 fountain, top-right quarter (solid)"),
    "FOUNT2": ("fountain bottom-left", "2x2 fountain, bottom-left quarter (solid)"),
    "FOUNT3": ("fountain bottom-right", "2x2 fountain, bottom-right quarter (solid)"),
    "FLOWERS": ("flowers", "flowered meadow (walkable); in the throne room it is the base of the pentacle lines"),
    "WINDOW": ("window", "window in a brick wall: frame, panes, bar, sill (10/11, instead of the barrel)"),
    "WELL": ("well", "well with its little roof (solid)"),
    "FENCE": ("fence", "horizontal fence with posts (solid)"),
    "LAMP": ("street lamp", "street lamp on the cobblestones (solid)"),
    "BUSH": ("bush", "bush with berries (solid)"),
    "STALL": ("market stall", "market stall of the square with the striped awning (solid)"),
    "BROOFA": ("roof B", "roof with scaled tiles (solid)"),
    "BROOFL": ("roof C", "roof with diagonal stripes (solid)"),
    "SIGNS": ("smith sign", "sign with the anvil above the smith's door"),
    "CHIMNEY": ("chimney", "brick chimney with smoke, on any roof (10/11, instead of the hay)"),
    "FENCEV": ("vertical fence", "vertical single-line fence with two posts (10/11: sides of the graveyard and the gardens)"),
    "SPIRE": ("spire", "spire with the cross above the bell tower and the church turret (10/11)"),
    # village only (file GFX0: slots that in the dungeon are walls, floors, stairs, free, chests)
    "GRASSC": ("grass C", "grass with a stone and a tuft"),
    "BRIDGE": ("bridge", "planks of the wooden bridge over the stream"),
    "DIRT": ("packed earth", "earth of the graveyard and of the vegetable garden, in front of the gravestones (minimap: road)"),
    "HDOOR": ("closed door", "door of a house that cannot be entered (solid)"),
    "WATER": ("water", "water of the stream and of the pond (solid)"),
    "WATERL": ("left bank", "grass, then water (solid)"),
    "WATERR": ("right bank", "water, then grass (solid)"),
    "GRAVE": ("gravestone", "rounded gravestone (solid)"),
    "GRAVE2": ("stone cross", "stone cross on a grave (solid)"),
    "CRYPTL": ("crypt, left side", "stone blocks with a slit (solid)"),
    "CRYPTR": ("crypt, right side", "stone blocks with a slit (solid)"),
    "CRYPTA": ("crypt, left roof", "left slope of the stone roof of the crypt (solid)"),
    "CRYPTB": ("crypt, gable", "front of the crypt with the skull on the arch (solid)"),
    "CRYPTC": ("crypt, right roof", "right slope of the stone roof of the crypt (solid)"),
    # throne room (file GFX2)
    "LEVER": ("lever", "suspicious lever of the throne room (plate, rod, knob): opens the portal to The Endless Abyss"),
    "BLACKP": ("black portal", "black portal of the throne room (T_BPORTAL, free slot 8): replaces the lever when it is pulled and leads to The Endless Abyss; dark red stone with a pink rim, black oval (the screen shares one palette, so it is black on black with a red swirl)"),
    "STAR": ("pentacle star", "lines of the star around the final boss"),
    "CIRCLE": ("pentacle circle", "circle of the pentacle around the final boss"),
}

# ------------------------------------------------------------------ UI font (out/work/gfx/uifont.bin, 128 screen codes)
# codes 0..63: normal glyphs; 64..127: the inverted versions (ui_putc with inv = $40), but for the redrawn icons.
SCREEN = "@abcdefghijklmnopqrstuvwxyz[£]↑← !\"#$%&'()*+,-./0123456789:;<=>?"
# code -> (name, constant or key, description)
UI = {
    0: ("frame bottom-right", "BOX_BR", "bottom-right corner of the boxes (ui_box); instead of @"),
    28: ("frame horizontal", "BOX_H", "horizontal side of the boxes (the box title goes on it); instead of £"),
    30: ("frame vertical", "BOX_V", "vertical side of the boxes; instead of ↑"),
    31: ("frame top-left", "BOX_TL", "top-left corner of the boxes; instead of ←"),
    59: ("frame top-right", "BOX_TR", "top-right corner of the boxes; instead of ;"),
    60: ("frame bottom-left", "BOX_BL", "bottom-left corner of the boxes; instead of <"),
    34: ("hammer", "CH_ANVIL", "icon of the smith: shop title (yellow) and minimap (white); instead of \""),
    35: ("shield", "CH_SHLD", "icon of the shield category (brown) in equipped, inventory, chest, shop; instead of #"),
    36: ("flask", "CH_FLASK", "icon of the alchemist: shop title and minimap (yellow); instead of $"),
    91: ("key", "CH_KEY", "keys next to the gold (purse) and in the item box"),
    92: ("coin", "CH_COIN", "gold: values and prices (\"600o\"), title of the golden chest (08/11: a coin with an engraved C)"),
    93: ("arrow", "CH_ARROW", "right arrow: C screen, current value -> value with the pending points (15/11; free since 08/11)"),
    94: ("potion", "CH_POT", "potions in the belt and in the shops, in the colour of the potion (red, yellow, violet)"),
    95: ("scroll", "CH_SCR", "portal scrolls (s N) and icon of the category"),
    97: ("sword", "CH_SWORD", "icon of the weapon category (equipped, inventory, chest, shop) and title of the barbarian menu"),
    98: ("armor", "CH_ARMOR", "icon of the armor category"),
    99: ("ring", "CH_RING", "icon of the ring category (yellow)"),
    100: ("skull", "CH_SKULL", "title of the death screen (09/11)"),
    101: ("tankard", "CH_INN", "inn: title \"inn\" (yellow) and icon on the minimap (light green) (09/11)"),
    124: ("bar 1/3", "$7c", "progress bar: one third full (bar_glyph, io_screen)"),
    125: ("bar 2/3", "$7d", "progress bar: two thirds full (bar_glyph)"),
    126: ("bar full", "$7e", "progress bar: full character (bar_glyph)"),
}
PUNCT = {" ": "space", "!": "exclamation mark", "\"": "quotes", "#": "hash", "$": "dollar", "%": "percent",
         "&": "ampersand", "'": "apostrophe", "(": "open parenthesis", ")": "close parenthesis", "*": "asterisk", "+": "plus",
         ",": "comma", "-": "dash", ".": "full stop", "/": "slash", ":": "colon", ";": "semicolon", "<": "less than",
         "=": "equals", ">": "greater than", "?": "question mark", "@": "at", "[": "open bracket",
         "£": "pound", "]": "close bracket", "↑": "up arrow", "←": "left arrow"}
RELIQUIA = set("abcdefghijklmnopqrstuvwxyz0123456789 !',-./:?")


def ui_glyphs():
    """the 128 codes of the UI font: list of dict(c, name, key, desc, kind)"""
    out = []
    for c in range(128):
        base, inv = c & 63, c >= 64
        ch = SCREEN[base]
        if c in UI:
            n, k, d = UI[c]
            kind = "icon" if k.startswith("CH_") else ("box" if k.startswith("BOX_") else ("bar" if k.startswith("$") else "free"))
            out.append(dict(c=c, name=n, key=k, desc=d, kind=kind))
            continue
        if base in UI and UI[base][1].startswith(("BOX_", "CH_")):
            n = "inverse of %s" % UI[base][0]
        elif ch.isalpha() and ch.isascii():
            n = "letter %s" % ch.upper()
        elif ch.isdigit():
            n = "digit %s" % ch
        else:
            n = PUNCT[ch]
        src = "font Reliquia 05 cero" if ch in RELIQUIA else "C64 ROM"
        if inv:
            out.append(dict(c=c, name="%s (inverse)" % n, key="%s + inv ($40)" % (ch if ch != " " else "space"),
                            desc="inverted version (ui_putc with inv = $40: selected entries); %s" % src, kind="inv"))
        else:
            out.append(dict(c=c, name=n, key=("space" if ch == " " else ch),
                            desc="text character (.enc \"screen\": written with the key/character shown); %s" % src,
                            kind="text"))
    return out


# ------------------------------------------------------------------ HUD and minimap glyphs (game charset)
HUD = {
    "SLASH": ("slash", "/", "separator in the HUD numbers (hp 25/25, xp)"),
    "BLANK": ("blank", "space", "blank character of the HUD"),
    "BAR0": ("bar 0/8", "G_BAR0", "hp or experience bar: empty character"),
    "BAR1": ("bar 1/8", "G_BAR1", "bar: 1 eighth full"), "BAR2": ("bar 2/8", "G_BAR2", "bar: 2 eighths full"),
    "BAR3": ("bar 3/8", "G_BAR3", "bar: 3 eighths full"), "BAR4": ("bar 4/8", "G_BAR4", "bar: 4 eighths full"),
    "BAR5": ("bar 5/8", "G_BAR5", "bar: 5 eighths full"), "BAR6": ("bar 6/8", "G_BAR6", "bar: 6 eighths full"),
    "BAR7": ("bar 7/8", "G_BAR7", "bar: 7 eighths full"), "BAR8": ("bar full", "G_BAR8", "bar: full character"),
    "POT": ("potion", "G_POT", "potion in the HUD belt (keys 1-4)"),
    "SCR": ("scroll", "G_SCR", "portal scrolls in the HUD (key 5)"),
    "DOT": ("dash", "G_DOT", "empty belt slot in the HUD"),
    "RULE": ("rule", "G_RULE", "line between the HUD and the map"),
    "KEY": ("key", "G_KEY", "keys in the HUD (next to the number)"),
    "WSWORD": ("weapon warning", "G_WSWORD", "slanted sword: the weapon is about to break (flashes below 20%, steady at 0)"),
    "WARMOR": ("armor warning", "G_WARMOR", "breastplate: the armor is about to break"),
    "WSHIELD": ("shield warning", "G_WSHIELD", "shield: the shield is about to break"),
    "LVUP": ("stat points", "G_LVUP", "green up arrow (chosen 11/11, glyph still to be confirmed: lab/concept/hud_glyphs) next to the level number (HUD row 23): stat points to spend, key C"),
}
for _d in "0123456789":
    HUD[_d] = ("digit %s" % _d, _d, "HUD digit (hp, xp, level, keys, potions)")
for _l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    HUD[_l] = ("letter %s" % _l, "%s / %s" % (_l, _l.lower()), "HUD letter (.enc \"hud\": upper and lower case give the same glyph)")
MINI = {176: ("stairs down (minimap)", "-", "stairs going down on the minimap"),
        177: ("stairs up (minimap)", "-", "stairs going up on the minimap"),
        63: ("blank", "-", "reserved blank character (minimap)")}
for _q in range(16):
    MINI[240 + _q] = ("quadrants %d (minimap)" % _q, "-", "minimap cell: 2x2 tiles, bits = full quadrants (%s)" % format(_q, "04b"))
