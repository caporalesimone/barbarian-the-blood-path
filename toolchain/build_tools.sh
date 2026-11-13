#!/bin/sh
# Compila i programmi esterni DENTRO c64-tools-builder (13/11). Lo lancia toolchain/build.sh, non si usa a mano.
#   VICE    toolchain/vice/src/vice-$VICE_VERSION.tar.gz -> src/vice-$VICE_VERSION/ -> bin/ (eseguibili + dati accanto)
#   zx0     toolchain/zx0/*.c                              -> toolchain/zx0/bin/zx0
#   cc1541  dallo zip di Krill (C64_KRILL_ZIP, toolchain.env)  -> toolchain/cc1541/bin/cc1541 (+ src/)
# Uso: toolchain/build_tools.sh [vice] [zx0] [cc1541]   (senza argomenti: tutti)
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
cd "$TC/.."
T0=${TC##*/}                            # cartella della toolchain vista dal progetto (toolchain)
JOBS=$(nproc)
WHAT="${*:-vice zx0 cc1541}"
for w in $WHAT; do
case $w in
vice)
    V=$T0/vice; T=$V/src/vice-$VICE_VERSION.tar.gz
    [ -f "$T" ] || { echo "manca $T (lo scarica toolchain/build.sh)"; exit 1; }
    rm -rf "$V/src/vice-$VICE_VERSION" "$V/bin"; tar xzf "$T" -C "$V/src"
    D=$(mktemp -d)
    ( cd "$V/src/vice-$VICE_VERSION" && ./configure --prefix=/opt/vice --enable-gtk3ui --disable-pdf-docs --without-oss >../configure.log 2>&1 \
      && make -j"$JOBS" >../make.log 2>&1 && make install DESTDIR="$D" >../install.log 2>&1 ) \
      || { echo "VICE: errore, vedere $V/src/*.log"; tail -20 "$V/src/make.log" 2>/dev/null; exit 1; }
    # spostabile: VICE cerca i dati (keymap, risorse, ROM) anche ACCANTO all'eseguibile: dati in bin/ insieme ai programmi
    mkdir -p "$V/bin"; cp -a "$D"/opt/vice/bin/. "$V/bin/"; cp -a "$D"/opt/vice/share/vice/. "$V/bin/"
    rm -rf "$D"; "$V/bin/x64sc" --version > "$V/bin/VERSION.txt" 2>&1 || true
    echo "VICE: $(head -1 "$V/bin/VERSION.txt") -> $V/bin";;
zx0)
    Z=$T0/zx0; mkdir -p $Z/bin
    gcc -O2 -fcommon -o $Z/bin/zx0 $Z/zx0.c $Z/optimize.c $Z/compress.c $Z/memory.c
    echo "zx0 -> $Z/bin/zx0";;
cc1541)
    C=$T0/cc1541; rm -rf $C/src $C/bin; mkdir -p $C/src $C/bin
    [ -f "${C64_KRILL_ZIP:-}" ] || { echo "cc1541: manca lo zip di Krill (C64_KRILL_ZIP=${C64_KRILL_ZIP:-})"; exit 1; }
    unzip -q "$C64_KRILL_ZIP" 'loader/tools/cc1541/*' -d $C/src
    make -s -C $C/src/loader/tools/cc1541 >/dev/null
    cp $C/src/loader/tools/cc1541/cc1541 $C/bin/cc1541
    echo "cc1541 -> $C/bin/cc1541";;
*) echo "sconosciuto: $w (vice zx0 cc1541)"; exit 1;;
esac
done
