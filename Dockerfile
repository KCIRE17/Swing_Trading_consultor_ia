# syntax=docker/dockerfile:1
#
# Swing Trading Consultor IA
#
# Imagen en dos etapas: la primera compila las dependencias en un venv y la
# segunda solo copia ese venv, de modo que la imagen final no lleva pip,
# setuptools ni cabeceras de compilacion.
#
# Importante: VERCEL no debe definirse aqui. main.py solo monta public/ como
# sitio estatico cuando VERCEL NO esta presente, que es justo el caso de Docker.

# ---------------------------------------------------------------- base
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------------------------------------------------------------- deps
FROM base AS builder

# build-essential queda solo en esta etapa: si algun paquete no trae rueda,
# se compila aqui y el resultado viaja en el venv.
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.lock.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.lock.txt

# ---------------------------------------------------------------- runtime
FROM base AS runtime

# ca-certificates para las llamadas a yfinance, Gemini y Supabase.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# Poda: pip ya cumplio su funcion y las batteries de test de los paquetes no se
# usan en runtime. Ahorra del orden de 95 MB.
RUN rm -rf /opt/venv/lib/python3.12/site-packages/pip \
    && rm -rf /opt/venv/lib/python3.12/site-packages/setuptools \
    && find /opt/venv/lib/python3.12/site-packages -maxdepth 2 -type d \
        \( -name tests -o -name test -o -name '*.tests' \) -exec rm -rf {} + \
    && find /opt/venv -type d -name __pycache__ -exec rm -rf {} +

ENV PATH="/opt/venv/bin:$PATH"

# Usuario sin privilegios. El uid 1000 coincide con el usuario habitual de
# Linux, que es quien monta volumenes en docker compose sin sudo.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Codigo: main.py, app/ y el modelo de sentimiento.
COPY --chown=app:app main.py pyproject.toml ./
COPY --chown=app:app app/ ./app/
COPY --chown=app:app models/ ./models/

# Sitio estatico. Es lo que main.py monta en "/" cuando VERCEL no esta definido.
COPY --chown=app:app public/ ./public/

USER app

ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

# Sin curl en la imagen: el propio Python sirve para el healthcheck.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4).status==200 else 1)"

CMD ["sh", "-c", "uvicorn main:app --host ${HOST} --port ${PORT}"]
