FROM python:3.12-slim


COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --package fastapi-demo

COPY ./app .
COPY alembic.ini .
COPY alembic ./alembic
ENV PYTHONPATH=/

EXPOSE 8000

CMD ["sh", "-c", "fastapi run --workers ${WORKERS:-4} main.py"]
