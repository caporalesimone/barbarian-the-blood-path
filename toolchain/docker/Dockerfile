# C64 toolchain images (13/11): ONE multi-stage Dockerfile, one image per target. Copyright (c) 2026 - Simone Caporale
#   toolchain/images.sh [--force] [names]     (passes the contexts and arguments below; no need to run docker build by hand)
#
#   base            ubuntu + CA + locale + /work. Stage WITHOUT an image name: it never runs, it is only the common parent.
#   tools-builder   base + compilers and development libraries. Only for the compile stages: it never becomes an image.
#   vice-build      VICE from the official tarball (context "vicesrc": toolchain/vice/download/, downloaded on the host)
#   zx0-build       zx0 from the C sources (context "zx0src": toolchain/zx0/)
#   cc1541-build    cc1541 from the Krill's Loader zip (context "krill" + ARG KRILL_ZIP, from the project toolchain.env)
#   builder         base + assembler, cc65, Python generators + zx0, cc1541 in /opt/c64/bin       -> c64-builder
#   emu-vice        builder + VICE (x64sc, c1541 and their data in /opt/vice) + libraries, Xvfb, ffmpeg -> c64-emu-vice
#   viewer          base + KasmVNC Xvnc, PulseAudio, Node server (index, screen with audio)       -> c64-emu-viewer
# Compilers live ONLY in the *-build stages: the final images get the programs already compiled (COPY --from). The BuildKit cache
# keeps the compiled stages: they are recompiled only when a source or the base changes (docker builder prune empties the cache).
# The secondary emulator (c64-emu-vc64web) has its own Dockerfile in the self-contained package vc64web-custom/ (official node base).
# Ubuntu version in ONE place: ARG UBUNTU (changing it rebuilds all the images and recompiles the external programs).
ARG UBUNTU=24.04

FROM ubuntu:${UBUNTU} AS base
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["bash"]

# --- compilers and development libraries (same base as the final images: the binaries use the same libraries)
FROM base AS tools-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential autoconf automake pkg-config flex bison xa65 dos2unix texinfo file unzip \
        libpng-dev libgif-dev libjpeg-dev libasound2-dev libpulse-dev libcurl4-openssl-dev libevdev-dev \
        libmpg123-dev libvorbis-dev libflac-dev libfontconfig1-dev zlib1g-dev libgtk-3-dev libglew-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src

# VICE (gtk3; headless tried and dropped: segfault at start-up). Installed in /opt/vice: the data is where the executable looks
# for it (/opt/vice/share/vice), so no copies next to the executable.
FROM tools-builder AS vice-build
ARG VICE_VERSION=3.10
COPY --from=vicesrc vice-${VICE_VERSION}.tar.gz /src/
RUN tar xzf vice-${VICE_VERSION}.tar.gz && cd vice-${VICE_VERSION} \
    && ./configure --prefix=/opt/vice --enable-gtk3ui --disable-pdf-docs --without-oss > /src/configure.log 2>&1 \
    && make -j"$(nproc)" > /src/make.log 2>&1 && make install > /src/install.log 2>&1 \
    || { tail -30 /src/*.log; exit 1; }
# only what is needed goes into the image: x64sc (C64), c1541 (disks) and the data (~9 MB)
RUN mkdir -p /out/bin && cp /opt/vice/bin/x64sc /opt/vice/bin/c1541 /out/bin/ && cp -a /opt/vice/share /out/share \
    && /out/bin/x64sc --version > /out/VERSION.txt 2>&1 || true

FROM tools-builder AS zx0-build
COPY --from=zx0src *.c *.h /src/
RUN gcc -O2 -fcommon -o /src/zx0 zx0.c optimize.c compress.c memory.c

FROM tools-builder AS cc1541-build
ARG KRILL_ZIP=loader-v194.zip
COPY --from=krill ${KRILL_ZIP} /src/krill.zip
RUN unzip -q krill.zip 'loader/tools/cc1541/*' && make -s -C loader/tools/cc1541 >/dev/null && cp loader/tools/cc1541/cc1541 /src/cc1541

# --- building C64 programs. No VICE, display or C compiler.
#   64tass                  6502 assembler
#   cc65 make perl unzip    Krill's Loader (ca65/ld65 + make + perl, from the zip)
#   python3 + pil/yaml/numpy/matplotlib   generators, atlas, maps, simulators (matplotlib: simulator charts)
#   git zip                 branch versions and zip archives
#   zx0, cc1541             compressor and disk writer (/opt/c64/bin, in the PATH)
FROM base AS builder
ENV PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PATH=/opt/c64/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends \
        64tass cc65 make perl unzip zip git \
        python3 python3-pil python3-yaml python3-numpy python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
COPY --from=zx0-build /src/zx0 /opt/c64/bin/zx0
COPY --from=cc1541-build /src/cc1541 /opt/c64/bin/cc1541

# --- VICE without a screen (tests, screenshots, measures, music rendering): VICE, its libraries, the virtual display and ffmpeg
# (WAV -> MP3). It starts from builder: the tests assemble variants (64tass).
FROM builder AS emu-vice
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgtk-3-0t64 libglew2.2 libgl1 libpulse0 libasound2t64 libpng16-16t64 libevdev2 libcurl4t64 \
        xvfb xauth procps ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=vice-build /out/bin/ /opt/vice/bin/
COPY --from=vice-build /out/share/ /opt/vice/share/
COPY --from=vice-build /out/VERSION.txt /opt/vice/VERSION.txt
ENV PATH=/opt/vice/bin:$PATH

# --- shared screen to watch in the browser, with audio (13/11): KasmVNC Xvnc (official package, context "kasmvnc":
# toolchain/kasmvnc/download/) + PulseAudio + Node server (toolchain/docker/viewer/server.js) on http://localhost:6080.
# The other containers draw on the same screen and play sound by mounting the c64-x11 volume (DISPLAY=:99,
# PULSE_SERVER=unix:/tmp/.X11-unix/pulse). The server uses pulseaudio2 (native module): compiled with the same node that runs it.
FROM base AS viewer-node
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm build-essential python3 libpulse-dev \
    && rm -rf /var/lib/apt/lists/*
COPY viewer/package.json /opt/viewer/
RUN --mount=type=secret,id=ca if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; npm config set cafile /run/secrets/ca; fi; \
    cd /opt/viewer && npm install --omit=dev --no-audit --no-fund && rm -f package-lock.json

FROM base AS viewer
ARG KASMVNC_DEB=kasmvncserver_ubuntu_noble_1.5.2_amd64.deb
COPY --from=kasmvnc ${KASMVNC_DEB} /tmp/kasmvnc.deb
# only the Xvnc libraries (the package dependencies WITHOUT perl, needed by the unused vncserver script) + the package files
RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6 libgbm1 libgl1 libpixman-1-0 libpng16-16t64 libssl3t64 libunwind8 libx11-6 libxau6 libxcursor1 libxdmcp6 \
        libxext6 libxfixes3 libxfont2 libxrandr2 libxshmfence1 libxtst6 xauth x11-xkb-utils xkb-data \
        pulseaudio nodejs procps \
    && dpkg-deb -x /tmp/kasmvnc.deb / && ln -sf /usr/bin/Xkasmvnc /usr/bin/Xvnc \
    && rm -rf /var/lib/apt/lists/* /tmp/kasmvnc.deb /usr/share/doc /usr/share/man
COPY --from=viewer-node /opt/viewer/node_modules /opt/viewer/node_modules
COPY viewer/ /opt/viewer/
EXPOSE 6080
CMD ["sh", "/opt/viewer/start.sh"]
