#!/bin/sh
# Verifica dell'ambiente dell'host (13/11): i controlli stanno in Lab64 (14/11: repository a parte, cartella accanto ../lab64 o LAB64).
# Copyright (c) 2026 - Simone Caporale
cd "$(dirname "$0")" || exit 1
L=${LAB64:-../lab64}
[ -x "$L/validate_env.sh" ] || { echo "  ERROR    Lab64 non trovato in $L: clonarlo accanto al progetto (../lab64) o impostare LAB64"; exit 1; }
exec "$L/validate_env.sh" "$@"
