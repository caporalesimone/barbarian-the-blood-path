# PROTOTIPO "KasmVNC leggera" (13/11): Xvnc di KasmVNC (pacchetto ufficiale) + PulseAudio + kclient (solo audio).
ARG UBUNTU=24.04
# kclient usa pulseaudio2, modulo nativo: si compila con lo stesso node (Ubuntu) che lo esegue
FROM ubuntu:${UBUNTU} AS kclient
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm build-essential python3 libpulse-dev ca-certificates
COPY kclient/ /kclient/
RUN --mount=type=secret,id=ca if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; npm config set cafile /run/secrets/ca; fi; \
    cd /kclient && npm install --omit=dev --no-audit --no-fund && rm -f package-lock.json \
 && sed -i 's#show_control_bar=true#show_control_bar=true\&port=6901#' public/index.html

FROM ubuntu:${UBUNTU}
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# il pacchetto lo scarica ./fetch.sh
COPY kasmvncserver_ubuntu_noble_1.5.2_amd64.deb /tmp/
# solo le librerie di Xvnc (dipendenze del pacchetto SENZA perl: servono solo allo script vncserver, che non usiamo), poi i file
RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6 libgbm1 libgl1 libpixman-1-0 libpng16-16t64 libssl3t64 libunwind8 libx11-6 libxau6 libxcursor1 libxdmcp6 \
        libxext6 libxfixes3 libxfont2 libxrandr2 libxshmfence1 libxtst6 xauth x11-xkb-utils xkb-data \
        pulseaudio nodejs \
    && dpkg-deb -x /tmp/kasmvncserver_ubuntu_noble_1.5.2_amd64.deb / && ln -sf /usr/bin/Xkasmvnc /usr/bin/Xvnc \
    && rm -rf /var/lib/apt/lists/* /tmp/*.deb /usr/share/doc /usr/share/man
COPY --from=kclient /kclient /kclient
COPY start.sh /opt/kasm/start.sh
EXPOSE 6900 6901
CMD ["sh", "/opt/kasm/start.sh"]
