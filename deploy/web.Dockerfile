FROM node:24.21.0 AS build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit --no-fund

COPY frontend/ .
RUN npm run build

FROM nginx:1.30.5

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/nginx.conf deploy/nginx-tls.conf /etc/nginx/available/
COPY deploy/app.conf deploy/security-headers.conf deploy/limits.conf /etc/nginx/snippets/
COPY deploy/entrypoint.sh /entrypoint.sh
COPY --from=build /frontend/dist /usr/share/nginx/html

ENTRYPOINT ["/entrypoint.sh"]
