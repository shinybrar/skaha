FROM python:3.13-alpine@sha256:323a717dc4a010fee21e3f1aac738ee10bb485de4e7593ce242b36ee48d6b352 AS base

FROM base AS builder
COPY . /skaha
WORKDIR /skaha

# Install UV
RUN set -ex \
    && apk add --no-cache curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && source $HOME/.local/bin/env \
    && uv build

FROM base AS production
COPY --from=builder /skaha/dist /skaha/dist
RUN pip install --no-cache-dir /skaha/dist/*.whl
