#!/usr/bin/env python3
"""Mosaico (3 colonne) delle schermate a menu salvate in docs/screens/ (tools/vice/shots_menus.sh), ingrandito 2x, e pagina
offline docs/screens/index.html (immagini relative: si apre dal disco senza rete)."""
import os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs", "screens")
TITLES = {"menu_iniziale": "Menu iniziale", "nuovo_barbaro": "Nuovo barbaro", "scheda": "Scheda del barbaro salvato",
          "inventario": "Inventario", "baule": "Baule del dungeon", "fabbro": "Fabbro",
          "alchimista": "Alchimista", "locanda": "Locanda (baule)",
          "menu_gioco": "Menu di gioco", "quit": "Quit game?", "morte": "Morte", "mappa": "Mappa",
          "badsave": "Salvataggi di un'altra versione", "io_screen": "Caricamento / salvataggio",
          "io_generico": "Caricamento generico (locanda)", "io_livello": "Caricamento di un piano",
          "leva": "Leva della sala del trono (piano 20)",
          "personaggio": "Personaggio (C): punti in attesa, gettoni respec",
          "personaggio_vuoto": "Personaggio (C): senza punti ne' gettoni",
          "trucchi": "Trucchi (solo build di debug, CHEATS=1)"}
ORDER = list(TITLES)
ims = [(n, Image.open(os.path.join(D, n + ".png")).convert("RGB")) for n in ORDER if os.path.exists(os.path.join(D, n + ".png"))]
w, h = ims[0][1].size
out = Image.new("RGB", (3 * w + 12, ((len(ims) + 2) // 3) * (h + 14) + 6), (80, 80, 80))
d = ImageDraw.Draw(out)
for i, (n, im) in enumerate(ims):
    x, y = (i % 3) * (w + 6), (i // 3) * (h + 14)
    d.text((x + 4, y + 1), n, fill=(255, 255, 255))
    out.paste(im.resize((w, h)), (x, y + 12))
out.resize((out.size[0] * 2, out.size[1] * 2), Image.NEAREST).save(os.path.join(D, "tutti_i_menu.png"))
print("mosaico:", os.path.join(D, "tutti_i_menu.png"), len(ims), "schermate")

rows = "\n".join(f'<figure><img src="{n}.png" alt="{TITLES[n]}"><figcaption>{TITLES[n]} <code>{n}.png</code></figcaption></figure>'
                 for n, _ in ims)
html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><title>Schermate a menu</title>
<style>body{{background:#222;color:#ddd;font-family:sans-serif;margin:16px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:16px}}
figure{{margin:0;background:#333;padding:8px}}img{{width:100%;image-rendering:pixelated}}code{{color:#aaa}}</style></head>
<body><h1>Barbarian: The Blood Path — schermate a menu</h1>
<p>Screenshot da VICE (tools/vice/shots_menus.sh). Pagina offline: le immagini sono nella stessa cartella.</p>
<main>{rows}</main></body></html>"""
open(os.path.join(D, "index.html"), "w").write(html)
print("pagina:", os.path.join(D, "index.html"))
