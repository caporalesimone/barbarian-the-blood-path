#!/bin/sh
# Costruisce le immagini della toolchain (13/11). Copyright (c) 2026 - Simone Caporale
#   toolchain/images.sh                       tutte quelle che mancano
#   toolchain/images.sh --force [nomi...]     le rifa' (nomi: builder emu-vice emu-viewer emu-vc64web)
#   A immagini fatte si cancellano i sorgenti scaricati (tarball di VICE, .deb di KasmVNC): --force li riscarica.
# builder, emu-vice, emu-viewer: target del Dockerfile multi-stage toolchain/docker/Dockerfile (stage base comune, senza nome).
#   I programmi esterni si compilano DENTRO la build (stage *-build, con i compilatori) e nelle immagini finali entrano solo i
#   binari: zx0 e cc1541 in c64-builder, VICE in c64-emu-vice. La cache di BuildKit evita di ricompilarli a ogni build.
#   Sorgenti: VICE dal tarball ufficiale, scaricato qui SULL'HOST (curl: certificati e proxy del computer) in toolchain/vice/download/;
#   zx0 da toolchain/zx0/; cc1541 dallo zip di Krill's Loader (C64_KRILL_ZIP, toolchain.env del progetto).
#   VICE_VERSION=3.10 (predefinita), VICE_URL=... (tarball diverso).
# emu-vc64web: pagine generate nel builder, immagine dal Dockerfile del pacchetto autonomo toolchain/vc64web-custom.
#   KasmVNC (c64-emu-viewer): pacchetto ufficiale .deb, scaricato qui sull'host in toolchain/kasmvnc/download/ (KASMVNC_VERSION=1.5.2).
# Immagini del progetto: le costruisce il progetto (./build.sh). C64_CA_BUNDLE=FILE: CA di un proxy che intercetta TLS, passata
# come segreto alle build che scaricano con npm (vc64web, server del viewer).
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}                     # toolchain/ vista dal container (progetto in /work)
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
FORCE=0; [ "${1:-}" = "--force" ] && { FORCE=1; shift; }
NAMES="${*:-builder emu-vice emu-viewer emu-vc64web}"
VICE_VERSION="${VICE_VERSION:-3.10}"
VICE_URL="${VICE_URL:-https://sourceforge.net/projects/vice-emu/files/releases/vice-$VICE_VERSION.tar.gz/download}"
KASMVNC_VERSION="${KASMVNC_VERSION:-1.5.2}"            # pacchetto per la Ubuntu della base (noble = 24.04): cambiare insieme ad ARG UBUNTU
KASMVNC_DEB="${KASMVNC_DEB:-kasmvncserver_ubuntu_noble_${KASMVNC_VERSION}_amd64.deb}"
KASMVNC_URL="${KASMVNC_URL:-https://github.com/kasmtech/KasmVNC/releases/download/v$KASMVNC_VERSION/$KASMVNC_DEB}"
SECRET=""; [ -n "${C64_CA_BUNDLE:-}" ] && SECRET="--secret id=ca,src=$C64_CA_BUNDLE"
have() { docker image inspect "c64-$1" >/dev/null 2>&1; }
vc64web_pages() {                      # pagine di vc64web in out/cache/vc64web/: la page VirtualC64 la usa l'indice del viewer, la headless l'immagine
    have builder || "$0" builder
    (cd "$ROOT" && "$TC/run.sh" builder python3 "$REL/vc64web-custom/build.py" --no-docker --no-ffmpeg-check --out out/cache/vc64web)
}

vice_tarball() {                       # scarica il tarball di VICE sull'host, se manca
    T="$TC/vice/download/vice-$VICE_VERSION.tar.gz"
    if [ ! -s "$T" ]; then
        mkdir -p "$TC/vice/download"; echo "scarico $VICE_URL"
        curl -fsSL --retry 3 -o "$T.part" "$VICE_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "download di VICE fallito"; exit 1; }
    fi
    echo "   VICE $VICE_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)"
}
kasmvnc_deb() {                        # scarica il pacchetto di KasmVNC sull'host, se manca
    T="$TC/kasmvnc/download/$KASMVNC_DEB"
    if [ ! -s "$T" ]; then
        mkdir -p "$TC/kasmvnc/download"; echo "scarico $KASMVNC_URL"
        curl -fsSL --retry 3 -o "$T.part" "$KASMVNC_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "download di KasmVNC fallito"; exit 1; }
    fi
    echo "   KasmVNC $KASMVNC_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)"
}
target() {                             # docker build di un target del Dockerfile della toolchain, con i contesti dei sorgenti
    K=${C64_KRILL_ZIP:-}
    case "$K" in /*) ;; ?*) K="$ROOT/$K" ;; esac
    [ -f "$K" ] || { echo "manca lo zip di Krill's Loader per cc1541: C64_KRILL_ZIP=${C64_KRILL_ZIP:-} (toolchain.env)"; exit 1; }
    mkdir -p "$TC/vice/download" "$TC/kasmvnc/download"            # i contesti devono esistere anche se il target non li usa
    case $1 in viewer) kasmvnc_deb ;; *) vice_tarball ;; esac
    # shellcheck disable=SC2086
    DOCKER_BUILDKIT=1 docker build -q $SECRET --target "$1" -t "$2" \
        --build-arg VICE_VERSION="$VICE_VERSION" --build-arg KRILL_ZIP="$(basename "$K")" --build-arg KASMVNC_DEB="$KASMVNC_DEB" \
        --build-context vicesrc="$TC/vice/download" --build-context zx0src="$TC/zx0" --build-context krill="$(dirname "$K")" \
        --build-context kasmvnc="$TC/kasmvnc/download" "$TC/docker" >/dev/null
}
for n in $NAMES; do
    if [ $FORCE = 0 ] && have "$n"; then continue; fi
    echo "== immagine c64-$n =="
    case $n in
    builder|emu-vice) target "$n" "c64-$n" ;;
    emu-viewer)       target viewer c64-emu-viewer ;;
    emu-vc64web)
        vc64web_pages
        # shellcheck disable=SC2086
        DOCKER_BUILDKIT=1 docker build -q $SECRET -t c64-emu-vc64web --build-context pages="$ROOT/out/cache/vc64web" \
            "$TC/vc64web-custom" >/dev/null ;;
    *) echo "immagine sconosciuta: $n"; exit 1 ;;
    esac
    echo "   $(docker image inspect -f '{{.Size}}' "c64-$n" | awk '{printf "%.0f MB", $1/1e6}')"
done
# (14/11, regola del committente) cio' che serve SOLO a costruire un'immagine si toglie a immagine fatta: VICE e KasmVNC sono
# gia' dentro le immagini; per rifarle (--force) i sorgenti si riscaricano da soli (il contenuto e' lo stesso: la cache di
# BuildKit resta valida). La pagina headless di vc64web serve solo alla build dell'immagine (c64d.js la ha nel container).
# la pagina VirtualC64 serve all'indice del viewer anche se l'immagine di vc64web c'e' gia' (out/ puo' essere stato svuotato)
case " $NAMES " in *" emu-viewer "*) ls "$ROOT"/out/cache/vc64web/VirtualC64-v*.html >/dev/null 2>&1 || vc64web_pages >/dev/null ;; esac
have emu-vice && rm -f "$TC/vice/download/"*.tar.gz
have emu-viewer && rm -f "$TC/kasmvnc/download/"*.deb
have emu-vc64web && rm -f "$ROOT/out/cache/vc64web/c64-headless.html"
true
