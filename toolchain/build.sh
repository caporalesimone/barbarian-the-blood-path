#!/bin/sh
# Compila UNA volta i programmi esterni che non cambiano (13/11, regola del committente): VICE, zx0, cc1541.
# Crea l'immagine usa e getta c64-tools-builder (target tools-builder di toolchain/docker/Dockerfile), la usa e alla fine
# cancella container e immagine.
# Dall'host:   toolchain/build.sh [vice] [zx0] [cc1541]      (senza argomenti: tutti; ./build.sh lo chiama da solo se manca qualcosa)
#   VICE_VERSION=3.10 (predefinita qui sotto)   VICE_URL=...   (tarball diverso)
# Il tarball di VICE si scarica qui, SULL'HOST (certificati e proxy del computer), in toolchain/vice/src/. cc1541: dallo zip di Krill (C64_KRILL_ZIP, toolchain.env).
# Copyright (c) 2026 - Simone Caporale
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
cd "$ROOT"
VICE_VERSION="${VICE_VERSION:-3.10}"
VICE_URL="${VICE_URL:-https://sourceforge.net/projects/vice-emu/files/releases/vice-$VICE_VERSION.tar.gz/download}"
IMG=c64-tools-builder
WHAT="${*:-vice zx0 cc1541}"
command -v docker >/dev/null || { echo "Docker non trovato (./validate_env.sh)"; exit 1; }
case " $WHAT " in *" vice "*)
    T=$REL/vice/src/vice-$VICE_VERSION.tar.gz
    if [ ! -s "$T" ]; then
        mkdir -p $REL/vice/src; echo "scarico $VICE_URL"
        curl -fsSL --retry 3 -o "$T.part" "$VICE_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "download di VICE fallito"; exit 1; }
    fi
    echo "VICE $VICE_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)";;
esac
echo "== immagine $IMG (usa e getta) =="
DOCKER_BUILDKIT=1 docker build -q --target tools-builder -t $IMG "$TC/docker" >/dev/null
RC=0
docker run --rm --name $IMG -u "$(id -u):$(id -g)" -e VICE_VERSION="$VICE_VERSION" -e C64_KRILL_ZIP="${C64_KRILL_ZIP:-}" -v "$ROOT":/work -w /work $IMG \
    sh $REL/build_tools.sh $WHAT || RC=$?
docker rmi -f $IMG >/dev/null 2>&1 || true            # (regola: immagine e container dei tool non restano)
[ $RC = 0 ] && echo "tool compilati: $WHAT" || echo "ERRORE nella compilazione dei tool"
exit $RC
