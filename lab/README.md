# lab/ — materiale di studio

Copyright © 2026 - Simone Caporale

Materiale di riferimento e di prova che **la build non usa** e che i test non leggono. Si tiene per memoria delle scelte fatte;
nulla qui deve servire per costruire il gioco (se serve, va spostato in `src/`, `data/` o `tools/`).

| Cartella | Contenuto | In git |
|---|---|---|
| `concept/hud_glyphs/` | studio dei glifi dell'HUD: foglio di prova, `glyphs.json`, script `make_sheet.py` | sì |
| `fonts/out_reliquia/` | anteprime delle varianti "reliquia" del font della UI, conservate come riferimento della scelta (le anteprime nuove le scrivono `tools/font/*.py` in `out/font/`) | sì |
| `villaggi/` | (15/11) concept delle mappe dei villaggi dei capitoli 2–5 (`concept_maps.py`, `mapkit.py`: prima stesura dei testi in `data/`) e `proposta-a-temi/`, la proposta scartata (stessa struttura del villaggio 1 con altri tile), da valutare | sì |
| `music/` | brani MP3 di riferimento e candidati (~13 MB) | **no** (`.gitignore`): includerli a mano quando si scarica il progetto |
