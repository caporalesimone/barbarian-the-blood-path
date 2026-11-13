# barbarian-emu-vice (13/11): barbarian-builder + cio' che serve per far girare VICE senza schermo (test, screenshot, arena,
# misure, render dei brani). VICE non e' un pacchetto: e' third-party-tools/vice/bin (compilato una volta, gtk3, nel progetto);
# qui ci sono solo le sue librerie, il display virtuale (Xvfb) e ffmpeg (WAV -> MP3 di tools/build/gen_music.py --render).
# Parte da barbarian-builder perche' i test assemblano varianti del gioco (64tass) e importano i generatori.
# Copyright (c) 2026 - Simone Caporale
FROM barbarian-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgtk-3-0t64 libglew2.2 libgl1 libpulse0 libasound2t64 libpng16-16t64 libevdev2 libcurl4t64 \
        xvfb xauth procps ffmpeg \
    && rm -rf /var/lib/apt/lists/*
CMD ["bash"]
