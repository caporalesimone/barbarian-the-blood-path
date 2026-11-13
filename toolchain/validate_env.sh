#!/bin/sh
# Verifica l'ambiente dell'HOST prima di usare la toolchain e il progetto (13/11, richiesta del committente).
# Copyright (c) 2026 - Simone Caporale
#   toolchain/validate_env.sh   (o ./validate_env.sh del progetto)   stampa una riga per controllo: OK / AVVISO / ERRORE; esce con 1 se c'e' almeno un ERRORE
# Sull'host servono solo: sh, Docker (con BuildKit), git, curl (download di VICE). Tutto il resto gira nei container.
# Controlla anche DOVE sta il progetto: dentro il filesystem Linux di WSL (veloce) o su un disco Windows (/mnt/c, lento
# e con problemi di permessi e fine riga). Metodo: il tipo di filesystem del punto di montaggio che contiene la cartella del
# progetto, letto da /proc/self/mountinfo (il mount con il prefisso piu' lungo), non il nome del percorso.
TC=$(cd "$(dirname "$0")" && pwd) || exit 1
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}
cd "$ROOT" || exit 1
[ -f toolchain.env ] && . ./toolchain.env
ERR=0; WARN=0
ok()   { printf '  OK      %s\n' "$*"; }
warn() { printf '  AVVISO  %s\n' "$*"; WARN=$((WARN + 1)); }
err()  { printf '  ERRORE  %s\n' "$*"; ERR=$((ERR + 1)); }

echo "== sistema =="
OS=$(uname -s)
WSL=0
if [ -r /proc/sys/kernel/osrelease ] && grep -qi microsoft /proc/sys/kernel/osrelease; then WSL=1; fi
[ -n "${WSL_DISTRO_NAME:-}" ] || [ -n "${WSL_INTEROP:-}" ] && WSL=1
case "$OS" in
Linux)  if [ $WSL = 1 ]; then ok "Linux in WSL (${WSL_DISTRO_NAME:-distribuzione sconosciuta})"; else ok "Linux"; fi ;;
Darwin) warn "macOS: non provato (Docker Desktop dovrebbe bastare)" ;;
*)      err "$OS: serve Linux o WSL2 (su Windows: aprire il progetto dentro WSL)" ;;
esac

echo "== cartella del progetto: $ROOT =="
if [ -r /proc/self/mountinfo ]; then
    # campi di mountinfo: 5 = punto di montaggio; dopo il separatore " - ": tipo di filesystem e sorgente
    M=$(awk -v p="$ROOT" '
        { mp=$5; gsub(/\\040/, " ", mp); for (i=7; i<=NF; i++) if ($i == "-") { fs=$(i+1); src=$(i+2); break }
          if ((p == mp || index(p, mp == "/" ? "/" : mp "/") == 1) && length(mp) >= best) { best=length(mp); r=mp " " fs " " src } }
        END { print r }' /proc/self/mountinfo)
    MP=${M%% *}; R=${M#* }; FS=${R%% *}; SRC=${R#* }
    case "$FS" in
    9p|drvfs|v9fs|virtiofs|fuse.grpcfuse|fuseblk|cifs|smb3|nfs|nfs4|vboxsf)
        if [ $WSL = 1 ]; then err "il progetto sta su un disco Windows ($FS, montato in $MP): spostarlo nel filesystem di WSL (es. ~/progetti), e' molto piu' veloce e evita problemi di permessi e fine riga"
        else warn "filesystem condiviso o di rete ($FS su $MP): build e test possono essere lenti"; fi ;;
    ext4|ext3|xfs|btrfs|zfs|overlay|tmpfs|f2fs) ok "filesystem $FS (montaggio $MP)" ;;
    "") warn "tipo di filesystem non trovato in /proc/self/mountinfo" ;;
    *) warn "filesystem $FS (montaggio $MP, $SRC): non classificato" ;;
    esac
else
    warn "/proc/self/mountinfo non c'e': tipo di filesystem non controllato"
