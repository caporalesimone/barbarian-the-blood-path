# lab/ — materiale di studio

Copyright © 2026 - Simone Caporale

Materiale di riferimento e di prova che **la build non usa** e che i test non leggono. Si tiene per memoria delle scelte fatte;
nulla qui deve servire per costruire il gioco (se serve, va spostato in `src/`, `data/` o `tools/`).

| Cartella | Contenuto | In git |
|---|---|---|
| `archivio_v1.9/` | archivio della versione 1.9 del gioco (sorgenti e note di allora, `NOTE.md`), per confronto | sì |
| `concept/hud_glyphs/` | studio dei glifi dell'HUD: foglio di prova, `glyphs.json`, script `make_sheet.py` | sì |
| `concepts/` | immagini di concept del gioco | sì |
| `fonts/out_reliquia/` | anteprime delle varianti "reliquia" del font della UI, conservate come riferimento della scelta (le anteprime nuove le scrivono `tools/font/*.py` in `out/font/`) | sì |
| `krill-proto/` | prototipo di prova di Krill's Loader (prima dell'integrazione nel gioco, `docs/FastLoader.md`) | sì |
| `music/` | brani MP3 di riferimento e candidati (~13 MB) | **no** (`.gitignore`): includerli a mano quando si scarica il progetto |
