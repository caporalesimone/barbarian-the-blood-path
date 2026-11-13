# VirtualC64 headless + API di controllo. Contiene la pagina headless GIA' buildata (c64-headless.html, generata da build.py)
# e solo i file necessari all'esecuzione (elenco in .dockerignore: allowlist). Niente portable/, build.py, changelog, ecc.
# Non lanciare a mano: `python3 build.py` genera le pagine e poi costruisce l'immagine, passando la cartella delle pagine come
# contesto con nome "pages" (--build-context pages=DIR: cosi' l'uscita --out puo' stare anche fuori da questa cartella).
# CA facoltativa per un proxy che intercetta TLS (solo durante npm/playwright): --secret id=ca,src=FILE (build.py: C64_CA_BUNDLE).
# Copyright © 2026 Simone Caporale
FROM node:22-bookworm-slim
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NODE_PATH=/usr/local/lib/node_modules \
    C64_HOST=0.0.0.0 C64_NO_SANDBOX=1 \
    C64_ROMS=/roms C64_GAMES=/games
# dipendenze esterne: ffmpeg (video) e Playwright + Chromium (usati solo internamente dal demone)
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg \
 && npm i -g playwright@1.63.0 \
 && npx playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/* /root/.npm
WORKDIR /app
COPY --from=pages c64-headless.html /app/out/c64-headless.html
COPY headless/ /app/headless/
COPY docs/ /app/docs/
COPY roms/ /app/roms/
RUN mkdir -p /games /roms /scripts /output
# /games = file di gioco (.d64 .g64 .prg .t64 .crt ...) ; /roms = ROM aggiuntive ; /scripts = script di input ; /output = file prodotti (screenshot, video, registrazioni)
VOLUME ["/games", "/roms", "/scripts", "/output"]
EXPOSE 7064
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD node -e "require('http').get('http://127.0.0.1:7064/ping',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"
CMD ["node", "headless/c64d.js", "--port", "7064"]
