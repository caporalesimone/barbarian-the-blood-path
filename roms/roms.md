# ROM del C64

Copyright © 2026 - Simone Caporale (note). Stessa cartella, identica, in `roms/` del progetto e in `third-party-tools/vc64web-custom/roms/`
(`./validate_env.sh` controlla che coincidano).

## Set predefinito

Kernal `vice-roms/C64/kernal-901227-03.bin`, BASIC `vice-roms/C64/basic-901226-01.bin`, chargen `vice-roms/C64/chargen-901225-01.bin`,
drive 1541-II `vice-roms/DRIVES/dos1541ii-251968-03.bin` (+ 1541 `dos1541-325302-01+901229-05.bin`). Obbligatorie per VICE
(`tools/vice/vice_rom.py`, che passa anche 1570 e 1571) e per la build di vc64web; le altre sono facoltative.

## File

| File | Byte | SHA-256 | Licenza | Contenuto |
|---|---|---|---|---|
| `vice-roms/C64/kernal-901227-03.bin` | 8192 | `83c60d47047d7beab8e5b7bf6f67f80daa088b7a6a27de0d7e016f6484042721` | Commodore (proprietaria) | Kernal C64 rev. 3, il più diffuso |
| `vice-roms/C64/basic-901226-01.bin` | 8192 | `89878cea0a268734696de11c4bae593eaaa506465d2029d619c0e0cbccdfa62d` | Commodore (proprietaria) | BASIC V2 |
| `vice-roms/C64/chargen-901225-01.bin` | 4096 | `fd0d53b8480e86163ac98998976c72cc58d5dd8eb824ed7b829774e74213b420` | Commodore (proprietaria) | generatore di caratteri standard |
| `vice-roms/DRIVES/dos1541ii-251968-03.bin` | 16384 | `326c289c38753323d7e8167897447cf61ef35189d82eb8d75210ece949adda7c` | Commodore (proprietaria) | firmware 1541-II |
| `vice-roms/DRIVES/dos1541-325302-01+901229-05.bin` | 16384 | `d1d45afb46fd4e2b48d93ca367b889d75654a3b7acf73044e51f6d880c09369e` | Commodore (proprietaria) | firmware 1541 |
| `vice-roms/DRIVES/dos1570-315090-01.bin` | 32768 | `948e042a17578446124f8982857e9a77d9de86fd5f8d939ba5785e62faef6870` | Commodore (proprietaria) | firmware 1570 (test KRILL-18) |
| `vice-roms/DRIVES/dos1571-310654-05.bin` | 32768 | `1fd73459b54a72a737609a879c283645acc37835de2c121633153db9fac81d45` | Commodore (proprietaria) | firmware 1571 (test KRILL-18) |
| `vice-roms/C64/kernal-901227-02.bin` | 8192 | `675cf19a3e04bf68e41cc7a9010b353e51845ed9069db65496c52b79f1e1385f` | Commodore (proprietaria) | Kernal rev. 2 (menu della pagina portable) |
| `vice-roms/C64/kernal-901227-01.bin` | 8192 | `f585600a2e47d0224459e878184d3f4cce2665bfcce65e61732530c6d89c4269` | Commodore (proprietaria) | Kernal rev. 1 (portable) |
| `vice-roms/C64/kernal-251104-04.bin` | 8192 | `81ad3a08920f2782ab031bb3ae02789d1f5f216c3d24d262e752a2b13e9faf73` | Commodore (proprietaria) | Kernal SX-64 (portable) |
| `vice-roms/C64/kernal-390852-01.bin` | 8192 | `0a644f5e7f6ef8cb67b07e7a80f3f9a35584d9b131294c64f6e747a7e5c8a789` | Commodore (proprietaria) | Kernal C64 Games System (portable) |
| `vice-roms/C64/kernal-901246-01.bin` | 8192 | `b2b430a134514af11f3ed64c0929fc5241d8436ba7b12514ec02d1b2cb2fd533` | Commodore (proprietaria) | Kernal 4064 / PET 64, identificazione non certa (portable) |
| `vice-roms/C64/kernal-906145-02.bin` | 8192 | `48af48070ec9adda79ae7f65b772c422062eb12e69214a7cf788e6947a3b4117` | Commodore (proprietaria) | Kernal non identificato (portable) |
| `vice-roms/C64/chargen-906143-02.bin` | 4096 | `0f4a5b0f9ec0d86639ba316053e330fdd849692623a41f8de4a420fcd47c55ee` | Commodore (proprietaria) | chargen alternativo (portable) |
| `open-roms/kernal_generic.rom` | 8192 | `88e86ed3d0c710edab8f90ad146faa8de1ead11f43494b176c7b54724ca721c6` | LGPL-3.0+ (open-roms/LICENSE) | Kernal libero Open ROMs (ripiego di vc64web) |
| `open-roms/basic_generic.rom` | 8192 | `54a1464b4b27c9dc61bbd62a818fdd12ec99af9089111005a5add0ad0e6bd5ec` | LGPL-3.0+, parti MIT (open-roms/LICENSE) | BASIC libero, senza virgola mobile |
| `open-roms/chargen_pxlfont_2.3.rom` | 4096 | `bc5ed24e8e694543f0229800d050acff86d9674aec6dbd95055a26e824d8a395` | LGPL-3.0+; font PXLfont: licenza non verificata | chargen libero (PXLfont) |

## Dove trovarle

- `vice-roms/C64/*`, `vice-roms/DRIVES/*`: cartella dati di VICE, `data/C64/` e `data/DRIVES/` del tarball dei sorgenti
  (https://sourceforge.net/projects/vice-emu/files/releases/) o del mirror git: `https://github.com/VICE-Team/svn-mirror/raw/main/vice/data/C64/<file>`, `https://github.com/VICE-Team/svn-mirror/raw/main/vice/data/DRIVES/<file>`
  (nel mirror il `+` di `dos1541-325302-01+901229-05.bin` va scritto `%2B`). **URL del mirror non aperti da qui** (rete limitata): non verificati.
- `open-roms/*`: https://github.com/MEGA65/open-roms (commit `ad178dbe4d48cd6a317737a8e0e7e662f7e33d32`), con `LICENSE`, `CREDITS.md`, `README.md`.

**Copyright**: le ROM Commodore non sono libere. Sono in git su richiesta del committente (13/11) per esportare il progetto; prima di
pubblicare il repository vanno tolte (TODO I7). Le descrizioni delle varianti vengono dal pacchetto vc64web: `901246-01` e `906145-02`
non sono identificate con certezza.
