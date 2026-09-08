FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY data/README.md ./data/README.md
COPY data/eval ./data/eval
COPY data/synthetic_cases ./data/synthetic_cases

RUN python -m pip install '.[dev]'

RUN groupadd --gid 10001 medaudit \
    && useradd --uid 10001 --gid medaudit --no-create-home medaudit \
    && chown -R medaudit:medaudit /app

USER medaudit

CMD ["pytest", "-p", "no:cacheprovider"]
