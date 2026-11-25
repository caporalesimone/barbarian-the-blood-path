# CLAUDE.md — general rules of the "Barbarian: The Blood Path" project (C64, 6502, 64tass)

Rules valid for **the whole project**. Detailed rules live next to what they govern (13/11, owner's rule):
- **[docs/getting-started.md](docs/getting-started.md)**: to be read **the first time** in every new session, to understand how
  build and tests work (folders, containers, flows, commands). Updated in the same work if the build or the tests change.
- **[src/CLAUDE.md](src/CLAUDE.md)**: **development** rules of the game (sources, memory, loader, saves, UI, graphics and atlas,
  music, data and balancing, simulators). They also apply to `tools/` and `data/` when the game is changed.
- **[tests/CLAUDE.md](tests/CLAUDE.md)**: **test** rules (suites, IDs, test hero, secondary emulator).

## Who and how
- Project by Simone Caporale (engineer). **Always reply in Italian** (mandatory rule, whatever the language of this file), precise,
  technical and direct. ALWAYS flag when a piece of information is not 100% certain.
- Files for Simone are delivered as files (SendUserFile), not as published artifacts.
- All text **in the game** is in English; names of items, monsters and abilities are never translated.
- (14/11, owner's rule) **The toolchain, Lab64, is entirely in English**: code, comments, scripts, generated pages,
  README, messages and **commits** (it has its own `CLAUDE.md`). The rest of the project (wiki, TODO, game commits) stays in Italian.
- Copyright: "COPYRIGHT 2026 - SIMONE CAPORALE" in the game, "Copyright © 2026 - Simone Caporale" in documents.

## Environment: everything in containers (13/11, owner's rule)
- Build and tests run **only in Docker containers**. The **toolchain** (13/11, owner's rule) is generic for the C64 and knows
  nothing about the game. **Since 14/11 it is a separate repository, Lab64** (owner's choice: no submodule, history not kept).
  (15/11, owner's rule) **The game uses Lab64 only as one would expect from a project**: the **`lab64`** command in the PATH
  (`lab64 install`), never a path to Lab64 (no `../lab64`); inside the containers the `lab64` command and Lab64's Python library
  (`vicemon`, `c64test`, `c64manual`, `psid`) are already there. Images **`lab64-<name>`**: `lab64-tools`
  (build **and** tests and VICE tools: builder and VICE merged on 14/11), `lab64-vc64web` secondary emulator, `lab64-viewer` live view
  with audio (KasmVNC). The game's own images are called **`barbarian-<name>`** and live next to their code
  (none today: since 14/11 the manual is made with Lab64's `lab64-pdf-gen`). Lab64's configuration for the game
  is in `lab64.env`. The host only needs sh, Docker (with Compose v2), git, curl. Python runs **only in containers**. Commands (from the
  game folder): `./build.sh [...]` (or `lab64 build`), `lab64 test [--view|--no-view] [--emu] [...]`, `lab64 up|down|ps|view` (compose stack: with `lab64 up` commands run
  in the always-on `lab64-tools` container), `lab64 run <command>`, `lab64 manual`, `lab64 map`,
  `lab64 check-env`. Images carry Lab64's version in the tag (`lab64-tools:1.4`); the game pins it with `LAB64_VERSION` in
  `lab64.env`. Test engine, VICE library and manual generator live in Lab64; the game's `tools/vice/vice_env.sh` only adds
  `ROOT` to Lab64's.
- A change to Lab64 is committed **in its own repository** (in English, with its own rules) and must leave the game's build green.
- Containers must stay **minimal**: each has only what its task needs; no tools used just once
  (tool compilers: only in the Dockerfile's `*-build` stages, which do not become images). Images with the **version** in the tag
  (e.g. `ubuntu:24.04`), never the digest. Lab64's images come from **a single multi-stage Dockerfile**
  (Lab64's `docker/Dockerfile`): the `base` stage (no image name, does not run) is the common parent and holds the
  **Ubuntu version in a single place** (`ARG UBUNTU`). vc64web has its own Dockerfile (standalone package, node base).
- (14/11, owner's rule) External programs are **at the latest version** and are built **from source** where possible
  (VICE, 64tass, cc65, cc1541, zx0: `*-build` stages of Lab64's Dockerfile; the BuildKit cache avoids rebuilding them); only
  **binaries and licenses** go into the images, sources are discarded. Versions, URLs and SHA-256 **only** in Lab64's `build-scripts/sources.conf`;
  `lab64 images` downloads the sources on the host into Lab64's `downloads/` and deletes them once the images are built.
- **Scripts**: POSIX shell/bash when the script only launches commands; Python when there is real logic. Never a Python script that is just
  a wrapper around shell commands. External Python libraries allowed only if they are in the container.
- **Paths**: **no absolute paths** in the project, **only relative ones**, and **all the files needed live in the project**.
  Shell scripts derive the root from the file's location, Python ones from `__file__`; Lab64 only through the `lab64` command (on the host
  and in containers) and its Python library (importable in containers). ROMs only those of Lab64 (`vicemon.ROMS_C64`,
  `vicemon.ROMS`). The only absolute paths allowed are `/work` (the project) and, only if unavoidable, `$LAB64` in containers. After every change to a script: test it
  by running it from another folder.
- **Outputs** (14/11, owner's rule): everything generated lives in `out/` (not in git, except `out/.gitkeep`), in **four folders**:
  `out/work/` = intermediates and outputs of the current build (`.prg`, `.lst`, `.lbl`, `.inc`, logs, `gfx/`, `snd/`, `krill/`, `atlas/`,
  `memory-map/`, `manual/`, `simulators/`, `disk.d64`, test reports...; each tool in its own subfolder; rewritable, can be
  deleted); `out/cache/` = what is reused across builds and not deleted (`zx0/`, `steps/`, `vc64web/`); `out/tmp/` = throwaway
  (can always be deleted; **never** `/tmp`); `out/releases/` = **per-version artifacts**: every build publishes into
  `out/releases/v<version>/` (disk; atlas, maps, test reports and manual only if generated in that build; **no source
  zip**) with `manifest.json` (`tools/build/publish.py`: the game's choices on top of Lab64's `c64publish`); `out/releases/latest` points to the latest; the last **5** versions are kept
  (`./build.sh --keep N`, `KEEP_VERSIONS`). In code the paths are `out/work/...`: **never** write to `out/` directly.
  Publishing off the computer (GitHub) will come later.
- Line endings always LF (`.gitattributes`); on Windows the project lives in the WSL2 filesystem, not on `/mnt/c` (`lab64 check-env`).

## Folders
`src/` (game and libraries for the C64, `src/third-party/`), `data/`, `tools/` (`build/`, `atlas/`, `manual/`,
`simulators/`, `vice/`, `font/`), `tests/` (`smoke/`, `sanity/`, `regression/`), `docs/` (only **written** documentation: what
can be regenerated goes in `out/`, its generators in `tools/`), `lab64.env` (Lab64 configuration), `lab/` (study, not used by the build: [lab/README.md](lab/README.md)),
`out/`. Outside the repository: Lab64 (wherever you like, used only through the `lab64` command: Docker images, external programs,
ROMs, secondary emulator, automatic map, manual; documentation: Lab64's `README.md` and `docs/`). Full table: [docs/getting-started.md](docs/getting-started.md) section 2. A verification script that checks something
becomes a test in `tests/`, it does not stay in `tools/`.

## Documentation: ALWAYS aligned with the code
- `docs/` is the **game's wiki** (index: `docs/index.md`). Every change to a game dynamic
  (generation, combat, items, monsters, loot, saves, disk, memory, UI, tools) must be reflected
  in the matching page **in the same work**, not afterwards. If a page does not exist, it is created and
  added to the index. Diagrams and flows in Mermaid (checked with `mmdc`).
- The wiki describes the game **as it is in the code**; what is only designed lives in the design pages
  (`SISTEMA_COMBATTIMENTO.md`, `BILANCIAMENTO.md`) or in a "Design / to do" section marked as such.
- **Architecture** (11/11, owner's request): `docs/wiki/architettura.md` (structure), `docs/wiki/flussi.md` (how the
  code runs), `docs/wiki/build.md` (pipeline) and `docs/getting-started.md` (build and tests, containers) are updated in the same work when
  a module, a flow, memory, an interrupt, the build or the tests change.
- Generated documents (in `out/work/`, published in `out/releases/`): RAM and disk maps (`lab64 map` from the listings, the disk and the `@map` / `@free` / `@scenario` annotations in the sources: [docs/wiki/build.md](docs/wiki/build.md) section 4a), graphics atlas (`tools/atlas/`,
  rules in `src/CLAUDE.md`), manual (`tools/manual/`, source in `manual/`), simulator reports. If what they
  describe changes, the generators are updated.
- `docs/wiki/FORMATO_DATI.md`: exact format of the files on disk and of the saves; update it together with `SAVE_VER`.
- **Menu screenshots** (08/11, owner's rule): kept **in git** in `docs/screens/` (one per screen +
  mosaic `tutti_i_menu.png`; 13/11: they stay versioned). Only the changed ones are redone:
  `lab64 run tools/vice/shots_menus.sh inventario locanda ...` (no names: all), the mosaic regenerates itself.
- **Manual**: PDF with WeasyPrint in the `lab64-pdf-gen` container (`./build.sh --manual` or `lab64 manual`, `tools/manual/gen_manual.py`):
  (15/11) Lab64's base "c64" theme (page, colors, keys, page numbers) + `manual/tema.css` (only the game's rules);
  the build makes **all the manuals that have a source** (today Italian; English when `manual_src_en.html` exists), a page
  that overflows is a warning, in `--release` an error.
  **Cover** always with the dungeons' **red theme** (palette 4): `dungeon` screenshot in `tools/vice/shots_manual.sh` (floor 8
  with the test seed). **Manual screenshots**: the character is always in a valid position (walkable tile); for the
  village `tools/vice/check_pos.py` checks it, in dungeons look at the screenshot before delivering.
- **Help** (`HELP`, [docs/wiki/help.md](docs/wiki/help.md)): text in `data/help.txt`, HUD crop in `data/help_hud.json`.
  If a key or a screen changes, update `data/help.txt` in the same work; if the HUD graphics or
  layout change, `lab64 run python3 tools/build/gen_help.py --snap` (the release test checks it).
- `TODO.md`: **open work only**, divided into **chapters** with ID `<letter><number>` (A1, B2, ...; A = top priority): each item
  with goal, motivation, complexity, what is needed, caveats. New decisions are written in the item they belong to, with the
  date; a finished item is **deleted** and the decision goes in the relevant wiki page. Decisions and work
  done up to 08/11 are in `docs/wiki/storico-todo.md` (archive, not updated).
- Throwaway files (instructions for another model, temporary plans): deleted when the work is finished.

## Git
- (10/11, owner's rule) Git repository, branch `main`. **One commit per completed activity**, normally **before
  starting a new topic** (no endless commits). "Completed" = green build, **smoke + sanity passed** (`./build.sh`), wiki and
  TODO updated in the same work. Message in Italian: short title + body with what and why, plus the `Co-Authored-By` line
  (never the `Claude-Session` link: owner's rule, 16/11). Commit author: **Simone Caporale `<caporalesimone@gmail.com>`** (repository's local
  configuration; history recreated as a single commit on 13/11 at the owner's request).
- Outside git: `out/` (except `.gitkeep`), caches, logs. Commodore ROMs are **not in git** (16/11, owner's rule: exact names in Lab64's `roms/.gitignore`, empty
  folders in the repository): the user adds them in Lab64 **before** building the images (which contain them and are not distributed);
  `lab64 images` stops if they are missing (names and SHA-256 in Lab64's `roms/roms.md`).
- (17/11, owner's rule) **Export**: when the owner asks for an export, fetch `origin` of **both** repositories (game and Lab64), compare it
  with the local commits and produce **two patch files**, one per repository (only commits not yet on `origin`), delivered as files.
  (25/11, owner's rule) Together with the patches, **two git bundles** (`git bundle create <repo>_origin-<base>..<head>.bundle
  origin/main..main`): the bundle keeps the commits identical (hash, author and commit dates, merges), the patches do not (only
  the author date, no merges). Verify both on a clean copy of `origin/main` (`git am` / `git pull --ff-only <bundle> main`)
  before delivering; the owner applies the bundle with `git pull --ff-only <bundle> main`, then pushes.
- Before delivering, `git status` clean; history is not rewritten unless the owner asks.
- **MP3 outside the repository** (11/11, owner's rule): `lab/music/` (~13 MB) **is not in git and never was**.
  **When the owner asks to download the repository, also include `lab/music/`** (separate zip or together with the git bundle).

## Build, versions, release
- `./build.sh` = **everything** (disk, maps, atlas, smoke and sanity, manual); parameters to skip artifacts: table in the [README](README.md).
  **Owner's rule (14/11): unless requested otherwise, when I build I use `./build.sh --fast`** (disk + smoke and sanity only,
  fast build), and the auxiliary builds (atlas, maps, manual, release) only if requested or if what they describe changes.
  `./build.sh --release` (also regression, `EMU-*`, manual): **only when the owner asks for it**. Details: [docs/getting-started.md](docs/getting-started.md), [docs/wiki/build.md](docs/wiki/build.md).
- **Disk first, tests after** (23/11, owner's rule): after every build that changes the game, **attach the `.d64` to the owner
  (SendUserFile) before running the tests**, so he can try it without waiting for them (`./build.sh --fast --no-test`, send
  `out/releases/latest/*.d64`, then the tests). If the tests fail: fix, rebuild, **send the new `.d64` again**, then test again.
- **A single disk** (11/11 evening, owner's rule): `out/work/disk.d64` (working disk) -> `out/releases/vX.Y/blood_path_vX.Y_1541.d64`. For development:
  `LOAD"*",8`, `POKE 1020,1` (straight to `START`; `POKE 1021,1` = god mode), `RUN` ([docs/wiki/cheats.md](docs/wiki/cheats.md)).
- **Version**: grows by itself (minor number in `version.yaml`) on **every build with changes** to the sources
  (`tools/build/bump_version.py`; fingerprint in `version.yaml`, `source_hash`). **Every delivered file carries the version in its name**
  (`blood_path_vX.Y_1541.d64`; the same for manual and other files when it makes sense).
- **Version 2.0** (09/11, owner's rule): the game becomes **2.0 as soon as the quest system is ready (TODO H1) and never before**:
  until then 1.x (the minor number is an integer and grows without limit: 1.999 → 1.1000).
- **Branch versions** (11/11, owner's rule): a build on a branch other than `main` = version `tag.N`
  (`tools/build/verinfo.py`, `branch_versions` at the bottom of `version.yaml`), so they do not burn `main`'s numbers.
- The save format has a version (`save_version` in `version.yaml`, `SAVE_VER`): change it on every change to the format
  of the character or of the saved floor.
- **VICE** (`x64sc` 3.10, built in the `lab64-tools` image) is the **only authoritative reference** (cycles, timing,
  drive, debug). The game must also run on the secondary emulator vc64web ([docs/wiki/emulatore.md](docs/wiki/emulatore.md),
  rules in `tests/CLAUDE.md`).
