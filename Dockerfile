FROM python:3.13.6-alpine@sha256:f196fd275fdad7287ccb4b0a85c2e402bb8c794d205cf6158909041c1ee9f38d AS base

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
