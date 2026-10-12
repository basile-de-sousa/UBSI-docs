# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS document-assets
WORKDIR /build
COPY scripts/document-assets.py scripts/document-assets.py
COPY documents/assets.lock.json documents/assets.lock.json
RUN python scripts/document-assets.py
COPY scripts/search-assets.py scripts/search-assets.py
COPY search/assets.lock.json search/assets.lock.json
RUN python scripts/search-assets.py

FROM node:24.19.0-bookworm-slim@sha256:a9f5f7c91a432850b2a8a7797adf5eadb6c733ceed61167806cee7ea7fbc29df AS frontend
WORKDIR /build
COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts
COPY tsconfig.json vite.config.mjs ./
COPY frontend ./frontend
COPY public ./public
COPY --from=document-assets /build/public/vendor ./public/vendor
COPY --from=document-assets /build/.vendor ./.vendor
COPY scripts/document-shapes.mjs ./scripts/document-shapes.mjs
RUN node scripts/document-shapes.mjs
COPY scripts/vendor-notices.mjs ./scripts/vendor-notices.mjs
RUN npm run typecheck && npm run build

FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS dependencies
WORKDIR /build
COPY requirements.lock ./
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock

FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false
WORKDIR /app/portal
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless libcairo2 && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 10001 portal && useradd --uid 10001 --gid portal --no-create-home portal && mkdir -p /var/lib/ubsi/private && chown portal:portal /var/lib/ubsi/private && chmod 700 /var/lib/ubsi/private
COPY --from=dependencies /opt/venv /opt/venv
COPY manage.py ./
COPY config ./config
COPY accounts ./accounts
COPY acceptance ./acceptance
COPY core ./core
COPY documents ./documents
COPY knowledge ./knowledge
COPY search ./search
COPY jobs ./jobs
COPY sprints ./sprints
COPY templates ./templates
COPY --from=frontend /build/.vendor ./.vendor
COPY --from=document-assets /build/.models ./.models
COPY --from=frontend /build/static-built ./static-built
RUN java -Djava.awt.headless=true -jar .vendor/plantuml.jar -license > static-built/vendor/PLANTUML-LICENSE.txt
# These values exist only during static collection, never as runtime defaults.
RUN mkdir /build-private && PORTAL_ENV=development DEBUG=false SECRET_KEY=build-only-unused-secret-key-for-static-collection-00000000 ALLOWED_HOSTS=localhost,127.0.0.1 DATABASE_URL=postgresql://build:build@localhost/build PRIVATE_STORAGE_ROOT=/build-private python manage.py collectstatic --noinput && rm -r /build-private
USER portal
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=4 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready/', timeout=4).close()"]
# No raw URL access log: future authentication URLs may contain bearer tokens.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "30", "--forwarded-allow-ips", "", "--no-control-socket", "--error-logfile", "-", "--log-level", "warning"]
