ARG VARIANT=3.12-bookworm
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        mosquitto-clients \
        postgresql-client \
        shellcheck \
    && rm -rf /var/lib/apt/lists/*
