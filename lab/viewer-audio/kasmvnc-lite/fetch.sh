#!/bin/sh
# Scarica sull'host i sorgenti del prototipo (non in git): pacchetto ufficiale di KasmVNC e kclient (GPL-3.0, linuxserver).
set -eu
cd "$(dirname "$0")"
V=1.5.2; D=kasmvncserver_ubuntu_noble_${V}_amd64.deb
[ -s "$D" ] || curl -fsSL -o "$D" "https://github.com/kasmtech/KasmVNC/releases/download/v$V/$D"
echo "$D sha256 $(sha256sum "$D" | cut -c1-64)   (13/11: 89a5d1fbe9e032b122202be158a2b25f15c97e0a5b8dcf92a5e6835c7b7b2acd)"
[ -d kclient ] || { git clone -q --depth 1 https://github.com/linuxserver/kclient kclient && rm -rf kclient/.git; }
echo "kclient: $(sed -n 's/.*"version": "\(.*\)".*/\1/p' kclient/package.json)"
