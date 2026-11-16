# Bestiario — `data/monsters/bestiary.tsv`

Copyright © 2026 - Simone Caporale

Un mostro per riga, **tab** come separatore, come `monstdat.tsv` di Diablo/DevilutionX (11/11). Loader e controllo:
`tools/build/bestiary.py` (`python3 tools/build/bestiary.py` stampa i bestiari per capitolo). Nel gioco di oggi entrano le righe con
`implemented = yes`, **nell'ordine del file** (base, forti, finale: il tipo del mostro nel codice = posizione); le altre
sono concept. Pagina della wiki: [docs/wiki/bestiario.md](../../docs/wiki/bestiario.md).

| Colonna | Significato |
|---|---|
| `id` | identificatore (minuscolo, `_`); per le righe del gioco (capitolo 1) il nome mostrato è l'id con gli spazi |
| `chapter` | capitolo del bestiario (1..; il boss finale sta nell'ultimo capitolo della storia) |
| `tier` | `base`, `strong` (variante potenziata: stesso sprite, altro colore), `boss` (boss di capitolo), `final` (boss finale) |
| `strong_of` | per `strong`: il mostro base dello stesso capitolo |
| `name` | nome per manuale e documenti (inglese). (15/11) In minuscolo è il nome che la barra mostra nel gioco per i mostri dei capitoli 2–4 e per i boss di capitolo: la build controlla che coincida con i disegni (`tools/build/gen_gfx.py`) |
| `floor` | profondità **globale** minima (1..255) da cui compare; vita, CA, ATT e danno crescono per piano da qui (`rules.yaml growth`) |
| `level` | livello del mostro (esperienza e bottino) |
| `hp`, `dmg` | dadi (`NdS+K`) |
| `ac`, `att`, `save` | classe armatura, bonus d'attacco, salvezza |
| `xp` | esperienza alla profondità minima |
| `speed` | velocità (pixel/fotogramma × 4; 8 = normale) |
| `color` | colore C64 dello sprite (0..15); (15/11) per ogni riga con uno sprite nel gioco deve coincidere con il disegno (controllo della build) |
| `loot_level_bonus` | bonus al livello del bottino |
| `flags` | `strong`, `final`, `stun_immune` (immune al blocco da colpo), `chapter_boss` |
| `ai` | comportamento voluto (oggi nel codice: inseguimento e mischia, evocazioni solo per il boss finale) |
| `sprite` | sprite usato (la famiglia: la variante forte usa lo sprite della base con un'aggiunta; `concept` = da disegnare). Dal 15/11 tutti i mostri dei capitoli 1–4 hanno lo sprite nel gioco (`tools/build/monsters.py`, `tools/build/monsters_chap.py`) |
| `implemented` | `yes` = **statistiche** nel gioco di oggi (sono le righe da cui `gen_db.py` fa i tipi 1..9), `no` = statistiche e IA concept. (15/11) Le righe `no` dei capitoli 2–4 hanno nel gioco sprite, colore e nome, ma usano le statistiche del tipo nella stessa posizione del capitolo 1 (nota della riga) |
| `notes` | testo libero |

Aggiungere un mostro al gioco: riga con `implemented = yes` nel posto giusto (base prima dei forti, il finale in fondo),
sprite, `./build.sh`, simulatori (`docs/wiki/balancing-guide.md`), `docs/wiki/mostri.md`.
