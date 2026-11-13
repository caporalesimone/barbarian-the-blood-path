# barbarian-builder (13/11): tutto cio' che serve per COSTRUIRE il gioco per C64 (assemblatore, generatori Python, Krill's Loader)
# e per i simulatori. Niente VICE, niente display, niente compilatore C: i programmi esterni (zx0, cc1541) li compila una volta
# barbarian-tools-builder (third-party-tools/build.sh) e stanno nel progetto, in third-party-tools/*/bin.
# Il progetto si monta in /work (./build.sh, docker/run.sh). Copyright (c) 2026 - Simone Caporale
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
#   64tass                  assemblatore 6502
#   cc65 make perl unzip    Krill's Loader (tools/build/krill_build.sh: ca65/ld65 + make + perl, dallo zip)
#   python3 + pil/yaml/numpy/matplotlib   generatori, atlante, mappe, simulatori (matplotlib: grafici dei simulatori)
#   git zip                 versione dei branch (tools/build/verinfo.py) e zip dei sorgenti (tools/build/release.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
        64tass cc65 make perl unzip zip git ca-certificates \
        python3 python3-pil python3-yaml python3-numpy python3-matplotlib \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
WORKDIR /work
CMD ["bash"]
