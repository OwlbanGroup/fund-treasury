FROM python:3.11-slim

WORKDIR /srv/app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN useradd --create-home appuser \
    && mkdir -p /data/outbox \
    && chown -R appuser:appuser /srv/app /data

USER appuser

# Non-root user writes the SQLite DB and bank file outbox under /data (volume).
ENV DATABASE_URL=sqlite:////data/treasury.db \
    BANK_FILE_OUTBOX=/data/outbox

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
