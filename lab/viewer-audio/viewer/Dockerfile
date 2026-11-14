# PROTOTIPO (passo C, 13/11): viewer + PulseAudio (scheda virtuale) + strumenti per l'evento di prova
FROM lab64-viewer
RUN apt-get update && apt-get install -y --no-install-recommends pulseaudio pulseaudio-utils x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*
# tone.wav: python3 ../make_files.py, poi copiarlo qui
COPY start-audio.sh tone.wav event.sh /opt/proto/
CMD ["sh", "/opt/proto/start-audio.sh"]
