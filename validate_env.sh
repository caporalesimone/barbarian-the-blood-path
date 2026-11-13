#!/bin/sh
# Verifica dell'ambiente dell'host (13/11): i controlli stanno nella toolchain. Copyright (c) 2026 - Simone Caporale
exec "$(dirname "$0")/toolchain/validate_env.sh" "$@"
