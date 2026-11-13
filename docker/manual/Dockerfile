# barbarian-manual (13/11): solo il PDF del manuale (tools/manual/gen_manual.py) con WeasyPrint (HTML + CSS -> PDF, senza browser).
# ~320 MB contro ~950 MB di una base con Chromium. Python, PyYAML e Pillow per lo script; pango e font DejaVu per WeasyPrint.
# CA facoltativa di un proxy che intercetta TLS (solo per pip): --secret id=ca,src=FILE (./build.sh: BARBARIAN_CA_BUNDLE).
# Copyright (c) 2026 - Simone Caporale
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN --mount=type=secret,id=ca \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install --no-cache-dir weasyprint==70.0 pyyaml pillow
WORKDIR /work
CMD ["bash"]
