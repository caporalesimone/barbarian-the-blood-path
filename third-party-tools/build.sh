#!/bin/sh
# Compila UNA volta i programmi esterni che non cambiano (13/11, regola del committente): VICE, zx0, cc1541.
# Crea l'immagine usa e getta barbarian-tools-builder (docker/tools-builder), la usa e alla fine cancella container e immagine.
# Dall'host:   third-party-tools/build.sh [vice] [zx0] [cc1541]      (senza argomenti: tutti; ./build.sh lo chiama da solo se manca qualcosa)
#   VICE_VERSION=3.10 (predefinita qui sotto)   VICE_URL=...   (tarball diverso)
# Il tarball di VICE si scarica qui, SULL'HOST (certificati e proxy del computer), in third-party-tools/vice/src/.
# Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")/.."
VICE_VERSION="${VICE_VERSION:-3.10}"
VICE_URL="${VICE_URL:-https://sourceforge.net/projects/vice-emu/files/releases/vice-$VICE_VERSION.tar.gz/download}"
IMG=barbarian-tools-builder
WHAT="${*:-vice zx0 cc1541}"
command -v docker >/dev/null || { echo "Docker non trovato (./validate_env.sh)"; exit 1; }
case " $WHAT " in *" vice "*)
    T=third-party-tools/vice/src/vice-$VICE_VERSION.tar.gz
    if [ ! -s "$T" ]; then
        mkdir -p third-party-tools/vice/src; echo "scarico $VICE_URL"
        curl -fsSL --retry 3 -o "$T.part" "$VICE_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "download di VICE fallito"; exit 1; }
    fi
    echo "VICE $VICE_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)";;
esac
echo "== immagine $IMG (usa e getta) =="
docker build -q -t $IMG docker/tools-builder >/dev/null
RC=0
docker run --rm --name $IMG -u "$(id -u):$(id -g)" -e VICE_VERSION="$VICE_VERSION" -v "$PWD":/work -w /work $IMG \
    sh third-party-tools/build_tools.sh $WHAT || RC=$?
docker rmi -f $IMG >/dev/null 2>&1 || true            # (regola: immagine e container dei tool non restano)
[ $RC = 0 ] && echo "tool compilati: $WHAT" || echo "ERRORE nella compilazione dei tool"
exit $RC
