# PROTOTIPO (passo C): tunnel WebSocket guacamole-lite (Node) + pagina con guacamole-common-js
FROM node:22-bookworm-slim
WORKDIR /app
RUN --mount=type=secret,id=ca if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; \
    npm init -y >/dev/null && npm install --no-audit --no-fund guacamole-lite@1.2.0 guacamole-common-js@1.5.0 && rm -rf /root/.npm
COPY server.js index.html /app/
EXPOSE 8080 8081
CMD ["node", "server.js"]