fi
case "$ROOT" in /mnt/[a-z]/*) [ $WSL = 1 ] && err "percorso sotto /mnt/<disco>: e' un disco Windows visto da WSL" ;; esac
case "$ROOT" in *" "*) warn "il percorso contiene spazi: gli script li gestiscono, ma e' meglio evitarli" ;; esac
FREE=$(df -Pk "$ROOT" 2>/dev/null | awk 'NR==2 {print int($4/1024/1024)}')
[ -n "$FREE" ] && { [ "$FREE" -ge 10 ] && ok "spazio libero: $FREE GB" || warn "spazio libero: $FREE GB (immagini + VICE + out/ ~ 8 GB)"; }

echo "== programmi dell'host =="
for p in git curl; do command -v $p >/dev/null && ok "$p: $(command -v $p)" || err "$p non trovato"; done
if command -v docker >/dev/null; then
    ok "docker: $(docker --version 2>/dev/null)"
    if docker info >/dev/null 2>&1; then ok "demone Docker raggiungibile"
    else err "il demone Docker non risponde (avviarlo; su Linux aggiungere l'utente al gruppo docker; su Windows: Docker Desktop con integrazione WSL)"; fi
    docker buildx version >/dev/null 2>&1 && ok "BuildKit (docker buildx)" || warn "docker buildx non trovato: servono BuildKit e --build-context (Docker >= 23)"
else
    err "Docker non trovato (https://docs.docker.com/get-docker/)"
fi

echo "== git e fine riga =="
if git rev-parse --git-dir >/dev/null 2>&1; then
    A=$(git config core.autocrlf || true)
    [ "$A" = "true" ] && err "core.autocrlf=true: gli script diventerebbero CRLF (git config core.autocrlf false)" || ok "core.autocrlf=${A:-non impostato}"
    [ -f .gitattributes ] && ok ".gitattributes (eol=lf)" || err ".gitattributes mancante"
    CR=$(git ls-files --eol 2>/dev/null | awk '$2 ~ /crlf/ && ($4 ~ /\.(sh|py)$/ || $4 ~ /Dockerfile$/) {print $4}' | head -5)
    [ -z "$CR" ] && ok "nessuno script con fine riga CRLF" || err "script con CRLF nella copia di lavoro: $CR"
else
    warn "non e' un repository git"
fi

echo "== ROM ($REL/roms/roms.md) =="
if command -v sha256sum >/dev/null; then
    BAD=0; N=0
    for line in $(sed -n 's/^| `\([^`]*\)` | [0-9]* | `\([0-9a-f]\{64\}\)` .*/\1:\2/p' "$REL/roms/roms.md"); do
        f=${line%%:*}; s=${line#*:}; N=$((N + 1))
        if [ ! -f "$REL/roms/$f" ]; then err "manca $REL/roms/$f"; BAD=1
        elif [ "$(sha256sum "$REL/roms/$f" | cut -c1-64)" != "$s" ]; then err "SHA-256 diverso: $REL/roms/$f"; BAD=1; fi
    done
    [ $BAD = 0 ] && ok "$N ROM presenti, SHA-256 come in $REL/roms/roms.md"
else
    warn "sha256sum non trovato: ROM non controllate"
fi
V=$REL/vc64web-custom/roms
if diff -r "$REL/roms" "$V" >/dev/null 2>&1; then ok "$REL/roms/ e $V identiche"; else err "$REL/roms/ e $V sono diverse (devono essere uguali: diff -r $REL/roms $V)"; fi

echo "== immagini Docker e programmi compilati =="
if docker info >/dev/null 2>&1; then
    for i in c64-builder c64-emu-vice c64-emu-vc64web c64-emu-viewer ${C64_EXTRA_IMAGES:-}; do
        docker image inspect "$i" >/dev/null 2>&1 && ok "immagine $i" || warn "immagine $i assente (./build.sh la costruisce quando serve)"
    done
fi
for b in vice/bin/x64sc zx0/bin/zx0 cc1541/bin/cc1541; do
    [ -x "$REL/$b" ] && ok "$REL/$b" || warn "$REL/$b assente (./build.sh lo compila: $REL/build.sh)"
done

echo
if [ $ERR -gt 0 ]; then echo "RISULTATO: $ERR errori, $WARN avvisi"; exit 1; fi
echo "RISULTATO: ok ($WARN avvisi)"
