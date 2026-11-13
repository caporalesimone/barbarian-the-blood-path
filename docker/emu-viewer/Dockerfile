# barbarian-emu-viewer (13/11): schermo condiviso per guardare dal vivo gli emulatori che girano negli altri container.
# Xvfb (:99) + x11vnc + noVNC: il browser dell'host apre http://localhost:6080 e vede lo schermo. Facoltativo: lo avvia
# ./build.sh --view (o docker/viewer.sh start). Gli altri container usano lo stesso schermo montando il volume barbarian-x11
# (socket X in /tmp/.X11-unix) con DISPLAY=:99. Niente audio (VNC non lo trasporta). Copyright (c) 2026 - Simone Caporale
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends xvfb x11vnc novnc websockify procps \
    && rm -rf /var/lib/apt/lists/* \
    && printf '<meta http-equiv="refresh" content="0;url=vnc.html?autoconnect=1&resize=scale&reconnect=1">\n' > /usr/share/novnc/index.html
COPY start.sh /start.sh
EXPOSE 6080
CMD ["sh", "/start.sh"]
