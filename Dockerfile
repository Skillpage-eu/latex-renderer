FROM texlive/texlive:latest

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.6.12/uv-installer.sh | sh

WORKDIR /app

COPY . .

RUN /root/.local/bin/uv sync

CMD [".venv/bin/uvicorn",  "main:app", "--host", "0.0.0.0", "--port", "8000"]


