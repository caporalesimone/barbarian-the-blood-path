# barbarian-tools-builder (13/11): container USA E GETTA che compila una sola volta i programmi esterni che non cambiano
# (VICE, zx0, cc1541) in third-party-tools/*/bin. Contiene solo i compilatori e le librerie di sviluppo: nessun file del progetto.
# Non si usa a mano: lo crea third-party-tools/build.sh, che alla fine cancella container e immagine.
# Stessa base di barbarian-builder / barbarian-emu-vice (ubuntu:24.04): i binari usano le stesse librerie.
# Copyright (c) 2026 - Simone Caporale
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential autoconf automake pkg-config flex bison xa65 dos2unix texinfo file unzip ca-certificates \
        libpng-dev libgif-dev libjpeg-dev libasound2-dev libpulse-dev libcurl4-openssl-dev libevdev-dev \
        libmpg123-dev libvorbis-dev libflac-dev libfontconfig1-dev zlib1g-dev libgtk-3-dev libglew-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
