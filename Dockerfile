FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.11-slim as production

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /install /usr/local

COPY app/ ./app/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]