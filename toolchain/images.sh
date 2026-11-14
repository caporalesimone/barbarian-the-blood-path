#!/bin/sh
# Builds the toolchain images (13/11). Copyright (c) 2026 - Simone Caporale
#   toolchain/images.sh                       all the missing ones
#   toolchain/images.sh --force [names...]    rebuilds them (names: builder emu-vice emu-viewer emu-vc64web)
#   Once the images exist, the downloaded sources (VICE tarball, KasmVNC .deb) are deleted: --force downloads them again.
# builder, emu-vice, emu-viewer: targets of the multi-stage Dockerfile toolchain/docker/Dockerfile (common unnamed base stage).
#   External programs are compiled INSIDE the build (*-build stages, with the compilers) and only the binaries go into the final
#   images: zx0 and cc1541 in c64-builder, VICE in c64-emu-vice. The BuildKit cache avoids recompiling them at every build.
#   Sources: VICE from the official tarball, downloaded here ON THE HOST (curl: the computer's certificates and proxy) into
#   toolchain/vice/download/; zx0 from toolchain/zx0/; cc1541 from the Krill's Loader zip (C64_KRILL_ZIP, project toolchain.env).
#   VICE_VERSION=3.10 (default), VICE_URL=... (another tarball).
# emu-vc64web: pages generated in the builder, image from the Dockerfile of the self-contained package toolchain/vc64web-custom.
#   KasmVNC (c64-emu-viewer): official .deb, downloaded here on the host into toolchain/kasmvnc/download/ (KASMVNC_VERSION=1.5.2).
# Project images: built by the project (./build.sh). C64_CA_BUNDLE=FILE: CA of a TLS-intercepting proxy, passed as a secret to
# the builds that download with npm (vc64web, viewer server).
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}                     # toolchain/ as seen from the container (project in /work)
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
FORCE=0; [ "${1:-}" = "--force" ] && { FORCE=1; shift; }
NAMES="${*:-builder emu-vice emu-viewer emu-vc64web}"
VICE_VERSION="${VICE_VERSION:-3.10}"
VICE_URL="${VICE_URL:-https://sourceforge.net/projects/vice-emu/files/releases/vice-$VICE_VERSION.tar.gz/download}"
KASMVNC_VERSION="${KASMVNC_VERSION:-1.5.2}"            # package for the Ubuntu of the base (noble = 24.04): change together with ARG UBUNTU
KASMVNC_DEB="${KASMVNC_DEB:-kasmvncserver_ubuntu_noble_${KASMVNC_VERSION}_amd64.deb}"
KASMVNC_URL="${KASMVNC_URL:-https://github.com/kasmtech/KasmVNC/releases/download/v$KASMVNC_VERSION/$KASMVNC_DEB}"
SECRET=""; [ -n "${C64_CA_BUNDLE:-}" ] && SECRET="--secret id=ca,src=$C64_CA_BUNDLE"
have() { docker image inspect "c64-$1" >/dev/null 2>&1; }
vc64web_pages() {                      # vc64web pages in out/cache/vc64web/: VirtualC64 is used by the viewer index, the headless one by the image
    have builder || "$0" builder
    (cd "$ROOT" && "$TC/run.sh" builder python3 "$REL/vc64web-custom/build.py" --no-docker --no-ffmpeg-check --out out/cache/vc64web)
}

vice_tarball() {                       # downloads the VICE tarball on the host, if missing
    T="$TC/vice/download/vice-$VICE_VERSION.tar.gz"
    if [ ! -s "$T" ]; then
        mkdir -p "$TC/vice/download"; echo "downloading $VICE_URL"
        curl -fsSL --retry 3 -o "$T.part" "$VICE_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "VICE download failed"; exit 1; }
    fi
    echo "   VICE $VICE_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)"
}
kasmvnc_deb() {                        # downloads the KasmVNC package on the host, if missing
    T="$TC/kasmvnc/download/$KASMVNC_DEB"
    if [ ! -s "$T" ]; then
        mkdir -p "$TC/kasmvnc/download"; echo "downloading $KASMVNC_URL"
        curl -fsSL --retry 3 -o "$T.part" "$KASMVNC_URL" && mv "$T.part" "$T" || { rm -f "$T.part"; echo "KasmVNC download failed"; exit 1; }
    fi
    echo "   KasmVNC $KASMVNC_VERSION: sha256 $(sha256sum "$T" | cut -c1-64)"
}
target() {                             # docker build of a target of the toolchain Dockerfile, with the source contexts
    K=${C64_KRILL_ZIP:-}
    case "$K" in /*) ;; ?*) K="$ROOT/$K" ;; esac
    [ -f "$K" ] || { echo "missing the Krill's Loader zip for cc1541: C64_KRILL_ZIP=${C64_KRILL_ZIP:-} (toolchain.env)"; exit 1; }
    mkdir -p "$TC/vice/download" "$TC/kasmvnc/download"            # the contexts must exist even if the target does not use them
    case $1 in viewer) kasmvnc_deb ;; *) vice_tarball ;; esac
    # shellcheck disable=SC2086
    DOCKER_BUILDKIT=1 docker build -q $SECRET --target "$1" -t "$2" \
        --build-arg VICE_VERSION="$VICE_VERSION" --build-arg KRILL_ZIP="$(basename "$K")" --build-arg KASMVNC_DEB="$KASMVNC_DEB" \
        --build-context vicesrc="$TC/vice/download" --build-context zx0src="$TC/zx0" --build-context krill="$(dirname "$K")" \
        --build-context kasmvnc="$TC/kasmvnc/download" "$TC/docker" >/dev/null
}
for n in $NAMES; do
    if [ $FORCE = 0 ] && have "$n"; then continue; fi
    echo "== image c64-$n =="
    case $n in
    builder|emu-vice) target "$n" "c64-$n" ;;
    emu-viewer)       target viewer c64-emu-viewer ;;
    emu-vc64web)
        vc64web_pages
        # shellcheck disable=SC2086
        DOCKER_BUILDKIT=1 docker build -q $SECRET -t c64-emu-vc64web --build-context pages="$ROOT/out/cache/vc64web" \
            "$TC/vc64web-custom" >/dev/null ;;
    *) echo "unknown image: $n"; exit 1 ;;
    esac
    echo "   $(docker image inspect -f '{{.Size}}' "c64-$n" | awk '{printf "%.0f MB", $1/1e6}')"
done
# (14/11, owner's rule) what is needed ONLY to build an image is removed once the image exists: VICE and KasmVNC are already
# inside the images; to rebuild them (--force) the sources are downloaded again (same content: the BuildKit cache stays valid).
# The vc64web headless page is needed only by the image build (c64d.js has it in the container).
# The VirtualC64 page is needed by the viewer index even if the vc64web image exists (out/ may have been emptied).
case " $NAMES " in *" emu-viewer "*) ls "$ROOT"/out/cache/vc64web/VirtualC64-v*.html >/dev/null 2>&1 || vc64web_pages >/dev/null ;; esac
have emu-vice && rm -f "$TC/vice/download/"*.tar.gz
have emu-viewer && rm -f "$TC/kasmvnc/download/"*.deb
have emu-vc64web && rm -f "$ROOT/out/cache/vc64web/c64-headless.html"
true
