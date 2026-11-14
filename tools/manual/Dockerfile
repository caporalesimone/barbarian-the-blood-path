# barbarian-manual (13/11): PDF del manuale (tools/manual/gen_manual.py) con WeasyPrint (HTML + CSS -> PDF, senza browser).
# Immagine del PROGETTO (non di Lab64; diventera' lab64-pdf-gen, TODO T2): parte da lab64-tools, che ha gia' Python 3, PyYAML e Pillow, e aggiunge solo
# WeasyPrint con pango e i font DejaVu. pip serve solo durante la build (poi si toglie).
# CA facoltativa di un proxy che intercetta TLS (solo per pip): --secret id=ca,src=FILE (./build.sh: C64_CA_BUNDLE).
# Costruita da ./build.sh: docker build -t barbarian-manual tools/manual. Copyright (c) 2026 - Simone Caporale
FROM lab64-tools
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu-core python3-pip \
    && pip install --no-cache-dir --break-system-packages weasyprint==70.0 \
    && apt-get purge -y --auto-remove python3-pip && rm -rf /var/lib/apt/lists/*
