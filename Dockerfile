FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ ./
