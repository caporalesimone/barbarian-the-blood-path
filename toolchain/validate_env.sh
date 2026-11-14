#!/bin/sh
# Checks the HOST environment before using the toolchain and the project (13/11, owner's request).
# Copyright (c) 2026 - Simone Caporale
#   toolchain/validate_env.sh   (or the project ./validate_env.sh)   one line per check: OK / WARNING / ERROR; exits 1 if there is at least one ERROR
# The host needs only: sh, Docker (with BuildKit), git, curl (VICE download). Everything else runs in the containers.
# It also checks WHERE the project is: in the WSL Linux filesystem (fast) or on a Windows disk (/mnt/c, slow and with
# permission and line-ending problems). Method: the filesystem type of the mount point that holds the project folder, read
# from /proc/self/mountinfo (the mount with the longest prefix), not the path name.
TC=$(cd "$(dirname "$0")" && pwd) || exit 1
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}
cd "$ROOT" || exit 1
[ -f toolchain.env ] && . ./toolchain.env
ERR=0; WARN=0
ok()   { printf '  OK       %s\n' "$*"; }
warn() { printf '  WARNING  %s\n' "$*"; WARN=$((WARN + 1)); }
err()  { printf '  ERROR    %s\n' "$*"; ERR=$((ERR + 1)); }

echo "== system =="
OS=$(uname -s)
WSL=0
if [ -r /proc/sys/kernel/osrelease ] && grep -qi microsoft /proc/sys/kernel/osrelease; then WSL=1; fi
[ -n "${WSL_DISTRO_NAME:-}" ] || [ -n "${WSL_INTEROP:-}" ] && WSL=1
case "$OS" in
Linux)  if [ $WSL = 1 ]; then ok "Linux in WSL (${WSL_DISTRO_NAME:-unknown distribution})"; else ok "Linux"; fi ;;
Darwin) warn "macOS: not tested (Docker Desktop should be enough)" ;;
*)      err "$OS: Linux or WSL2 needed (on Windows: open the project inside WSL)" ;;
esac

echo "== project folder: $ROOT =="
if [ -r /proc/self/mountinfo ]; then
    # mountinfo fields: 5 = mount point; after the " - " separator: filesystem type and source
    M=$(awk -v p="$ROOT" '
        { mp=$5; gsub(/\\040/, " ", mp); for (i=7; i<=NF; i++) if ($i == "-") { fs=$(i+1); src=$(i+2); break }
          if ((p == mp || index(p, mp == "/" ? "/" : mp "/") == 1) && length(mp) >= best) { best=length(mp); r=mp " " fs " " src } }
        END { print r }' /proc/self/mountinfo)
    MP=${M%% *}; R=${M#* }; FS=${R%% *}; SRC=${R#* }
    case "$FS" in
    9p|drvfs|v9fs|virtiofs|fuse.grpcfuse|fuseblk|cifs|smb3|nfs|nfs4|vboxsf)
        if [ $WSL = 1 ]; then err "the project is on a Windows disk ($FS, mounted on $MP): move it into the WSL filesystem (e.g. ~/projects), it is much faster and avoids permission and line-ending problems"
        else warn "shared or network filesystem ($FS on $MP): build and tests can be slow"; fi ;;
    ext4|ext3|xfs|btrfs|zfs|overlay|tmpfs|f2fs) ok "filesystem $FS (mount $MP)" ;;
    "") warn "filesystem type not found in /proc/self/mountinfo" ;;
    *) warn "filesystem $FS (mount $MP, $SRC): not classified" ;;
    esac
else
    warn "no /proc/self/mountinfo: filesystem type not checked"
