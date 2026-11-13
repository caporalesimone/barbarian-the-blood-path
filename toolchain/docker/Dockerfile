# Immagini della toolchain C64 (13/11): UN solo Dockerfile multi-stage, una immagine per target. Copyright (c) 2026 - Simone Caporale
#   docker build --target builder  -t c64-builder  toolchain/docker      (lo fa toolchain/images.sh)
#
#   base            ubuntu + CA + locale + /work. Stage SENZA nome di immagine: non si avvia mai, serve solo da genitore comune.
#   tools-builder   base + compilatori: compila VICE, zx0, cc1541 (toolchain/build.sh). Usa e getta: l'immagine si cancella dopo.
#   builder         base + assemblatore, cc65, generatori Python                         -> c64-builder
#   emu-vice        builder + librerie di VICE, Xvfb, ffmpeg (test e strumenti in VICE)  -> c64-emu-vice
#   viewer          base + Xvfb, x11vnc, noVNC, pagina indice                            -> c64-emu-viewer
# L'emulatore secondario (c64-emu-vc64web) ha il suo Dockerfile nel pacchetto autonomo vc64web-custom/ (base node ufficiale).
# Versione di Ubuntu in UN solo punto: ARG UBUNTU (cambiarla rifa' tutte le immagini; poi ricompilare i tool: toolchain/build.sh).
ARG UBUNTU=24.04

FROM ubuntu:${UBUNTU} AS base
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["bash"]

# --- compilatori e librerie di sviluppo dei tool (stessa base: i binari usano le stesse librerie delle immagini che li eseguono)
FROM base AS tools-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential autoconf automake pkg-config flex bison xa65 dos2unix texinfo file unzip \
        libpng-dev libgif-dev libjpeg-dev libasound2-dev libpulse-dev libcurl4-openssl-dev libevdev-dev \
        libmpg123-dev libvorbis-dev libflac-dev libfontconfig1-dev zlib1g-dev libgtk-3-dev libglew-dev \
    && rm -rf /var/lib/apt/lists/*

# --- costruzione dei programmi per C64. Niente VICE, display o compilatore C (zx0 e cc1541: toolchain/*/bin)
#   64tass                  assemblatore 6502
#   cc65 make perl unzip    Krill's Loader (ca65/ld65 + make + perl, dallo zip)
#   python3 + pil/yaml/numpy/matplotlib   generatori, atlante, mappe, simulatori (matplotlib: grafici dei simulatori)
#   git zip                 versione dei branch e zip dei sorgenti
FROM base AS builder
ENV PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
RUN apt-get update && apt-get install -y --no-install-recommends \
        64tass cc65 make perl unzip zip git \
        python3 python3-pil python3-yaml python3-numpy python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'

# --- VICE senza schermo (test, screenshot, misure, render dei brani). VICE e' toolchain/vice/bin (compilato una volta, gtk3);
# qui solo le sue librerie, il display virtuale e ffmpeg (WAV -> MP3). Parte da builder: i test assemblano varianti (64tass).
FROM builder AS emu-vice
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgtk-3-0t64 libglew2.2 libgl1 libpulse0 libasound2t64 libpng16-16t64 libevdev2 libcurl4t64 \
        xvfb xauth procps ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# --- schermo condiviso da guardare nel browser: Xvfb :99 + x11vnc + noVNC, pagina indice su http://localhost:6080
# Gli altri container disegnano sullo stesso schermo montando il volume c64-x11 (DISPLAY=:99). VNC non trasporta audio.
FROM base AS viewer
RUN apt-get update && apt-get install -y --no-install-recommends xvfb x11vnc novnc websockify procps \
    && rm -rf /var/lib/apt/lists/*
COPY viewer/ /opt/viewer/
EXPOSE 6080
CMD ["sh", "/opt/viewer/start.sh"]
