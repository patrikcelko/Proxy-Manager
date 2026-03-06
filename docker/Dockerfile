#  Stage 1: Build the TypeScript frontend bundle
FROM node:22-alpine AS frontend

WORKDIR /build
COPY package.json package-lock.json tsconfig.json ./
COPY proxy_manager/static/ts/ proxy_manager/static/ts/
RUN npm ci --ignore-scripts && npm run build

#  Stage 2: Python application
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY . .

# Overwrite bundle with freshly built version from Stage 1
COPY --from=frontend /build/proxy_manager/static/js/admin.bundle.js proxy_manager/static/js/admin.bundle.js
COPY --from=frontend /build/proxy_manager/static/js/admin.bundle.js.map proxy_manager/static/js/admin.bundle.js.map

RUN pip install --no-cache-dir .

EXPOSE 8222

CMD ["uvicorn", "proxy_manager:app", "--host", "0.0.0.0", "--port", "8222"]
