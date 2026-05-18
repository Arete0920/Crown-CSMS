# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY release_closeout /app/backend/release_closeout

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app/backend
ENV DJANGO_SETTINGS_MODULE=crown_api.settings

EXPOSE 8000

CMD ["/app/entrypoint.sh"]


# Crown production hardening: run as non-root.
RUN addgroup --system crownapp || true \
    && adduser --system --ingroup crownapp crownapp || true
USER crownapp

