FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency spec first for caching
COPY pyproject.toml .

# Copy source code
COPY packages/api packages/api
COPY alembic.ini .

# Force fresh install every deploy
RUN pip install --no-cache-dir . && python -c "import agentwallet; print('OK')"

EXPOSE 8000

CMD ["uvicorn", "agentwallet.main:app", "--host", "0.0.0.0", "--port", "8000"]
