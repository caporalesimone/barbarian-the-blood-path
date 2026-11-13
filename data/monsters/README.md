# Bestiario — `data/monsters/bestiary.tsv`

Copyright © 2026 - Simone Caporale

Un mostro per riga, **tab** come separatore, come `monstdat.tsv` di Diablo/DevilutionX (11/11). Loader e controllo:
`tools/build/bestiary.py` (`python3 tools/build/bestiary.py` stampa i bestiari per capitolo). Nel gioco di oggi entrano le righe con
`implemented = yes`, **nell'ordine del file** (base, forti, finale: il tipo del mostro nel codice = posizione); le altre
sono concept. Pagina della wiki: [docs/bestiario.md](../../docs/bestiario.md).

| Colonna | Significato |
|---|---|
| `id` | identificatore (minuscolo, `_`): nel gioco il nome mostrato è l'id con gli spazi |
| `chapter` | capitolo del bestiario (1..; il boss finale sta nell'ultimo capitolo della storia) |
| `tier` | `base`, `strong` (variante potenziata: stesso sprite, altro colore), `boss` (boss di capitolo), `final` (boss finale) |
| `strong_of` | per `strong`: il mostro base dello stesso capitolo |
| `name` | nome per manuale e documenti (inglese) |
| `floor` | profondità **globale** minima (1..255) da cui compare; vita, CA, ATT e danno crescono per piano da qui (`rules.yaml growth`) |
| `level` | livello del mostro (esperienza e bottino) |
| `hp`, `dmg` | dadi (`NdS+K`) |
| `ac`, `att`, `save` | classe armatura, bonus d'attacco, salvezza |
| `xp` | esperienza alla profondità minima |
| `speed` | velocità (pixel/fotogramma × 4; 8 = normale) |
| `color` | colore C64 dello sprite (0..15) |
| `loot_level_bonus` | bonus al livello del bottino |
| `flags` | `strong`, `final`, `stun_immune` (immune al blocco da colpo), `chapter_boss` |
| `ai` | comportamento voluto (oggi nel codice: inseguimento e mischia, evocazioni solo per il boss finale) |
| `sprite` | sprite usato (`concept` = da disegnare) |
| `implemented` | `yes` = nel gioco di oggi, `no` = concept |
| `notes` | testo libero |

Aggiungere un mostro al gioco: riga con `implemented = yes` nel posto giusto (base prima dei forti, il finale in fondo),
sprite, `./build.sh`, simulatori (`docs/balancing-guide.md`), `docs/mostri.md`.
