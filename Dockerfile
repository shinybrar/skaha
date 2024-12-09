FROM python:3.13-alpine@sha256:804ad02b9ba67ea1f8307eeb6407b121c6bd6bb19d3f182aae166821eb59d6a4 AS base

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
