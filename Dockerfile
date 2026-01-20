# =============================================================================
# WhatsApp Gateway - Dockerfile
# Build multi-stage para produccion (Python + FastAPI + Uvicorn)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Instalar dependencias
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /app

# Copiar requirements primero (mejor cache)
COPY requirements.txt .

# Instalar dependencias del sistema y Python
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Imagen final limpia
# -----------------------------------------------------------------------------
FROM python:3.13-slim

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas del builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar codigo de la aplicacion
COPY . .

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Puerto expuesto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl --fail http://localhost:8000/health || exit 1

# Variables de entorno por defecto (no sensibles)
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Comando de inicio (forma exec para manejo correcto de signals)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
