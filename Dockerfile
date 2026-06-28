# ═══════════════════════════════════════════════════
#  SKYY – Production Dockerfile
#  Multi-stage build for minimal image size
# ═══════════════════════════════════════════════════

# ─── Build Stage ───
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ─── Runtime Stage ───
FROM python:3.12-slim

# Security: run as non-root user
RUN groupadd -r skyy && useradd -r -g skyy -d /app -s /bin/false skyy

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY run.py .
COPY app/ app/
COPY .env.example .env

# Create logs directory
RUN mkdir -p logs && chown -R skyy:skyy /app

# Security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

USER skyy

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "logs/access.log", "--error-logfile", "logs/error.log", "run:app"]