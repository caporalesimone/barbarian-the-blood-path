# Open ROMs (free Kernal/Basic/chargen)

**What it is**: free replacements of the Commodore ROMs (Open ROMs project, MEGA65). Here are the three images of the «generic» variant (`kernal_generic.rom`, `basic_generic.rom`, `chargen_pxlfont_2.3.rom`), used by the emulator only when the Commodore ROMs are missing. Known limits: no floating point in Basic (`PRINT 2+3` gives `?NOT IMPLEMENTED ERROR`).

**Origin**: https://github.com/MEGA65/open-roms (checkout used: commit `ad178dbe4d48cd6a317737a8e0e7e662f7e33d32`, 16/05/2026). How the three images were produced (build from source or copy from a release) is not recorded in this project.

**License**: GNU LGPL v3 or later for the package (checked in the `LICENSE` file, copied here with `CREDITS.md`); some Basic files are under the MIT license (Microsoft), as stated in `LICENSE`. The chargen font (PXLfont, by Retrofan according to `CREDITS.md`) has its own license, **not verified**: check it before publishing the chargen.