fi
case "$ROOT" in /mnt/[a-z]/*) [ $WSL = 1 ] && err "path under /mnt/<drive>: a Windows disk seen from WSL" ;; esac
case "$ROOT" in *" "*) warn "the path contains spaces: the scripts handle them, but better avoid them" ;; esac
FREE=$(df -Pk "$ROOT" 2>/dev/null | awk 'NR==2 {print int($4/1024/1024)}')
[ -n "$FREE" ] && { [ "$FREE" -ge 10 ] && ok "free space: $FREE GB" || warn "free space: $FREE GB (images + VICE + out/ ~ 8 GB)"; }

echo "== host programs =="
for p in git curl; do command -v $p >/dev/null && ok "$p: $(command -v $p)" || err "$p not found"; done
if command -v docker >/dev/null; then
    ok "docker: $(docker --version 2>/dev/null)"
    if docker info >/dev/null 2>&1; then ok "Docker daemon reachable"
    else err "the Docker daemon does not answer (start it; on Linux add the user to the docker group; on Windows: Docker Desktop with WSL integration)"; fi
    docker buildx version >/dev/null 2>&1 && ok "BuildKit (docker buildx)" || warn "docker buildx not found: BuildKit and --build-context are needed (Docker >= 23)"
else
    err "Docker not found (https://docs.docker.com/get-docker/)"
fi

echo "== git and line endings =="
if git rev-parse --git-dir >/dev/null 2>&1; then
    A=$(git config core.autocrlf || true)
    [ "$A" = "true" ] && err "core.autocrlf=true: the scripts would become CRLF (git config core.autocrlf false)" || ok "core.autocrlf=${A:-not set}"
    [ -f .gitattributes ] && ok ".gitattributes (eol=lf)" || err ".gitattributes missing"
    CR=$(git ls-files --eol 2>/dev/null | awk '$2 ~ /crlf/ && ($4 ~ /\.(sh|py)$/ || $4 ~ /Dockerfile$/) {print $4}' | head -5)
    [ -z "$CR" ] && ok "no script with CRLF line endings" || err "scripts with CRLF in the working copy: $CR"
else
    warn "not a git repository"
fi

echo "== ROM ($REL/roms/roms.md) =="
if command -v sha256sum >/dev/null; then
    BAD=0; N=0
    for line in $(sed -n 's/^| `\([^`]*\)` | [0-9]* | `\([0-9a-f]\{64\}\)` .*/\1:\2/p' "$REL/roms/roms.md"); do
        f=${line%%:*}; s=${line#*:}; N=$((N + 1))
        if [ ! -f "$REL/roms/$f" ]; then err "missing $REL/roms/$f"; BAD=1
        elif [ "$(sha256sum "$REL/roms/$f" | cut -c1-64)" != "$s" ]; then err "different SHA-256: $REL/roms/$f"; BAD=1; fi
    done
    [ $BAD = 0 ] && ok "$N ROMs present, SHA-256 as in $REL/roms/roms.md"
else
    warn "sha256sum not found: ROMs not checked"
fi
V=$REL/vc64web-custom/roms
if diff -r "$REL/roms" "$V" >/dev/null 2>&1; then ok "$REL/roms/ and $V identical"; else err "$REL/roms/ and $V differ (they must be equal: diff -r $REL/roms $V)"; fi

echo "== Docker images and external program sources =="
if docker info >/dev/null 2>&1; then
    for i in c64-builder c64-emu-vice c64-emu-vc64web c64-emu-viewer ${C64_EXTRA_IMAGES:-}; do
        docker image inspect "$i" >/dev/null 2>&1 && ok "image $i" || warn "image $i missing (./build.sh builds it when needed)"
    done
fi
# (13/11) VICE, zx0 and cc1541 are compiled INSIDE the images: only the VICE tarball is needed here (toolchain/images.sh downloads
# it, and deletes it once c64-emu-vice exists, 14/11)
if docker image inspect c64-emu-vice >/dev/null 2>&1; then ok "VICE is inside c64-emu-vice (tarball not needed)"
elif ls "$REL"/vice/download/vice-*.tar.gz >/dev/null 2>&1; then ok "VICE tarball in $REL/vice/download/"
else warn "VICE tarball missing ($REL/images.sh downloads it when it builds the images)"; fi
K=${C64_KRILL_ZIP:-}
[ -n "$K" ] && { [ -f "$K" ] && ok "Krill zip for cc1541: $K" || err "Krill zip for cc1541 not found: $K (C64_KRILL_ZIP)"; }

echo
if [ $ERR -gt 0 ]; then echo "RESULT: $ERR errors, $WARN warnings"; exit 1; fi
echo "RESULT: ok ($WARN warnings)"
