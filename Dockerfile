FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    libbz2-dev \
    liblzma-dev \
    wget \
    gnupg \
    libgtk2.0-0 \
    libgconf-2-4 \
    libxss1 \
    libnss3 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

RUN ln -s $POETRY_VENV/bin/poetry /usr/local/bin/poetry

WORKDIR /TOHMIN

COPY pyproject.toml ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . .

WORKDIR /TOHMIN/src

CMD ["poetry", "run", "python", "app.py"]