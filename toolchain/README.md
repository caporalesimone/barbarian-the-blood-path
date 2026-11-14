# toolchain/ — C64 toolchain in containers

Copyright © 2026 - Simone Caporale (notes). Every external program has its license and its own `.gitignore` in its folder.

A **generic** environment to build and test programs for the Commodore 64: Docker images, external programs compiled once, ROMs
and the scripts that use them. **It knows nothing about the game**: the project that uses it configures it with a `toolchain.env`
file in its root (the folder above `toolchain/`, or `C64_PROJECT`). The project is mounted in the containers at `/work`.

## Images

One multi-stage Dockerfile, `docker/Dockerfile`: one image per target, all with the same parent.

| Image | Target | Contents |
|---|---|---|
| (none) | `base` | ubuntu (`ARG UBUNTU`, today 24.04) + CA + locale + `/work`. Common parent: **it has no name**, it never runs |
| (none) | `tools-builder`, `vice-build`, `zx0-build`, `cc1541-build` | compilers and development libraries; they compile the external programs. They stay in the BuildKit cache and never become images |
| `c64-builder` | `builder` | 64tass, cc65, make, perl, zip, git, Python 3 with Pillow, PyYAML, NumPy, Matplotlib; zx0 and cc1541 in `/opt/c64/bin` |
| `c64-emu-vice` | `emu-vice` | builder + VICE (`x64sc`, `c1541` and its data in `/opt/vice`), gtk3 libraries, Xvfb, ffmpeg |
| `c64-emu-viewer` | `viewer` | KasmVNC Xvnc (official package) + PulseAudio + Node server (`docker/viewer/server.js`): control center, screen with audio, `out/`, C64 keyboard and joystick overlay (`/input`), `/control` towards the player |
| `c64-emu-vc64web` | (Dockerfile of `vc64web-custom/`) | node, Playwright + Chromium, ffmpeg, daemon of the in-browser emulator |

To change Ubuntu: `ARG UBUNTU` in `docker/Dockerfile`, then `images.sh --force` (it also recompiles VICE, zx0 and cc1541 on the new base).

## Scripts

| Script | What it does |
|---|---|
| `images.sh [--force] [names]` | builds the missing images (`builder emu-vice emu-viewer emu-vc64web`); downloads the VICE tarball on the host if missing |
| `run.sh <image> [command]` | runs a command with the project in `/work`, as the host user; `builder` = `c64-builder`, a full name is used as is |
| `viewer.sh start\|stop\|exec` | http://localhost:6080: control center (build and test status, one card per version of `out/releases/`, trends and comparison), live screen with audio (KasmVNC + PulseAudio), vc64web in the browser, the project `out/`; `exec <command>` = command in `c64-emu-vice` attached to screen and audio. With `C64_VIEW_PLAYER` it also starts `c64-emu-player` |
| `viewer_player.py` | viewer player (container `c64-emu-player`): runs `C64_VIEW_PLAYER <file>` on the live screen when the page asks (`POST /control`), through a Unix socket in the `c64-x11` volume; the viewer has no Docker socket |
| `memmap/c64map.py` | **automatic** memory and disk map, with no configuration (in the `c64-builder` container): reads the 64tass listings (`-L`), the labels (`-l`), the PRGs and the `.d64`; writes `index.html` and `memmap.json`. `--work`, `--disk`, `--out`, `--title` (default `C64_VIEW_TITLE`). Static analysis: limits in the page |
| `validate_env.sh` | checks the host: system, WSL and project location, Docker, line endings, ROMs, images, tools |

## Project configuration (`toolchain.env`)

| Variable | Use |
|---|---|
| `C64_PASS_ENV` | host variables passed to the containers by `run.sh` (besides `EMU_URL`, `C64_VIEW`, `DISPLAY`) |
| `C64_EXTRA_IMAGES` | project images checked by `validate_env.sh` |
| `C64_VIEW_DISK` | disk proposed first in the viewer page (pattern with `*`, the highest version wins) |
| `C64_VIEW_TITLE` | project name in the header of the viewer page |
| `C64_VIEW_PLAYER` | command that opens a file (`.d64 .g64 .prg .t64 .crt`, path relative to the project; `--bare` = no disk) on the viewer screen; without it the VICE buttons of the page are off |
| `C64_KRILL_ZIP` | Krill's Loader zip from which cc1541 is compiled |

