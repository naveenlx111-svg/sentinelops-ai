FROM python:3.14-slim
WORKDIR /app
RUN useradd --uid 10001 shop
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH"
USER 10001