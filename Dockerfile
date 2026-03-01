FROM python:3.11-slim as builder
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \\
    pip install --prefix=/install  --no-cache-dir -r requirements.txt


#Stage 2

FROM python:3.11-slim As production

WORKDIR /app

# Create a non-root user

RUN groupadd -r appuser && useradd -r -g  appuser appuser

# Copy installed packages from builder stage

COPY --from=builder /install /usr/local

COPY app/ ./app

# Set ownership to non-root user

RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check — Docker will call this every 30s
# If it fails 3 times, Docker marks container as unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Start the app
# --host 0.0.0.0 makes it accessible outside the container
# --workers 2 runs 2 parallel processes

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