Other variables: `C64_CA_BUNDLE` (CA of a TLS-intercepting proxy, a secret for npm/pip in the builds), `C64_DOCKER_ARGS` (extra
`docker run` options), `VIEW_PORT`, `VIEW_PASSWORD` (password of the whole viewer, none by default), `VIEW_SIZE`, `VIEW_HOSTS` (host
names allowed besides localhost: the server refuses the others against DNS rebinding).

## Manifest for the viewer (contract with the project, 14/11)

The viewer page (`docker/viewer/www/index.html`) is generic: it reads only these files, written by the project. Everything is
optional except `files`; a missing field is not shown.

`out/releases/v<V>/manifest.json` (one folder per version; `out/releases/latest` = link to the latest):

| Field | Contents |
|---|---|
| `schema` | 1 |
| `version`, `branch`, `built_at`, `updated_at`, `release` | version, git branch, ISO 8601 UTC dates, `true` for a release |
| `files` | `{name: {group, type: file\|dir, files, bytes, sha256, produced}}`: the `.d64` files among them get the vc64web / VICE / download buttons |
| `groups` | `{group: label}`: how to show the groups of `files` and `missing` |
| `missing` | groups not generated in this version |
| `tests` | `{ran, suites[], total, pass, fail, skip, seconds}`; the details in `test_report.json` (`{suites, total_s, results: [{id, suite, desc, result PASS\|FAIL\|SKIP, reason, time}]}`) |
| `stats.metrics` | project measures: `[{id, label, value, unit: B\|s\|"", better: up\|down\|null, hint}]` (cards, trends, comparison) |
| `stats.info` | `[{label, value}]`: data to show and compare, with no chart |
| `stats.disk` | `{blocks_total, blocks_free, blocks_used, files: [{name, type, blocks}]}` (disk directory) |
| `stats.git` | `{commit, subject, dirty}` |
| `stats.build_seconds` | build duration |

Live status, in `out/tmp/` (rewritten atomically: temporary file and rename):
- `build.json`: `{state: running|ok|fail, phase, flags, started, updated}` (times in Unix seconds);
- `tests.json`: `{state, suites, filter, total, started, updated, seconds, current: {id, suite, desc, since}, results: [as above], caps}`.

In this project they are written by `tools/build/publish.py`, `build.sh` and `tests/run.py`.

## External programs

| Folder | Program | License | How it is obtained |
|---|---|---|---|
| `vice/` | VICE 3.10 (reference emulator, gtk3 interface) | GPL-2.0 (`vice/LICENSE`) | official tarball downloaded on the host into `vice/download/` (`VICE_VERSION`, `VICE_URL`), compiled in the `vice-build` stage |
| `zx0/` | ZX0 v2.2 by Einar Saukas (compressor) | BSD-3 (`zx0/LICENSE`) | C sources in git, compiled in the `zx0-build` stage |
| `cc1541/` | cc1541 (writes .d64 disks) | MIT (`cc1541/LICENSE`) | from the Krill zip (`C64_KRILL_ZIP`), compiled in the `cc1541-build` stage |
| `vc64web-custom/` | our variant of vc64web: in-browser emulator + command-line control | see `vc64web-custom/docs/INCLUSION.md` (not verified) | self-contained package; image `c64-emu-vc64web` (`images.sh emu-vc64web`) |
| `kasmvnc/` | KasmVNC 1.5.2 (X server with web client) | GPL-2.0 (`kasmvnc/LICENSE`) | official `.deb` for Ubuntu 24.04, downloaded on the host into `kasmvnc/download/` (`KASMVNC_VERSION`), unpacked in the `viewer` target |
| `roms/` | C64 ROMs (`vice-roms/{C64,DRIVES}`, `open-roms/`) | see `roms/roms.md` | in git; identical to `vc64web-custom/roms/` (`validate_env.sh` checks it) |

Details for the game: `docs/getting-started.md` and `docs/build.md` (section 4b) of the project.
