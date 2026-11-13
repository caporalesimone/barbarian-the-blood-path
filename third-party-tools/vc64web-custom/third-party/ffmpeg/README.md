# ffmpeg — NON incluso

**Cos'è**: codificatore usato dal demone per i video deterministici (`c64 video`, `video start` negli script): H.264 (libx264). Non è nel pacchetto: va nel PATH (il Dockerfile lo installa con `apt`, pacchetto Debian `ffmpeg`).

**Origine**: https://ffmpeg.org
**Licenza**: LGPL-2.1+ o GPL-2+ a seconda di come è compilato; le build che includono libx264 (come quella Debian, da quanto ricordo, non verificato) sono GPL. Se si pubblica un'immagine Docker che lo contiene, valgono quei termini.
