# Immagini della toolchain C64 (13/11): UN solo Dockerfile multi-stage, una immagine per target. Copyright (c) 2026 - Simone Caporale
#   toolchain/images.sh [--force] [nomi]     (passa i contesti e gli argomenti qui sotto; non serve lanciare docker build a mano)
#
#   base            ubuntu + CA + locale + /work. Stage SENZA nome di immagine: non si avvia mai, serve solo da genitore comune.
#   tools-builder   base + compilatori e librerie di sviluppo. Solo per gli stage di compilazione: non diventa un'immagine.
#   vice-build      VICE dal tarball ufficiale (contesto "vicesrc": toolchain/vice/download/, scaricato sull'host)
#   zx0-build       zx0 dai sorgenti C (contesto "zx0src": toolchain/zx0/)
#   cc1541-build    cc1541 dallo zip di Krill's Loader (contesto "krill" + ARG KRILL_ZIP, dal toolchain.env del progetto)
#   builder         base + assemblatore, cc65, generatori Python + zx0, cc1541 in /opt/c64/bin    -> c64-builder
#   emu-vice        builder + VICE (x64sc, c1541 e i suoi dati in /opt/vice) + librerie, Xvfb, ffmpeg -> c64-emu-vice
#   viewer          base + Xvfb, x11vnc, noVNC, pagina indice                                    -> c64-emu-viewer
# I compilatori stanno SOLO negli stage *-build: le immagini finali ricevono i programmi gia' compilati (COPY --from). La cache di
# BuildKit tiene gli stage compilati: si ricompila solo se cambia un sorgente o la base (docker builder prune svuota la cache).
# L'emulatore secondario (c64-emu-vc64web) ha il suo Dockerfile nel pacchetto autonomo vc64web-custom/ (base node ufficiale).
# Versione di Ubuntu in UN solo punto: ARG UBUNTU (cambiarla rifa' tutte le immagini e ricompila i programmi esterni).
ARG UBUNTU=24.04

FROM ubuntu:${UBUNTU} AS base
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["bash"]

# --- compilatori e librerie di sviluppo (stessa base delle immagini finali: i binari usano le stesse librerie)
FROM base AS tools-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential autoconf automake pkg-config flex bison xa65 dos2unix texinfo file unzip \
        libpng-dev libgif-dev libjpeg-dev libasound2-dev libpulse-dev libcurl4-openssl-dev libevdev-dev \
        libmpg123-dev libvorbis-dev libflac-dev libfontconfig1-dev zlib1g-dev libgtk-3-dev libglew-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src

# VICE (gtk3; headless provato e scartato: segfault all'avvio, docs/build.md). Installato in /opt/vice: i dati stanno dove
# l'eseguibile li cerca (/opt/vice/share/vice), quindi niente copie accanto all'eseguibile.
FROM tools-builder AS vice-build
ARG VICE_VERSION=3.10
COPY --from=vicesrc vice-${VICE_VERSION}.tar.gz /src/
RUN tar xzf vice-${VICE_VERSION}.tar.gz && cd vice-${VICE_VERSION} \
    && ./configure --prefix=/opt/vice --enable-gtk3ui --disable-pdf-docs --without-oss > /src/configure.log 2>&1 \
    && make -j"$(nproc)" > /src/make.log 2>&1 && make install > /src/install.log 2>&1 \
    || { tail -30 /src/*.log; exit 1; }
# nell'immagine solo cio' che serve: x64sc (C64), c1541 (dischi) e i dati (~9 MB)
RUN mkdir -p /out/bin && cp /opt/vice/bin/x64sc /opt/vice/bin/c1541 /out/bin/ && cp -a /opt/vice/share /out/share \
    && /out/bin/x64sc --version > /out/VERSION.txt 2>&1 || true

FROM tools-builder AS zx0-build
COPY --from=zx0src *.c *.h /src/
RUN gcc -O2 -fcommon -o /src/zx0 zx0.c optimize.c compress.c memory.c

FROM tools-builder AS cc1541-build
ARG KRILL_ZIP=loader-v194.zip
COPY --from=krill ${KRILL_ZIP} /src/krill.zip
RUN unzip -q krill.zip 'loader/tools/cc1541/*' && make -s -C loader/tools/cc1541 >/dev/null && cp loader/tools/cc1541/cc1541 /src/cc1541

# --- costruzione dei programmi per C64. Niente VICE, display o compilatore C.
#   64tass                  assemblatore 6502
#   cc65 make perl unzip    Krill's Loader (ca65/ld65 + make + perl, dallo zip)
#   python3 + pil/yaml/numpy/matplotlib   generatori, atlante, mappe, simulatori (matplotlib: grafici dei simulatori)
#   git zip                 versione dei branch e zip dei sorgenti
#   zx0, cc1541             compressore e scrittore di dischi (/opt/c64/bin, nel PATH)
FROM base AS builder
ENV PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PATH=/opt/c64/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends \
        64tass cc65 make perl unzip zip git \
        python3 python3-pil python3-yaml python3-numpy python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
COPY --from=zx0-build /src/zx0 /opt/c64/bin/zx0
COPY --from=cc1541-build /src/cc1541 /opt/c64/bin/cc1541

# --- VICE senza schermo (test, screenshot, misure, render dei brani): VICE, le sue librerie, il display virtuale e ffmpeg
# (WAV -> MP3). Parte da builder: i test assemblano varianti (64tass).
FROM builder AS emu-vice
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgtk-3-0t64 libglew2.2 libgl1 libpulse0 libasound2t64 libpng16-16t64 libevdev2 libcurl4t64 \
        xvfb xauth procps ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=vice-build /out/bin/ /opt/vice/bin/
COPY --from=vice-build /out/share/ /opt/vice/share/
COPY --from=vice-build /out/VERSION.txt /opt/vice/VERSION.txt
ENV PATH=/opt/vice/bin:$PATH

# --- schermo condiviso da guardare nel browser: Xvfb :99 + x11vnc + noVNC, pagina indice su http://localhost:6080
# Gli altri container disegnano sullo stesso schermo montando il volume c64-x11 (DISPLAY=:99). VNC non trasporta audio.
FROM base AS viewer
RUN apt-get update && apt-get install -y --no-install-recommends xvfb x11vnc novnc websockify procps \
    && rm -rf /var/lib/apt/lists/*
COPY viewer/ /opt/viewer/
EXPOSE 6080
CMD ["sh", "/opt/viewer/start.sh"]
