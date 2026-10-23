# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1
WORKDIR /app
COPY requirements-learning.txt requirements-creator.txt ./
COPY deploy/containers/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements-creator.txt -c requirements.lock
COPY musia ./musia
COPY apps/web ./apps/web
COPY website/musia.js ./website/musia.js
COPY website/data ./website/data
COPY website/assets ./website/assets
COPY deploy/containers/serve.py ./serve.py
RUN chmod -R a+rX /app && mkdir -m 0700 /state && chown 10001:10001 /state
USER 10001:10001
EXPOSE 8796
CMD ["python", "serve.py"]

# Explicit optional build: --build-context authsdk=/private/wheel-directory
# No private SDK or credentials enter the public/default image.
FROM app AS authenticated
USER root
RUN --mount=from=authsdk,target=/sdk,ro pip install --no-cache-dir /sdk/*.whl
USER 10001:10001

FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS agent
ENV NODE_ENV=production PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
WORKDIR /app
COPY deploy/containers/agent/package*.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund
COPY deploy/containers/agent/*.mjs deploy/containers/agent/*.json ./
RUN chmod -R a+rX /app
USER 10001:10001
EXPOSE 8081
CMD ["node", "server.mjs"]

FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587 AS egress
RUN apt-get update && apt-get install -y --no-install-recommends tinyproxy-bin ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --chmod=0444 deploy/containers/tinyproxy.conf /etc/tinyproxy/tinyproxy.conf
COPY --chmod=0444 deploy/containers/egress-allowlist /etc/tinyproxy/allowlist
RUN chmod 0755 /etc/tinyproxy
USER 10001:10001
EXPOSE 8888
CMD ["tinyproxy", "-d", "-c", "/etc/tinyproxy/tinyproxy.conf"]

FROM caddy:2-alpine@sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f AS web
# The upstream binary carries cap_net_bind_service. Copy to a new inode to
# remove that file capability: our high port needs no capabilities at all.
RUN cp /usr/bin/caddy /tmp/caddy && mv /tmp/caddy /usr/bin/caddy
COPY --chmod=0444 deploy/containers/Caddyfile /etc/caddy/Caddyfile
USER 10001:10001
