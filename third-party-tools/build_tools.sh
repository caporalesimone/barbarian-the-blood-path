#!/bin/sh
# Compila i programmi esterni DENTRO barbarian-tools-builder (13/11). Lo lancia third-party-tools/build.sh, non si usa a mano.
#   VICE    third-party-tools/vice/src/vice-$VICE_VERSION.tar.gz -> src/vice-$VICE_VERSION/ -> bin/ (eseguibili + dati accanto)
#   zx0     third-party-tools/zx0/*.c                                 -> third-party-tools/zx0/bin/zx0
#   cc1541  dal pacchetto di Krill (src/third-party/krill/*.zip)      -> third-party-tools/cc1541/bin/cc1541 (+ src/)
# Uso: third-party-tools/build_tools.sh [vice] [zx0] [cc1541]   (senza argomenti: tutti)
set -eu
cd "$(dirname "$0")/.."
JOBS=$(nproc)
WHAT="${*:-vice zx0 cc1541}"
for w in $WHAT; do
case $w in
vice)
    V=third-party-tools/vice; T=$V/src/vice-$VICE_VERSION.tar.gz
    [ -f "$T" ] || { echo "manca $T (lo scarica third-party-tools/build.sh)"; exit 1; }
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
    Z=third-party-tools/zx0; mkdir -p $Z/bin
    gcc -O2 -fcommon -o $Z/bin/zx0 $Z/zx0.c $Z/optimize.c $Z/compress.c $Z/memory.c
    echo "zx0 -> $Z/bin/zx0";;
cc1541)
    C=third-party-tools/cc1541; rm -rf $C/src $C/bin; mkdir -p $C/src $C/bin
    unzip -q src/third-party/krill/loader-v194.zip 'loader/tools/cc1541/*' -d $C/src
    make -s -C $C/src/loader/tools/cc1541 >/dev/null
    cp $C/src/loader/tools/cc1541/cc1541 $C/bin/cc1541
    echo "cc1541 -> $C/bin/cc1541";;
*) echo "sconosciuto: $w (vice zx0 cc1541)"; exit 1;;
esac
done
