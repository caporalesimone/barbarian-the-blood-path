# C64 ROMs

Copyright © 2026 - Simone Caporale (notes). The same folder, identical, is in the project `toolchain/roms/` and in
`toolchain/vc64web-custom/roms/` (`toolchain/validate_env.sh` checks that they match).

## Default set

Kernal `vice-roms/C64/kernal-901227-03.bin`, BASIC `vice-roms/C64/basic-901226-01.bin`, chargen `vice-roms/C64/chargen-901225-01.bin`,
1541-II drive `vice-roms/DRIVES/dos1541ii-251968-03.bin` (+ 1541 `dos1541-325302-01+901229-05.bin`). Required by VICE
(`tools/vice/vice_rom.py`, which also passes 1570 and 1571) and by the vc64web build; the others are optional.

## Files

| File | Bytes | SHA-256 | License | Contents |
|---|---|---|---|---|
| `vice-roms/C64/kernal-901227-03.bin` | 8192 | `83c60d47047d7beab8e5b7bf6f67f80daa088b7a6a27de0d7e016f6484042721` | Commodore (proprietary) | C64 Kernal rev. 3, the most common |
| `vice-roms/C64/basic-901226-01.bin` | 8192 | `89878cea0a268734696de11c4bae593eaaa506465d2029d619c0e0cbccdfa62d` | Commodore (proprietary) | BASIC V2 |
| `vice-roms/C64/chargen-901225-01.bin` | 4096 | `fd0d53b8480e86163ac98998976c72cc58d5dd8eb824ed7b829774e74213b420` | Commodore (proprietary) | standard character generator |
| `vice-roms/DRIVES/dos1541ii-251968-03.bin` | 16384 | `326c289c38753323d7e8167897447cf61ef35189d82eb8d75210ece949adda7c` | Commodore (proprietary) | firmware 1541-II |
| `vice-roms/DRIVES/dos1541-325302-01+901229-05.bin` | 16384 | `d1d45afb46fd4e2b48d93ca367b889d75654a3b7acf73044e51f6d880c09369e` | Commodore (proprietary) | firmware 1541 |
| `vice-roms/DRIVES/dos1570-315090-01.bin` | 32768 | `948e042a17578446124f8982857e9a77d9de86fd5f8d939ba5785e62faef6870` | Commodore (proprietary) | firmware 1570 (test KRILL-18) |
| `vice-roms/DRIVES/dos1571-310654-05.bin` | 32768 | `1fd73459b54a72a737609a879c283645acc37835de2c121633153db9fac81d45` | Commodore (proprietary) | firmware 1571 (test KRILL-18) |
| `vice-roms/C64/kernal-901227-02.bin` | 8192 | `675cf19a3e04bf68e41cc7a9010b353e51845ed9069db65496c52b79f1e1385f` | Commodore (proprietary) | Kernal rev. 2 (menu of the portable page) |
| `vice-roms/C64/kernal-901227-01.bin` | 8192 | `f585600a2e47d0224459e878184d3f4cce2665bfcce65e61732530c6d89c4269` | Commodore (proprietary) | Kernal rev. 1 (portable) |
| `vice-roms/C64/kernal-251104-04.bin` | 8192 | `81ad3a08920f2782ab031bb3ae02789d1f5f216c3d24d262e752a2b13e9faf73` | Commodore (proprietary) | Kernal SX-64 (portable) |
| `vice-roms/C64/kernal-390852-01.bin` | 8192 | `0a644f5e7f6ef8cb67b07e7a80f3f9a35584d9b131294c64f6e747a7e5c8a789` | Commodore (proprietary) | Kernal C64 Games System (portable) |
| `vice-roms/C64/kernal-901246-01.bin` | 8192 | `b2b430a134514af11f3ed64c0929fc5241d8436ba7b12514ec02d1b2cb2fd533` | Commodore (proprietary) | Kernal 4064 / PET 64, identification not certain (portable) |
| `vice-roms/C64/kernal-906145-02.bin` | 8192 | `48af48070ec9adda79ae7f65b772c422062eb12e69214a7cf788e6947a3b4117` | Commodore (proprietary) | unidentified Kernal (portable) |
| `vice-roms/C64/chargen-906143-02.bin` | 4096 | `0f4a5b0f9ec0d86639ba316053e330fdd849692623a41f8de4a420fcd47c55ee` | Commodore (proprietary) | alternative chargen (portable) |
| `open-roms/kernal_generic.rom` | 8192 | `88e86ed3d0c710edab8f90ad146faa8de1ead11f43494b176c7b54724ca721c6` | LGPL-3.0+ (open-roms/LICENSE) | free Open ROMs Kernal (vc64web fallback) |
| `open-roms/basic_generic.rom` | 8192 | `54a1464b4b27c9dc61bbd62a818fdd12ec99af9089111005a5add0ad0e6bd5ec` | LGPL-3.0+, MIT parts (open-roms/LICENSE) | free BASIC, no floating point |
| `open-roms/chargen_pxlfont_2.3.rom` | 4096 | `bc5ed24e8e694543f0229800d050acff86d9674aec6dbd95055a26e824d8a395` | LGPL-3.0+; PXLfont font: license not verified | free chargen (PXLfont) |

## Where to get them

- `vice-roms/C64/*`, `vice-roms/DRIVES/*`: VICE data folder, `data/C64/` and `data/DRIVES/` of the source tarball
  (https://sourceforge.net/projects/vice-emu/files/releases/) or of the git mirror: `https://github.com/VICE-Team/svn-mirror/raw/main/vice/data/C64/<file>`, `https://github.com/VICE-Team/svn-mirror/raw/main/vice/data/DRIVES/<file>`
  (in the mirror the `+` of `dos1541-325302-01+901229-05.bin` must be written `%2B`). **Mirror URLs not opened from here** (restricted network): not verified.
- `open-roms/*`: https://github.com/MEGA65/open-roms (commit `ad178dbe4d48cd6a317737a8e0e7e662f7e33d32`), with `LICENSE`, `CREDITS.md`, `README.md`.

**Copyright**: the Commodore ROMs are not free. They are in git at the owner's request (13/11) to export the project; they must be
removed before publishing the repository (TODO I7). The descriptions of the variants come from the vc64web package: `901246-01` and
`906145-02` are not identified with certainty.
