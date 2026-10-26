FROM python:3.12-slim

WORKDIR /app

# Pinned to the same uv as CI and Dockerfile.prod. An unpinned uv drifts past
# the `uv_build<0.12.0` bound in pyproject.toml and breaks the build.
RUN pip install --no-cache-dir uv==0.11.21

# Lockfile install so the image matches uv.lock (prometheus_client, etc.).
# --no-emit-project keeps the local `backend` package out of this layer; only
# pyproject/uv.lock are present here, so building it would fail on missing src/.
COPY pyproject.toml uv.lock .python-version ./
RUN uv export --frozen --no-dev --no-hashes --no-emit-project -o /tmp/requirements.txt \
    && uv pip install --system --no-cache -r /tmp/requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
